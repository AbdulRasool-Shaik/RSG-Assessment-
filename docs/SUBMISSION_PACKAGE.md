# Mini AI Business Intelligence Assistant
## Official Candidate Submission Package & Evaluator Guide

**Candidate Name:** Tharun Parsa  
**Target Role:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  
**Reporting Manager / Evaluator:** Jeevan Kumar, RSG  
**Assessment:** AI-Assisted Development Challenge: Mini AI Business Intelligence Assistant  
**Date of Submission:** October 2026  
**Repository Branch:** `main`  

---

## 1. Executive Summary

This submission package delivers a production-grade **Mini AI Business Intelligence Assistant** that allows business users to ask natural language questions regarding sales transactions and receive verifiable, mathematically precise answers grounded directly in actual SQLite database execution.

Rather than relying on unconstrained LLM text generation that hallucinates calculations, the application implements a **Vectorless RAG (Agentic Text-to-SQL)** architecture with a **Four-Tier Defense-in-Depth Security Sandbox** and an automated **Zero-Downtime Deterministic Fallback Engine**.

---

## 2. Deliverables Checklist (Per Challenge Requirements)

| # | Required Deliverable (from Word Document) | Status | Location in Codebase |
|---|---|:---:|---|
| **1** | **Source Code in Git Repository** | Complete | Committed to `main` branch with descriptive atomic commit history. |
| **2** | **README with Setup & Execution Instructions** | Complete | [README.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/README.md) |
| **3** | **Architecture Diagram & Technical Specification** | Complete | [docs/ARCHITECTURE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/ARCHITECTURE.md) |
| **4** | **Automated Test Suite (Minimum 5 required)** | Complete (16 tests) | [tests/test_assistant.py](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/tests/test_assistant.py) |
| **5** | **AI-Assisted Development Report** | Complete | [docs/AI_ASSISTED_DEVELOPMENT_REPORT.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/AI_ASSISTED_DEVELOPMENT_REPORT.md) |
| **6** | **Architectural Decision Records (ADRs)** | Complete (10 ADRs) | [docs/DECISIONS_LOG.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/DECISIONS_LOG.md) |
| **7** | **Interview Preparation & Defense Guide** | Complete | [docs/INTERVIEW_PREP_GUIDE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/INTERVIEW_PREP_GUIDE.md) |

---

## 3. Quickstart & Verification (Under 60 Seconds)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Configure Google AI Studio Key
A functional `.env` file can be configured to activate real-time Gemini AI:
```ini
GEMINI_API_KEY=your_google_ai_studio_api_key_here
GEMINI_MODEL=gemini-2.5-flash
HOST=127.0.0.1
PORT=8000
```
> **Evaluator Note:** If you do not have an API key or prefer not to use one, **no configuration is required**. The application will automatically execute using the high-performance **Offline Deterministic Semantic Engine** with instant response times and 100% data fidelity.

### Step 3: Launch Application
```bash
python -m backend.app
```
Access the interactive dashboard at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**  
Interactive Swagger API docs: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### Step 4: Run Automated Tests
```bash
python -m pytest tests/test_assistant.py -v
```
*Expected: 16 passed in ~2.0 seconds.*

---

## 4. Ground Truth Analytical Benchmarks

All benchmark figures have been verified against the cleaned SQLite database:

| # | Example Question | Executed SQL Logic | Ground Truth Verified Result |
|---|---|---|---|
| **Q1** | **"What is the total revenue?"** | `SELECT SUM(net_revenue) FROM sales WHERE status = 'Completed'` | **$1,445,200.00 Net** ($1,449,700.00 Gross, $4,500.00 Discounts across 50 completed orders) |
| **Q2** | **"Which product generated the highest revenue?"** | `SELECT product, SUM(net_revenue) FROM sales WHERE status = 'Completed' GROUP BY product ORDER BY 2 DESC LIMIT 1` | **Monitor ($473,000.00 Net Revenue, 52 units)** |
| **Q3** | **"What is the monthly revenue trend?"** | `SELECT order_month, SUM(net_revenue) FROM sales WHERE status = 'Completed' GROUP BY order_month ORDER BY 1 ASC` | **6-month trend (Jan–Jun 2026), peaking in May ($318,500.00)** |
| **Q4** | **"Which region generated the highest sales?"** | `SELECT region, SUM(net_revenue), SUM(quantity) FROM sales WHERE status = 'Completed' GROUP BY region ORDER BY 2 DESC` | **South ($411,200.00 Net Revenue, 182 units sold)** |
| **Q5** | **"How did revenue change between two months?"** | Compares April ($240,700.00) vs. May ($318,500.00) | **Increased by +$77,800.00 (+32.32%)** |

