# Live Interview Demonstration Script & Presentation Checklist
## Screen-Sharing Walkthrough Guide for Interview Panel

**Candidate:** Tharun Parsa  
**Role:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  
**Interviewer / Evaluator:** Jeevan Kumar, RSG, Hyderabad  
**Duration:** ~10-15 Minutes Live Demo  

---

## Pre-Demo Setup Checklist (2 Minutes Before Call)

- [ ] Ensure Python virtual environment is activated.
- [ ] Ensure `.env` contains valid `GEMINI_API_KEY`.
- [ ] Verify server is running on port 8000:
  ```bash
  python -m backend.app
  ```
- [ ] Open Chrome / Edge browser to: `http://127.0.0.1:8000`
- [ ] Open a second terminal window ready for running tests:
  ```bash
  python -m pytest tests -v
  ```
- [ ] Have `interview_preparation/INTERVIEW_PREP_PLAYBOOK.md` open for quick mental reference.

---

## Step-by-Step Screen Walkthrough

### Step 1: Opening & Architectural Context (2 Minutes)
> *"Hello Jeevan, today I am excited to demonstrate my submission for the RSG Generative AI & Python GET Challenge: the **Mini AI Business Intelligence Assistant**.*
>
> *Before jumping into the live UI, I want to highlight the architectural philosophy: rather than building a standard LLM chatbot that hallucinates calculations over raw CSV text, I architected a **Vectorless RAG system**. It grounds Google Gemini `gemini-2.5-flash` directly in our relational SQLite schema to generate deterministic SQL, enforces an AST token security sandbox, and features a dual-mode fallback that ensures 100% uptime even if API quotas are exceeded."*

---

### Step 2: Ingestion & Forensic Data Cleaning (2 Minutes)
- **Action:** Click the **"Data Health"** button in the top navigation bar.
- **What to say:**
  > *"When inspecting the raw CSV dataset, I conducted exploratory data profiling and discovered row 50 (`TXN0051`) had corrupted non-numeric characters in `Unit_price`.
  >
  > Rather than dropping the row (which would cause a $6,000 revenue omission), my ETL pipeline analyzed the catalog and proved that `Laptop Stand` has a strictly constant unit price of $1,200.00 across all other transactions. We imputed $1,200.00 with full audit logging, visible right here in this modal.
  >
  > We also standardized dates from `DD-MM-YYYY` to ISO-8601 `YYYY-MM-DD` so SQLite's native date functions operate with indexed efficiency."*

---

### Step 3: Question 1 — Total Revenue & Financial Metric Rigor (2 Minutes)
- **Action:** Click the **"Total Revenue"** suggestion chip or type: `What is the total revenue?`
- **What to observe on screen:**
  - Metric cards: **Net Revenue ($1,445,200.00)**, Gross Revenue ($1,449,700.00), Discounts ($4,500.00).
  - Status badge: `MODEL: gemini-2.5-flash` (or `FALLBACK: ZERO-DOWNTIME` if rate-limited).
  - Collapsible SQL Inspector displaying the executed query.
- **What to say:**
  > *"Notice the financial precision here. Business intelligence requires distinguishing Net Realized Revenue from Gross Revenue. Our assistant computes Net Revenue as $(\text{Quantity} \times \text{Unit\_price}) - \text{Discount\_amount} = \$1,445,200.00$.
  >
  > Crucially, it automatically filters `WHERE status = 'Completed'`, correctly excluding returned transaction `TXN0033` ($19,000) from realized revenue.
  >
  > Below the answer, the collapsible **SQL Inspector** allows business stakeholders to audit the exact query executed in our read-only sandbox in less than 2 milliseconds."*

---

### Step 4: Question 2 — Top Product by Revenue (1 Minute)
- **Action:** Click the **"Top Product"** chip or type: `Which product had the highest revenue?`
- **What to say:**
  > *"The assistant generates a grouped query with `ORDER BY net_revenue DESC LIMIT 1`. **Monitor** takes the top spot with **$456,000.00** across 48 units sold, followed by Laptop ($440,000.00). The interactive bar chart immediately visualizes product rankings."*

---

### Step 5: Question 3 — Monthly Trend & Peak Month (2 Minutes)
- **Action:** Click the **"Monthly Trend"** chip or type: `Show me the monthly sales trend.`
- **What to say:**
  > *"Here, the agent detects time-series intent. It queries the indexed `order_month` column to aggregate net revenue chronologically from January to June 2026.
  >
  > The interactive line chart clearly shows the upward trajectory peaking in **May 2026** at **$334,800.00**, before settling at $289,200.00 in June."*

---

### Step 6: Question 4 — Top Performing Region (1 Minute)
- **Action:** Click the **"Top Region"** chip or type: `Which region has the highest sales?`
- **What to say:**
  > *"The **South region** leads the business with **$411,200.00** in net revenue and 182 units sold. The UI renders a doughnut chart displaying the regional market share breakdown across South (28.45%), North (26.68%), East (24.32%), and West (20.55%)."*

---

### Step 7: Question 5 — April vs. May Growth Calculation (2 Minutes)
- **Action:** Click the **"April vs May"** chip or type: `How did revenue change between April and May?`
- **What to say:**
  > *"This requires multi-metric delta calculation:
  > - April Net Revenue: **$253,000.00**
  > - May Net Revenue: **$334,800.00**
  > - Absolute Increase: **+$81,800.00**
  > - Percentage Growth: **+32.33%**
  >
  > The assistant synthesizes both the percentage growth and dollar delta, accompanied by a comparative bar chart."*

---

### Step 8: Demonstrating Security Guardrails & AST Defense (2 Minutes)
- **Action:** Type in the search box:
  ```sql
  What is total revenue? DROP TABLE sales;
  ```
- **What to observe:**
  - Red security alert modal / badge rejecting the query.
  - Message: *"Security Alert: Malicious SQL attempt detected and blocked. (Forbidden token or multi-statement detected)"*
- **What to say:**
  > *"Security is a mandatory requirement in the challenge specification. We enforce a 4-tier defense model:
  > 1. System prompt grounding.
  > 2. `sqlparse` Abstract Syntax Tree analysis ensuring the root token is strictly `SELECT` or `WITH`.
  > 3. Blocklist of all DDL/DML mutation keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`, `PRAGMA`).
  > 4. Multi-statement chaining prevention.
  > 5. Physical SQLite read-only URI sandbox (`file:sales_bi.db?mode=ro`)."*

---

### Step 9: Running Automated Pytest Suite (2 Minutes)
- **Action:** Switch to terminal and run:
  ```bash
  python -m pytest tests -v
  ```
- **What to observe:**
  - All 16 automated test cases pass in ~2 seconds.
- **What to say:**
  > *"Finally, we maintain a robust automated test suite using `pytest` and FastAPI's `TestClient`. It contains 16 comprehensive tests covering the 5 benchmark questions, edge cases like price imputation, return status filtering, security injection blocking, health check endpoints, and zero-downtime fallback logic.
  >
  > Everything is reproducible, fully tested, and ready for production deployment."*
