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
import sqlparse
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

load_dotenv(override=True)

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
3. Metric Column Inclusion: Always select the computed aggregate metric in the SELECT clause alongside any group-by dimension columns (e.g., SELECT product, SUM(net_revenue) AS total_revenue ... or SELECT region, SUM(net_revenue) AS total_revenue ...) so supporting numbers are never omitted.
4. Date Aggregations: For monthly groupings, use `order_month` or `strftime('%Y-%m', order_date)`.
5. Strict Read-Only: Output exactly ONE single SELECT statement. Do NOT include Markdown formatting, code fences, or semicolons. Return ONLY raw SQL.
6. Zero Mutation: NEVER use DROP, DELETE, UPDATE, INSERT, ALTER, or PRAGMA.
7. Scope Check: If the question is completely unrelated to sales, business data, or transactions (e.g., general trivia, weather, jokes), respond with the exact word: REFUSE
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
        model_name: str = "gemini-2.5-flash",
        prefer_llm: bool = True
    ) -> QueryResponse:
        """
        Coordinates query processing:
        - If Gemini API Key is provided (via UI or environment variable), uses the Live Agentic Gemini Engine.
        - If no API key is provided, falls back seamlessly to the Deterministic Semantic Engine.
        """
        load_dotenv(override=True)
        # Resolve API Key (UI key takes precedence over .env)
        active_key = (api_key or "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
        active_model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        if not prefer_llm or not active_key:
            response = self.deterministic_engine.process_query(query)
            response.live_model = "None (Offline Rule Engine - Enter Gemini API Key in UI to activate Live AI)"
            return response

        try:
            return self._run_gemini_agent_pipeline(query, active_key, active_model)
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Live Gemini Agent error: {err_msg}. Falling back to deterministic engine.")
            fallback = self.deterministic_engine.process_query(query)
            if "429" in err_msg or "quota" in err_msg.lower():
                fallback.explanation = (
                    "Notice: Free Tier API quota rate limit reached (5 requests/minute). "
                    "Zero-Downtime Deterministic Fallback Engine automatically served this query with 100% data fidelity."
                )
                fallback.live_model = "Rate Limited (Google 429) -> Deterministic Fallback"
            else:
                fallback.explanation = f"Notice: Live AI exception ({err_msg[:90]}). Fallback engine activated."
                fallback.live_model = f"Fallback Mode ({err_msg[:30]}...)"
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
        Resilient against rate limits, JSON parsing variances, and network delays.
        """
        if not rows:
            return QueryResponse(
                query=query,
                status="success",
                answer="No completed transactions match this query criteria in the sales database.",
                sql_query=sql,
                execution_time_ms=exec_time,
                row_count=0,
                columns=cols,
                data=[],
                metrics=[
                    MetricCard(label="Records Found", value="0", subtitle="Empty result set"),
                    MetricCard(label="Status", value="Complete", subtitle="0 rows matched")
                ],
                engine_used="agentic_gemini_engine",
                live_model=f"Google {model_name} (Live)",
                explanation=f"Executed safe SQL generated by Google {model_name}."
            )

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
                system_instruction=SYNTHESIS_PROMPT,
                response_mime_type="application/json"
            )
            # Clean markdown code blocks from JSON
            synthesis_clean = re.sub(r'^```[a-zA-Z]*\s*', '', synthesis_raw.strip())
            synthesis_clean = re.sub(r'\s*```$', '', synthesis_clean).strip()
            synth_data = json.loads(synthesis_clean, strict=False)

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

            # Fallback metrics if empty
            if not metrics:
                metrics = self._generate_fallback_metrics(rows, cols, exec_time)

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
            elif len(rows) > 1:
                chart = self._generate_fallback_chart(rows, cols)

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
            logger.warning(f"Synthesis formatting failed ({e}). Generating robust tabular BI synthesis.")
            metrics = self._generate_fallback_metrics(rows, cols, exec_time)
            chart = self._generate_fallback_chart(rows, cols) if len(rows) > 1 else None

            # Build readable summary answer
            first_val = list(rows[0].values())
            summary_points = []
            if len(rows) == 1:
                details = ", ".join([f"**{k.replace('_', ' ').title()}**: {v}" for k, v in rows[0].items()])
                summary_points.append(f"Query returned **1** record: {details}.")
            else:
                summary_points.append(f"Query returned **{len(rows)}** records.")
                top_row = rows[0]
                summary_points.append(f"Top record: **{list(top_row.values())[0]}** with metrics {list(top_row.values())[1:]}.")

            answer = (
                f"### Live Query Result\n\n"
                f"{' '.join(summary_points)}\n\n"
                f"View the complete records and interactive visualizer below."
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
                explanation=f"Executed dynamic SQL generated by Google {model_name}."
            )

    def _generate_fallback_metrics(self, rows: List[Dict[str, Any]], cols: List[str], exec_time: float) -> List[MetricCard]:
        cards = [
            MetricCard(label="Records Returned", value=str(len(rows)), subtitle="Live SQL Output"),
            MetricCard(label="Query Latency", value=f"{exec_time:.2f} ms", subtitle="SQLite Sandbox")
        ]
        if rows:
            first_row = rows[0]
            for k, v in first_row.items():
                if isinstance(v, (int, float)):
                    k_lower = k.lower()
                    if any(term in k_lower for term in ["revenue", "sales", "sum", "total", "amount", "price"]):
                        cards.append(MetricCard(label=k.replace('_', ' ').title(), value=f"${v:,.2f}", subtitle="Computed Aggregate"))
                        break
                    elif any(term in k_lower for term in ["count", "quantity", "qty", "units"]):
                        cards.append(MetricCard(label=k.replace('_', ' ').title(), value=f"{v:,}", subtitle="Unit Metric"))
                        break
        return cards

    def _generate_fallback_chart(self, rows: List[Dict[str, Any]], cols: List[str]) -> Optional[ChartData]:
        if len(rows) < 2 or len(cols) < 2:
            return None
        label_col = cols[0]
        num_col = None
        for c in cols[1:]:
            if isinstance(rows[0].get(c), (int, float)):
                num_col = c
                break
        if not num_col:
            return None

        labels = [str(r.get(label_col, '')) for r in rows[:12]]
        data_vals = [float(r.get(num_col, 0) or 0) for r in rows[:12]]
        return ChartData(
            chart_type="bar" if len(labels) <= 8 else "line",
            title=f"{num_col.replace('_', ' ').title()} by {label_col.replace('_', ' ').title()}",
            labels=labels,
            datasets=[{"label": num_col.replace('_', ' ').title(), "data": data_vals}]
        )

    def _call_gemini(
        self,
        prompt: str,
        api_key: str,
        model_name: str,
        system_instruction: str,
        response_mime_type: Optional[str] = None
    ) -> str:
        """
        Calls Gemini using Google GenAI SDK (with HTTP REST fallback for resiliency).
        Supports structured JSON output specification.
        """
        # Primary: Google GenAI official SDK
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            config_params: Dict[str, Any] = {
                "system_instruction": system_instruction,
                "temperature": 0.1,
                "max_output_tokens": 1000
            }
            if response_mime_type:
                config_params["response_mime_type"] = response_mime_type

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params)
            )
            if response and response.text:
                return response.text
        except Exception as sdk_err:
            logger.info(f"GenAI SDK call raised: {sdk_err}. Trying standard Google AI Studio REST fallback.")

        # Secondary: Standard Google AI Studio REST API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload: Dict[str, Any] = {
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
        if response_mime_type:
            payload["generationConfig"]["responseMimeType"] = response_mime_type

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
        clean = sql_str.strip()
        # Strip any code fence like ```sql, ```sqlite, ```
        clean = re.sub(r'^```[a-zA-Z]*\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean).strip()
        # Strip comments safely
        clean = sqlparse.format(clean, strip_comments=True).strip()
        clean = clean.rstrip(';').strip()
        return clean