---

## 5. Forensic Data Cleaning Summary

During the dataset profiling stage (`ai_bi_assistant_sales_data - GET.csv`), three critical data quality anomalies were identified and resolved with complete audit transparency:

1. **`TXN0051` (Corrupted Unit Price):**
   - *Issue:* The unit price contained corrupted bytes resulting in `NaN`, which would distort downstream revenue totals if deleted.
   - *Resolution:* Imputed unit price to `$1,200.00` based on catalog modal price consistency for `Laptop Stand`. Preserved $6,000 in legitimate revenue.
2. **`TXN0033` (Returned Order Exclusion):**
   - *Issue:* Transaction had `status = 'Returned'` (Monitor, 2 units, $19,000.00). Including returns as realized income is a major business accounting error.
   - *Resolution:* Retained in SQLite table for transactional completeness, but excluded from net revenue aggregations (`WHERE status = 'Completed'`).
3. **`TXN0034` (Zero Quantity Order):**
   - *Issue:* Transaction had `quantity = 0`.
   - *Resolution:* Preserved for audit integrity; yields $0.00 net and gross revenue.
4. **Date Normalization:**
   - Standardized `DD-MM-YYYY` text timestamps to ISO-8601 `YYYY-MM-DD` and indexed `order_month` (`YYYY-MM`) for native SQLite time-series performance.

---

## 6. Security Architecture & Guardrails

To meet and exceed Requirement 4 (*"Do not allow destructive database operations"*), a **Four-Tier Defense-in-Depth Security Model** was implemented:

1. **Schema Grounding & System Prompt Constraints:** LLM is strictly instructed to generate single read-only `SELECT` statements.
2. **AST Token Parsing (`sqlparse`):** Validates the abstract syntax tree to ensure the statement type is strictly `SELECT` or `WITH ... SELECT`.
3. **Keyword Mutation Blocker:** Permanently rejects `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `EXEC`, `PRAGMA`.
4. **Semicolon Query Stacking Defense:** Intercepts and blocks semicolon chaining attacks (`SELECT ...; DROP TABLE sales;`).
5. **Physical Engine-Level Sandbox:** Database connection is opened with read-only URI semantics (`file:sales_bi.db?mode=ro`).

---

## 7. Rate-Limit Resilience (Zero Downtime)

Google AI Studio Free Tier enforces a strict quota of **5 requests per minute (RPM)**. When multiple queries are submitted in rapid succession:
- The backend intercepts HTTP 429 quota exceptions.
- The **Agentic Query Coordinator** automatically falls back to the **Deterministic Semantic Engine**.
- The user receives an immediate 100% accurate result (< 2ms) with an informative UI badge: `⚡ RATE LIMITED (ZERO-DOWNTIME FALLBACK)`.
- **Result:** The system never crashes or hangs, guaranteeing high availability during live evaluations.

---

## 8. Summary of Evaluation Criteria Alignment

| Evaluation Criteria | Demonstrated Engineering Evidence |
|---|---|
| **Working Functionality** | End-to-end working system with interactive UI, real-time Chart.js charts, and live model execution. |
| **Programming Fundamentals** | Modular architecture, Pydantic type safety, asynchronous FastAPI lifespan management, and clean object-oriented separation of concerns. |
| **Backend & Database Design** | Normalized schema, B-tree analytical indexing, read-only sandboxing, and forensic ETL data cleaning pipeline. |
| **Correctness & Reliability** | Verified ground-truth financials, 16 passing automated tests, zero-downtime rate-limit resilience. |
| **Appropriate Use of AI** | Vectorless RAG architecture, schema grounding, reflection self-correction loops, and structured JSON mode. |
| **Testing & Error Handling** | 16 pytest cases covering valid, invalid, injection attacks, and edge cases with 100% pass rate. |
| **Ability to Explain Decisions** | Complete documentation suite ([INTERVIEW_PREP_GUIDE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/INTERVIEW_PREP_GUIDE.md), [DECISIONS_LOG.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/DECISIONS_LOG.md), [ARCHITECTURE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/docs/ARCHITECTURE.md)). |
