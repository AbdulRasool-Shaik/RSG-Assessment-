"""
Live Google Gemini Agentic BI Engine
Implements real-time Vectorless RAG, dynamic schema-grounded Text-to-SQL generation,
autonomous self-correction reflection loops, and executive BI synthesis powered by
Google AI Studio Gemini models.
"""

import os
import re
import json
import logging
import requests
from typing import Optional, Dict, Any, List, Tuple
from .security import validate_sql_query, execute_safe_query, SecurityValidationError
from .models import QueryResponse, MetricCard, ChartData
from .deterministic_engine import DeterministicEngine

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite Business Intelligence AI Agent specializing in real-time SQLite sales analytics.
Your job is to translate the user's natural language question into an exact, optimized, read-only SQLite SQL query.

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
- discount_amount: REAL (promotional discount)
- gross_revenue: REAL (quantity * unit_price)
- net_revenue: REAL ((quantity * unit_price) - discount_amount)
- status: TEXT ('Completed', 'Returned')

### Critical Analytical & Business Rules:
1. Realized Revenue: Always filter by `status = 'Completed'` unless the user explicitly asks about returns or cancelled transactions.
2. Revenue Definition: For sales or revenue questions, select or sum `net_revenue` (or `(quantity * unit_price) - discount_amount`).
3. Date Aggregations: For monthly groupings, use `order_month` or `strftime('%Y-%m', order_date)`.
4. Strict Read-Only: Output exactly ONE single SELECT statement. Do NOT include Markdown formatting, code fences, or semicolons. Return ONLY raw SQL.
5. Zero Mutation: NEVER use DROP, DELETE, UPDATE, INSERT, ALTER, or PRAGMA.
6. Scope Check: If the question is completely unrelated to sales, business data, or transactions (e.g., general trivia, weather, jokes), respond with the exact word: REFUSE
"""

SYNTHESIS_PROMPT = """You are an Executive Business Intelligence Analyst.
Analyze the user's question, the executed SQL query, and the actual database output records.
Provide a structured JSON response with:
1. "answer": A comprehensive, executive-level Markdown summary explaining the findings with exact dollar figures, unit counts, key drivers, and actionable business takeaways.
2. "metrics": An array of 2 to 4 metric cards, each with {"label": "...", "value": "...", "subtitle": "..."}.
3. "chart": An optional chart object {"chart_type": "bar" | "line" | "doughnut", "title": "...", "labels": [...], "datasets": [{"label": "...", "data": [...]}]} if the data is suitable for visualization, or null.
4. "takeaway": A concise one-sentence strategic insight.

