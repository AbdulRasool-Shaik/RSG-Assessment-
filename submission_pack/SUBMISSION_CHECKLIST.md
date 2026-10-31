# Requirements Compliance Checklist
## Assessment Verification against `AI Assisted Development Challenge - GET.docx`

**Candidate:** Tharun Parsa  
**Assessment:** AI-Assisted Development Challenge: Mini AI Business Intelligence Assistant  
**Evaluation Target:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  

---

## Deliverables & Functional Requirements Verification

### 1. Data Management
- [x] **Load the supplied CSV into a database:** Ingested into SQLite database `sales_bi.db` via `backend/etl.py`.
- [x] **Handle missing or invalid records appropriately:**
  - Imputed missing unit price for `TXN0051` ($1,200.00 for Laptop Stand based on modal catalog price).
  - Handled returned order `TXN0033` ($19,000.00) by excluding it from completed revenue while preserving transactional integrity.
  - Handled zero quantity record `TXN0034` with logged audit record.
  - Converted `DD-MM-YYYY` dates to ISO-8601 `YYYY-MM-DD` and added indexed `order_month` column.
- [x] **Explain how the data is stored and queried:** Documented in [SYSTEM_ARCHITECTURE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/submission_pack/SYSTEM_ARCHITECTURE.md) and viewable in the UI Data Health modal.

### 2. Backend
- [x] **Build an API that accepts a user's question:** `POST /api/query` built with FastAPI.
- [x] **Process the question and return a structured answer:** Returns JSON schema with `answer`, `sql_query`, `data`, `metrics`, `chart`, `engine_used`, and `live_model`.
- [x] **Handle invalid requests and errors:**
  - Empty or null queries rejected with HTTP 400.
  - Semicolon-chained or destructive SQL attempts blocked and returned as security alerts without crashing.
  - Google AI Studio Free Tier rate limits (HTTP 429) automatically handled with zero-downtime deterministic fallback.

### 3. Analytics
- [x] **Support at least four of the five example questions:** All 5 core questions fully supported:
  1. What is the total revenue? ($1,445,200.00 Net)
  2. Which product generated highest revenue? (Monitor: $473,000.00)
  3. What is the monthly revenue trend? (Jan–Jun 2026, peak in May at $318,500.00)
  4. Which region generated highest sales? (South: $411,200.00, 182 units)
  5. How did revenue change between two months? (+32.32% / +$77,800.00 from April to May)
- [x] **Calculate results using database queries or deterministic logic:** Verified with actual SQLite SQL queries in read-only sandbox.
- [x] **Display the supporting figures used to produce the answer:** Metric cards, Chart.js visualizer, SQL Inspector, and tabular row preview.

### 4. AI Integration
- [x] **Use an LLM or an AI-assisted interpretation mechanism:** Google AI Studio Gemini API (`gemini-2.5-flash`) integrated via official `google-genai` SDK.
- [x] **Validate the generated query before execution:** AST token analysis using `sqlparse` verifying single-statement `SELECT` queries.
- [x] **Do not allow destructive database operations:** Banned keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`, `PRAGMA`) + physical read-only SQLite URI connection (`file:sales_bi.db?mode=ro`).
- [x] **Explain how you prevent unsupported or incorrect answers:** Guardrail intent router, domain refusal checks, schema grounding in system prompt, and autonomous reflection loops.

### 5. User Interface
- [x] **Provide a simple interface to enter questions and view results:** Modern web UI served at `http://127.0.0.1:8000`.
- [x] **Display the answer and relevant supporting data:** Formatted Markdown answer, metric cards, Chart.js trend charts, and collapsible SQL Inspector.

### 6. Testing
- [x] **Include at least five test cases:** 16 automated pytest cases implemented in `tests/test_assistant.py` (100% pass rate).
- [x] **Test valid questions, invalid questions, and at least one edge case:**
  - Valid: 5 core benchmark tests + channel breakdown.
  - Invalid / Malicious: Semicolon injection, `DROP TABLE`, `UPDATE`, out-of-domain query.
  - Edge Cases: `TXN0051` price imputation, `TXN0033` returned order exclusion.
- [x] **Document known limitations:** Fully documented in `README.md` (e.g. Free Tier 5 RPM rate limits, single-table scope, English localization).

### 7. Deliverables Checklist
- [x] **Source code in a Git repository:** Clean git history on branch `main`.
- [x] **README with setup and execution instructions:** Complete `README.md` at root.
- [x] **Architecture diagram or explanation:** [SYSTEM_ARCHITECTURE.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/submission_pack/SYSTEM_ARCHITECTURE.md).
- [x] **Automated tests:** `tests/test_assistant.py`.
- [x] **AI-assisted development report:** [AI_ASSISTED_DEVELOPMENT_REPORT.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/submission_pack/AI_ASSISTED_DEVELOPMENT_REPORT.md).
