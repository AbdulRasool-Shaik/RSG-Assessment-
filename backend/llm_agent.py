"""
Agentic LLM / Vectorless RAG Engine
Implements schema-grounded Text-to-SQL generation with an autonomous
reflection loop (self-correction on error), AST validation, and fallback
to the deterministic semantic engine when API keys are not supplied.
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, Any, Tuple
from .security import validate_sql_query, execute_safe_query, SecurityValidationError
from .models import QueryResponse, MetricCard, ChartData
from .deterministic_engine import DeterministicEngine

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Business Intelligence Agent specializing in SQLite sales analytics.
Your task is to convert a user's natural language question into a single, highly optimized, read-only SQLite query.

### Database Schema (Table: 'sales')
- transaction_id: TEXT PRIMARY KEY (e.g., 'TXN0001')
- order_date: TEXT (ISO-8601 'YYYY-MM-DD', e.g., '2026-01-03')
- order_month: TEXT ('YYYY-MM', e.g., '2026-01')
- product: TEXT (e.g., 'Laptop Stand', 'Wireless Mouse', 'Office Chair', 'Monitor', 'Keyboard', 'Desk', 'USB-C Hub')
- category: TEXT ('Accessories', 'Furniture', 'Electronics')
- region: TEXT ('North', 'South', 'West', 'East')
- sales_channel: TEXT ('Online', 'Retail')
- quantity: INTEGER (items sold)
- unit_price: REAL (price per unit)
- discount_amount: REAL (discount deducted)
- gross_revenue: REAL (quantity * unit_price)
- net_revenue: REAL ((quantity * unit_price) - discount_amount)
- status: TEXT ('Completed', 'Returned')

### Critical Business Rules:
1. Always filter by `status = 'Completed'` unless the user explicitly asks about returns or all records.
2. For revenue queries, calculate or select `net_revenue` (or `(quantity * unit_price) - discount_amount`).
3. For monthly grouping, use `order_month` or `strftime('%Y-%m', order_date)`.
4. Only return ONE single SELECT statement. Do not use semicolons. Do NOT include Markdown code fences or extra text. Return ONLY the raw SQL statement.
5. Never execute DROP, DELETE, UPDATE, INSERT, ALTER, or PRAGMA statements.
"""

class AgenticQueryCoordinator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.deterministic_engine = DeterministicEngine(db_path)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def execute(self, query: str, prefer_llm: bool = True) -> QueryResponse:
        """
        Coordinates query execution. Attempts Agentic LLM mode if configured,
        otherwise uses the deterministic semantic engine.
        """
        has_llm_key = bool(self.gemini_api_key or self.openai_api_key)
        
        # If user does not have LLM key or prefers deterministic mode
        if not prefer_llm or not has_llm_key:
            return self.deterministic_engine.process_query(query)

        try:
            return self._run_llm_agent_loop(query)
        except Exception as e:
            logger.warning(f"LLM Agent loop failed: {e}. Falling back to deterministic engine.")
            fallback_res = self.deterministic_engine.process_query(query)
            fallback_res.explanation = f"Notice: Processed via Deterministic Semantic Engine (LLM fallback: {str(e)[:100]})"
            return fallback_res

    def _run_llm_agent_loop(self, user_query: str, max_retries: int = 2) -> QueryResponse:
        """
        Agentic Reflection Loop:
        1. Generate SQL from natural language query.
        2. Validate AST and security policies.
        3. If error occurs, feed error message back to model for self-correction.
        4. Execute validated SQL in read-only sandbox.
        5. Synthesize structured answer.
        """
        prompt = f"User Question: {user_query}\nGenerate the optimal SQLite query:"
        feedback = ""

        for attempt in range(max_retries + 1):
            if feedback:
                current_prompt = f"{prompt}\n\nPrevious attempt failed with error:\n{feedback}\nPlease self-correct and output a valid SQLite query:"
            else:
                current_prompt = prompt

            raw_sql = self._call_llm(current_prompt)
            clean_sql = self._clean_sql(raw_sql)

            # Security and AST validation
            try:
                validate_sql_query(clean_sql)
                cols, rows, exec_time = execute_safe_query(self.db_path, clean_sql)
                
                # Format response
                return self._synthesize_response(user_query, clean_sql, cols, rows, exec_time)
            except (SecurityValidationError, Exception) as err:
                feedback = str(err)
                if attempt == max_retries:
                    raise RuntimeError(f"Agent self-correction exceeded max attempts. Last error: {feedback}")

        raise RuntimeError("Failed to generate valid SQL query.")

    def _call_llm(self, prompt: str) -> str:
        if self.gemini_api_key:
            return self._call_gemini(prompt)
        elif self.openai_api_key:
            return self._call_openai(prompt)
        raise ValueError("No valid LLM API key configured.")

    def _call_gemini(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": SYSTEM_PROMPT},
                    {"text": prompt}
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 300
            }
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _clean_sql(self, sql_str: str) -> str:
        # Remove markdown code fences if LLM wrapped it
        clean = sql_str.replace("```sql", "").replace("```", "").strip()
        # Remove trailing semicolon
        clean = clean.rstrip(";")
        return clean

    def _synthesize_response(
        self, query: str, sql: str, cols: list, rows: list, exec_time: float
    ) -> QueryResponse:
        # Build natural summary and metric cards
        metrics = []
        if rows and len(rows) == 1:
            row = rows[0]
            for k, v in list(row.items())[:3]:
                metrics.append(MetricCard(label=k.replace('_', ' ').title(), value=f"${v:,.2f}" if isinstance(v, (int, float)) and 'revenue' in k else str(v)))

        answer = f"### Query Result\n\nFound **{len(rows)}** record(s) matching your question.\n\n"
        if rows:
            answer += f"**Primary Finding:** {json.dumps(rows[0], default=str)}\n"

        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows[:20],
            metrics=metrics,
            engine_used="agentic_llm_engine",
            explanation="Generated via Vectorless RAG Agent with AST validation."
        )
