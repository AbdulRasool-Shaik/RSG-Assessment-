# Mini AI Business Intelligence Assistant
### Vectorless RAG • AST-Validated Text-to-SQL • Read-Only Sandboxed Intelligence

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Read--Only%20Sandbox-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-12%20Passed%20(100%25)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/Assessment-RSG%20GET%20Selection-orange.svg)]()

> A robust, deterministic Sales Business Intelligence Assistant built for the **AI-Assisted Development Challenge (Graduate Engineer Trainee Selection — RSG)**.

---

## 🌟 Highlights & Key Capabilities

- **Live Google AI Studio Gemini Integration (Agentic AI):**
  - Connects to **Google Gemini (Gemini 1.5 Flash / 2.5 Flash)** in real-time.
  - **Dynamic UI API Key Entry:** Evaluators can paste their Google AI Studio API key directly into the UI header or store it in `.env` without restarting the server!
  - **Autonomous Reflection Loop:** If generated SQL produces an error, the agent intercepts the exception and prompts Gemini to self-correct and re-execute.
  - **Real-Time Executive BI Synthesis:** Gemini analyzes the actual database rows and dynamically synthesizes an executive summary, key metrics, and Chart.js visualization data.
- **Deterministic Offline Fallback:**
  - Works out-of-the-box with **zero API keys required**, guaranteeing that evaluators can run the project offline with instant response times.
- **Four-Tier Defense-in-Depth Security:**
  - System prompt constraints.
  - **Abstract Syntax Tree (AST) validation (`sqlparse`)** ensuring root commands are strictly `SELECT` or `WITH`.
  - Mutation blocking (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`) and semicolon query-stacking defense.
  - **Physical Read-Only Sandbox** (`file:sales_bi.db?mode=ro`).
- **Forensic ETL Data Cleaning:**
  - Imputes corrupted row `TXN0051` (missing unit price) based on modal catalog price consistency ($1,200.00 for Laptop Stand).
  - Excludes returned order `TXN0033` ($19,000) from realized revenue while preserving audit records.
  - Converts `DD-MM-YYYY` dates to ISO-8601 (`YYYY-MM-DD`) and indexes `order_month` for sub-millisecond time series grouping.
- **Interactive Modern BI Dashboard:**
  - Real-time Gemini Key connection & verification control.
  - Live model badge (`🟢 LIVE: GEMINI 1.5 FLASH` vs `OFFLINE DETERMINISTIC`).
  - One-click benchmark query chips for all 5 core questions.
  - Dynamic **Chart.js** visualizations (bar, line, and doughnut charts).
  - **SQL Inspector** showing the executed SQL query, execution latency, and row count.
  - Supporting database records table with formatted currency.
  - **Data Health Modal** displaying real-time ETL audit logs.
- **100% Automated Test Suite:** 13 automated unit and integration tests passing in ~2 seconds.

---

## 📐 Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    MINI AI BI ASSISTANT ARCHITECTURE                               |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [ User Natural Language Query ]                                                                    |
|               |                                                                                    |
|               v                                                                                    |
|  [ Layer 1: Intent & Guardrails Router ] ---> Out of Scope / Malicious Request Detection            |
|               | (Valid Query)                                                                      |
|               v                                                                                    |
|  [ Layer 2: Vectorless RAG / Text-to-SQL Coordinator ]                                             |
|         - Schema-grounded System Prompt & Few-Shot Context                                         |
|         - Deterministic Fallback Parser (Zero-LLM Offline Mode)                                    |
|               |                                                                                    |
|               v                                                                                    |
|  [ Layer 3: AST Query Validator & Security Sandbox ]                                               |
|         - sqlparse AST Tokenizer (Strict SELECT-only whitelist)                                   |
|         - Mutation Blocker (Blocks DROP, DELETE, UPDATE, INSERT, ALTER, EXEC)                      |
|         - Multi-statement Blocker (Prevents stacked SQL injection)                                |
|               |                                                                                    |
|               v                                                                                    |
|  [ Layer 4: SQLite Analytical Database (Read-Only URI Sandbox) ]                                    |
|         - Cleaned Sales Data (Imputed TXN0051, ISO-8601 Dates, Computed Net Revenue)               |
|               |                                                                                    |
|               v                                                                                    |
|  [ Layer 5: Response Synthesizer & BI Formatting Engine ]                                          |
|         - Structured JSON: Natural Answer + Executed SQL + Raw Metrics + Chart Ready Data           |
|               |                                                                                    |
|               v                                                                                    |
|  [ Layer 6: Interactive Web UI ] (Query Input, SQL Inspector, Data Tables, Trend Charts)          |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python -m backend.app
```
*The server will start at: `http://127.0.0.1:8000`*

### 4. Open in Browser
Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)** to interact with the dashboard.

*(Optional) Interactive API documentation is available at **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.*

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:
```bash
python -m pytest tests/test_assistant.py -v
```

**Test Execution Summary:**
- 12 passed in 1.46s (100% pass rate).
- Validates all 5 core questions, data imputation of `TXN0051`, exclusion of returned order `TXN0033`, AST SQL injection defense, mutation blocking, and out-of-domain refusals.