Return ONLY a valid JSON object matching this schema without any surrounding text or markdown code fences.
"""

class AgenticQueryCoordinator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.deterministic_engine = DeterministicEngine(db_path)

    def execute(
        self,
        query: str,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        prefer_llm: bool = True
    ) -> QueryResponse:
        """
        Coordinates query processing:
        - If Gemini API Key is provided (via UI or environment variable), uses the Live Agentic Gemini Engine.
        - If no API key is provided, falls back seamlessly to the Deterministic Semantic Engine.
        """
        # Resolve API Key (UI key takes precedence over .env)
        active_key = (api_key or "").strip() or os.getenv("GEMINI_API_KEY", "").strip()

        if not prefer_llm or not active_key:
            response = self.deterministic_engine.process_query(query)
            response.live_model = "None (Offline Rule Engine - Enter Gemini API Key in UI to activate Live AI)"
            return response

        try:
            return self._run_gemini_agent_pipeline(query, active_key, model_name)
        except Exception as e:
            logger.warning(f"Live Gemini Agent error: {e}. Falling back to deterministic engine.")
            fallback = self.deterministic_engine.process_query(query)
            fallback.explanation = f"Notice: Fallback activated due to Live AI exception ({str(e)[:120]}). Enter a valid Google AI Studio key in the UI."
            fallback.live_model = f"Failed ({str(e)[:40]}...) -> Deterministic Fallback"
            return fallback

    def _run_gemini_agent_pipeline(
        self, user_query: str, api_key: str, model_name: str, max_retries: int = 2
    ) -> QueryResponse:
        """
        Full Agentic Reasoning Pipeline:
        1. Dynamic SQL Generation from Natural Language
        2. AST Security & Strict Whitelist Validation
        3. Read-Only Execution in SQLite Sandbox
        4. Autonomous Reflection (Self-Correction on SQL error)
        5. Real-Time BI Synthesis & Chart Generation
        """
        prompt = f"User Question: {user_query}\nGenerate the optimal SQLite query:"
        feedback = ""
        last_error = ""

        # Step 1 & 4: SQL Generation & Reflection Loop
        for attempt in range(max_retries + 1):
            if feedback:
                current_prompt = (
                    f"{prompt}\n\n"
                    f"CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\n"
                    f"Please self-correct the query against the schema and output a valid, executable SQLite query:"
                )
            else:
                current_prompt = prompt

            raw_sql = self._call_gemini(current_prompt, api_key, model_name, SYSTEM_PROMPT)
            clean_sql = self._clean_sql(raw_sql)

            # Check if Gemini flagged as out of scope
            if clean_sql.strip().upper() == "REFUSE":
                return QueryResponse(
                    query=user_query,
                    status="refused",
                    answer=(
                        "I am a specialized Sales Business Intelligence Assistant. "
                        "I can answer questions regarding sales transactions, revenue metrics, products, regions, categories, and trends."
                    ),
                    engine_used="live_gemini_guardrail",
                    live_model=f"Google {model_name} (Active)",
                    explanation="Gemini identified the query as outside the sales intelligence domain."
                )

            # Step 2 & 3: Validate AST and Execute
            try:
                validate_sql_query(clean_sql)
                cols, rows, exec_time = execute_safe_query(self.db_path, clean_sql)
                
                # Step 5: Real-time Executive BI Synthesis
                return self._synthesize_live_bi(
                    user_query, clean_sql, cols, rows, exec_time, api_key, model_name
                )
            except (SecurityValidationError, Exception) as err:
                last_error = str(err)
                feedback = f"Execution failed: {last_error}"
                logger.info(f"Agent reflection triggered on attempt {attempt + 1}: {feedback}")
                if attempt == max_retries:
                    raise RuntimeError(f"Reflection loop exceeded max attempts. Error: {last_error}")

        raise RuntimeError(f"Could not generate valid query: {last_error}")

    def _synthesize_live_bi(
        self,
        query: str,
        sql: str,
        cols: List[str],
        rows: List[Dict[str, Any]],
        exec_time: float,
        api_key: str,
        model_name: str
    ) -> QueryResponse:
        """
        Invokes Gemini to synthesize a structured BI narrative and visualization payload.
        """
        synthesis_input = {
            "user_question": query,
            "executed_sql": sql,
            "row_count": len(rows),
            "columns": cols,
            "sample_data": rows[:15]
        }

        try:
            synthesis_raw = self._call_gemini(
                prompt=f"Input Data:\n{json.dumps(synthesis_input, default=str)}",
                api_key=api_key,
                model_name=model_name,
                system_instruction=SYNTHESIS_PROMPT
            )
            # Clean markdown code blocks from JSON
            synthesis_clean = re.sub(r'```json\s*|\s*```', '', synthesis_raw).strip()
            synth_data = json.loads(synthesis_clean)

            answer = synth_data.get("answer", f"Executed query returned {len(rows)} record(s).")
            takeaway = synth_data.get("takeaway")
            if takeaway:
                answer += f"\n\n> **Key Business Insight:** {takeaway}"

            # Metrics
            metrics = []
            for m in synth_data.get("metrics", []):
                if isinstance(m, dict) and "label" in m and "value" in m:
                    metrics.append(MetricCard(
                        label=str(m["label"]),
                        value=str(m["value"]),
                        subtitle=m.get("subtitle")
                    ))

            # Chart
            chart = None
            c_data = synth_data.get("chart")
            if isinstance(c_data, dict) and c_data.get("labels") and c_data.get("datasets"):
                chart = ChartData(
                    chart_type=c_data.get("chart_type", "bar"),
                    title=c_data.get("title", "Sales Analytics"),
                    labels=c_data.get("labels", []),
                    datasets=c_data.get("datasets", [])
                )

            return QueryResponse(
                query=query,
                status="success",
                answer=answer,
                sql_query=sql,
                execution_time_ms=exec_time,
                row_count=len(rows),
                columns=cols,
                data=rows[:25],
                metrics=metrics,
                chart=chart,
                engine_used="agentic_gemini_engine",
                live_model=f"Google {model_name} (Live)",
                explanation=f"Dynamically generated and synthesized in real-time by Google {model_name}."
            )
        except Exception as e:
            logger.warning(f"Synthesis formatting failed ({e}). Returning basic tabular synthesis.")
            return QueryResponse(
                query=query,
                status="success",
                answer=f"### Live Query Result\n\nFound **{len(rows)}** record(s) matching your inquiry.\n\n"
                       f"```sql\n{sql}\n```",
                sql_query=sql,
                execution_time_ms=exec_time,
                row_count=len(rows),
                columns=cols,
                data=rows[:25],
                engine_used="agentic_gemini_engine",
                live_model=f"Google {model_name} (Live)",
                explanation="Executed dynamic SQL generated by Gemini."
            )

    def _call_gemini(
        self, prompt: str, api_key: str, model_name: str, system_instruction: str
    ) -> str:
        """
        Calls Gemini using Google GenAI SDK (with HTTP REST fallback for resiliency).
        """
        # Primary: Google GenAI official SDK
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    max_output_tokens=1000
                )
            )
            if response and response.text:
                return response.text
        except Exception as sdk_err:
            logger.info(f"GenAI SDK call raised: {sdk_err}. Trying standard Google AI Studio REST fallback.")

        # Secondary: Standard Google AI Studio REST API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt}
                ]
            }],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000
            }
        }
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"Google AI Studio returned HTTP {resp.status_code}: {resp.text}")
        
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates or "content" not in candidates[0]:
            raise RuntimeError("Gemini returned an empty candidate response.")
        
        parts = candidates[0]["content"].get("parts", [])
        return parts[0].get("text", "")

    def _clean_sql(self, sql_str: str) -> str:
        clean = re.sub(r'```sql\s*|\s*```', '', sql_str).strip()
        clean = clean.rstrip(';').strip()
        return clean
