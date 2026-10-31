# Official Candidate Submission Pack
## Mini AI Business Intelligence Assistant — GET Selection Assessment

**Candidate Name:** Tharun Parsa  
**Target Position:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  
**Reporting Manager / Evaluator:** Jeevan Kumar, RSG  
**Assessment Challenge:** AI-Assisted Development Challenge: Mini AI Business Intelligence Assistant  
**Repository Branch:** `main`  
**Submission Date:** October 2026  

---

## 1. Executive Summary

This submission package delivers a production-grade, mathematically verified **Mini AI Business Intelligence Assistant** that allows business users to ask natural language questions regarding sales data and receive deterministic, auditable answers backed by database queries.

Rather than relying on unconstrained LLM text generation that hallucinates calculations, the application implements a **Vectorless RAG (Agentic Text-to-SQL)** architecture with a **Four-Tier Defense-in-Depth Security Sandbox** and an automated **Zero-Downtime Deterministic Fallback Engine**.

---

## 2. Submission Pack Directory Contents

This folder (`submission_pack/`) contains all the required documentation specifically requested by the challenge specification:

| File Name | Description |
|---|---|
| **[AI_ASSISTED_DEVELOPMENT_REPORT.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/submission_pack/AI_ASSISTED_DEVELOPMENT_REPORT.md)** | **Mandatory Assessment Deliverable:** Direct answers to the 5 challenge questions regarding AI tools, development usage, problems encountered, debugging techniques, and future roadmap. |
| **[SYSTEM_ARCHITECTURE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/submission_pack/SYSTEM_ARCHITECTURE.md)** | **Technical Specification:** High-level Mermaid architecture diagram, component boundaries, and 4-tier security sandbox design. |
| **[BENCHMARK_RESULTS.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/submission_pack/BENCHMARK_RESULTS.md)** | **Ground Truth Benchmarks:** Exact verified answers, executed SQL queries, and accounting rationale for all 5 example questions. |
| **[SUBMISSION_CHECKLIST.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/submission_pack/SUBMISSION_CHECKLIST.md)** | **Requirements Checklist:** Line-by-line verification against all criteria in `AI Assisted Development Challenge - GET.docx`. |

*(Note: For candidate interview preparation, 25+ technical Q&As, elevator pitches, and Architectural Decision Records, refer to the separate `interview_preparation/` directory).*

---

## 3. Quickstart Guide (Run & Verify in Under 60 Seconds)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Set Google AI Studio API Key
To enable real-time Live Gemini AI:
- Configure `.env`:
  ```ini
  GEMINI_API_KEY=your_google_ai_studio_api_key_here
  GEMINI_MODEL=gemini-2.5-flash
  HOST=127.0.0.1
  PORT=8000
  ```
> **Evaluator Note:** If you do not have an API key or prefer not to use one, **no configuration is required**. The application will automatically execute using the high-performance **Offline Deterministic Semantic Engine** with instant response times and 100% data fidelity.

### Step 3: Start the Backend Server
```bash
python -m backend.app
```
Open your browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**  
Interactive Swagger API documentation: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### Step 4: Execute Automated Test Suite
```bash
python -m pytest tests/test_assistant.py -v
```
*Expected Result: 16 passed in ~2.0 seconds.*

---

## 4. Key Functional Highlights

1. **Dual-Mode AI Engine:**
   - **Live Agentic Mode:** Connects to Google AI Studio (`gemini-2.5-flash`), with autonomous reflection self-correction loops and structured JSON output.
   - **Zero-Downtime Deterministic Fallback:** Automatically serves requests if Google AI Studio Free Tier rate limits (5 RPM) or network disruptions occur.
2. **Four-Tier Defense-in-Depth Security:**
   - Abstract Syntax Tree (AST) validation via `sqlparse`.
   - Mutation blocking (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`, `PRAGMA`).
   - Semicolon-chaining prevention.
   - Physical read-only SQLite URI sandbox (`file:sales_bi.db?mode=ro`).
3. **Forensic ETL Pipeline:**
   - Imputed corrupted unit price for `TXN0051` based on catalog modal price consistency ($1,200.00 for Laptop Stand).
   - Preserved returned order `TXN0033` ($19,000.00) while properly excluding it from net completed revenue.
   - Converted `DD-MM-YYYY` dates to ISO-8601 `YYYY-MM-DD` and indexed `order_month` for instant time-series aggregation.
4. **Interactive Dashboard:**
   - Modern glassmorphic interface with quick-action benchmark chips, dynamic Chart.js charts, SQL Inspector, and ETL Data Health modal.