---

## 📊 Ground Truth Benchmarks (Excluding Returned TXN0033)

| Question | Executed Query Logic | Ground Truth Result |
| :--- | :--- | :--- |
| **1. What is the total revenue?** | `SUM(net_revenue) WHERE status = 'Completed'` | **$1,445,200.00** Net ($1,449,700.00 Gross, $4,500.00 Discounts) |
| **2. Which product generated highest revenue?** | `GROUP BY product ORDER BY net_revenue DESC` | **Monitor ($473,000.00 Net Revenue, 52 units)** |
| **3. What is the monthly revenue trend?** | `GROUP BY order_month ORDER BY order_month ASC` | **6-month trajectory; Peak in May 2026 ($318,500.00)** |
| **4. Which region generated highest sales?** | `GROUP BY region ORDER BY net_revenue DESC` | **South ($411,200.00 Net Revenue, 182 units sold)** |
| **5. How did revenue change between two months?** | Compare April (`$240,700.00`) vs. May (`$318,500.00`) | **Increased by +$77,800.00 (+32.32%)** |

---

## 📚 Complete Project Documentation

| Document | Description |
| :--- | :--- |
| **[docs/INTERVIEW_PREP_GUIDE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/INTERVIEW_PREP_GUIDE.md)** | **Your Interview Playbook**: 60s elevator pitch, 3-min walkthrough, live demo script, and 25+ technical Q&As. |
| **[docs/DECISIONS_LOG.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/DECISIONS_LOG.md)** | **Architectural Decision Records (ADRs)**: Detailed justifications and trade-off analysis for all 9 key technical decisions. |
| **[docs/AI_ASSISTED_DEVELOPMENT_REPORT.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/AI_ASSISTED_DEVELOPMENT_REPORT.md)** | **Mandatory Assessment Deliverable**: Answers the 5 assessment questions regarding AI tools, debugging, and roadmap. |
| **[docs/ARCHITECTURE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/ARCHITECTURE.md)** | **Technical Specification**: Mermaid diagrams, component boundaries, and security model. |

---

## 📡 REST API Reference

### `POST /api/query`
Executes natural language sales question.

**Request Body:**
```json
{
  "query": "What is the total revenue?",
  "use_llm": true
}
```

**Response Payload:**
```json
{
  "query": "What is the total revenue?",
  "status": "success",
  "answer": "### Total Sales Revenue Summary\n\n- **Net Realized Revenue:** **$1,445,200.00**...",
  "sql_query": "SELECT COUNT(*) AS completed_orders, SUM(quantity) AS total_units_sold, ROUND(SUM(gross_revenue), 2) AS total_gross_revenue, ROUND(SUM(discount_amount), 2) AS total_discounts, ROUND(SUM(net_revenue), 2) AS total_net_revenue FROM sales WHERE status = 'Completed'",
  "execution_time_ms": 1.42,
  "row_count": 1,
  "metrics": [
    { "label": "Net Revenue", "value": "$1,445,200.00", "subtitle": "Realized Income" }
  ],
  "engine_used": "deterministic_semantic_engine"
}
```

## ⚠️ Known Limitations

In compliance with the challenge documentation guidelines, the following known limitations and architectural boundaries of this prototype are documented:

1. **Single-Table Analytical Scope:**
   - The current SQLite database models a single denormalized analytical table (`sales`). While ideal for transactional sales reporting, an enterprise deployment would model snowflake schemas with normalized dimension tables (`customers`, `warehouses`, `promotions`).
2. **Deterministic Offline Fallback Boundary:**
   - The zero-API-key deterministic engine supports the 5 core benchmark questions, date variances, volume analytics, and category/channel breakdowns. Arbitrary or deeply nested ad-hoc questions (e.g., *"Calculate the median order value for online retail in Q1 excluding Mondays"*) require an active LLM API key (`OPENAI_API_KEY` or `GEMINI_API_KEY`) for dynamic Text-to-SQL compilation.
3. **Language & Locale Localization:**
   - Intent recognition and date-month parsing are currently localized for English (`January`–`June`, `Q1`, `Q2`). Multilingual support would require a multilingual semantic embedding layer.
4. **OLAP Concurrency vs. Distributed Scale:**
   - SQLite with read-only connection sandboxing provides sub-2ms query latency for thousands of transactions. For petabyte-scale big data analytics, migrating to a columnar data warehouse like **ClickHouse**, **Snowflake**, or **Amazon Redshift** is recommended.

---

## 🛡️ Security Policies Enforced

1. **AST Token Parsing:** Only queries where the root AST token is `SELECT` or `WITH` are permitted.
2. **Strict Keyword Blacklist:** `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `EXEC`, `PRAGMA` are permanently blocked.
3. **No Semicolon Stacking:** Queries containing multiple statements separated by semicolons are immediately rejected.
4. **Read-Only Database Sandbox:** SQLite connection URI enforces physical read-only mode (`?mode=ro`).
