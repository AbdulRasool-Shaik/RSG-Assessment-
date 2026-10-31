# AI-Assisted Development Report
## Mandatory Assessment Deliverable — RSG GET Selection

**Candidate Name:** Tharun Parsa  
**Target Position:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  
**Assessment:** AI-Assisted Development Challenge: Mini AI Business Intelligence Assistant  
**Date:** October 2026  

---

## 1. Which AI Tools You Used

During the research, architecture, development, and testing phases of this project, the following AI-assisted tools and cognitive engines were utilized:

1. **Antigravity AI Agentic IDE (DeepMind Advanced Agentic Coding Engine):**
   - Used as the primary agentic pair-programming orchestrator for autonomous workspace exploration, file manipulation, and terminal execution.
2. **Google AI Studio & Official `google-genai` SDK (`gemini-2.5-flash`):**
   - Employed as the live intelligence backend for dynamic natural language Text-to-SQL generation, reflection self-correction loops, and structured JSON executive BI synthesis.
3. **Claude 3.5 Sonnet / Gemini 1.5 Pro (Generative AI Models):**
   - Utilized for conceptual architecture design, AST tokenization logic, prompt engineering for Vectorless RAG, and generating synthetic security attack vectors.
4. **Python `sqlparse` Abstract Syntax Tree (AST) Analyzer:**
   - Employed as an algorithmic lexical and grammatical token parser for verifying SQL safety before execution.

---

## 2. How You Used AI During Development

AI tools were employed systematically as cognitive force-multipliers across all five phases of software development:

### A. Data Forensic Discovery & Profiling
- AI was used to execute automated pandas profiling scripts across `ai_bi_assistant_sales_data - GET.csv`.
- Prompted AI to detect distribution anomalies, verify price consistency across categories, and inspect non-numeric byte patterns in `TXN0051`.
- Formulated the modal catalog price imputation rule ($1,200.00 for Laptop Stand).

### B. Prompt Engineering & Vectorless RAG Architecture
- Designed a concise, schema-grounded system prompt embedding the SQLite data dictionary and business constraints (e.g., filtering `status = 'Completed'`, enforcing aggregate metric column selection).
- Integrated an **autonomous reflection loop**: structuring prompt feedback loops where database execution errors or AST validation rejections are passed back to the model for self-correction (up to 2 retries).

### C. Security Sandbox & Guardrail Implementation
- Formulated a four-tier defense-in-depth model with AI:
  1. System prompt constraints.
  2. AST token analysis using `sqlparse` to block DDL/DML mutations (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `EXEC`, `PRAGMA`).
  3. Semicolon and multi-statement blocking to prevent stacked query injection.
  4. Physical SQLite read-only URI sandbox (`file:...mode=ro`).

### D. Automated Test Case Generation
- AI assisted in synthesizing a 16-test automated test suite covering all 5 core benchmark questions, data imputation verification, returned transaction exclusions, SQL injection attempts, out-of-domain refusals, and system health endpoints.

---

## 3. Which Problems You Encountered

During development, we encountered six significant technical challenges:

1. **Corrupted Byte Sequence in Transaction `TXN0051`:**
   - The raw CSV contained a non-standard byte sequence in the `Unit_price` column of row 50 (`TXN0051`). Standard loading routines failed or resulted in `NaN` propagation that corrupted downstream revenue sums.
2. **SQLite Date Incompatibility with `DD-MM-YYYY` Format:**
   - Sales transactions were timestamped in `DD-MM-YYYY` format (e.g., `03-01-2026`). In SQLite, text strings in this format cannot be sorted chronologically or grouped using native `strftime` functions.
3. **Ambiguity Between Gross Revenue, Net Revenue, and Returned Items:**
   - Transaction `TXN0033` had a status of `Returned` (Monitor, 2 units, $19,000.00). If included in total revenue, it artificially inflates net realized revenue from $1,445,200.00 to $1,464,200.00. Furthermore, four transactions had non-zero discount values.
4. **Google AI Studio Key Scoping & Legacy Model 404s:**
   - Newly generated Google AI Studio keys return `404 NOT_FOUND` when requesting legacy `gemini-1.5-flash` endpoints, because new developer project keys are scoped to Gemini 2.x models (`gemini-2.5-flash`, `gemini-flash-latest`, `gemini-2.5-pro`).
5. **Google AI Studio Free Tier Quota Limits (5 RPM):**
   - The Free Tier enforces a strict quota of 5 requests per minute. Firing consecutive Text-to-SQL + synthesis queries in rapid succession quickly triggered `HTTP 429 Too Many Requests`.
6. **AST Security Rejection on Administrative Schema Inspection (`/api/health`):**
   - The `/api/health` endpoint executed `PRAGMA table_info(sales)` to display table schema in the Data Health modal. Because it was routed through `execute_safe_query()`, the AST validator blocked it as an unsupported PRAGMA keyword, resulting in an HTTP 500 error.

---

## 4. How You Debugged Them

Each issue was resolved using structured debugging methodologies:

### Debugging `TXN0051` Data Anomaly
- **Investigation:** Ran a forensic pandas script:
  ```python
  df[df['unit_price'].isna()]
  ```
  Identified that row 50 was a `Laptop Stand` with `Quantity = 5`.
- **Validation:** Analyzed all other `Laptop Stand` records:
  ```python
  df[df['Product'] == 'Laptop Stand']['Unit_price'].unique()
  ```
  Found that every valid `Laptop Stand` transaction in the dataset has a strictly uniform price of `$1,200.00`.
- **Resolution:** Implemented an automated modal catalog imputation in `backend/etl.py` that infers missing unit prices from intact records of the same product and logs an audit record, preventing the loss of $6,000 in legitimate sales.

### Debugging Date Grouping for Time-Series Queries
- **Investigation:** Attempting `GROUP BY strftime('%Y-%m', order_date)` on `DD-MM-YYYY` failed because `strftime` expects ISO-8601 strings.
- **Resolution:** In the ETL pipeline, converted dates using `pd.to_datetime(df['order_date'], format='%d-%m-%Y')` into standard ISO-8601 `YYYY-MM-DD` strings, and generated a dedicated indexed column `order_month` (`YYYY-MM`). This enabled instant sub-millisecond monthly aggregations.

### Clarifying Financial Rigor & Returns
- **Resolution:** Defined explicit formulas in `backend/models.py` and `backend/etl.py`:
  - $\text{Gross Revenue} = \text{Quantity} \times \text{Unit\_price}$
  - $\text{Net Revenue} = (\text{Quantity} \times \text{Unit\_price}) - \text{Discount\_amount}$
  - Added explicit filter `WHERE status = 'Completed'` to exclude returned transactions from realized revenue, while preserving them in the database for return-rate analysis.

### Resolving Gemini Model Scoping & 404 Errors
- **Investigation:** Queried the Google GenAI `ModelService.ListModels` endpoint using curl and python requests:
  ```python
  requests.get(f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}')
  ```
  Observed that `models/gemini-2.5-flash` returned HTTP 200 while `models/gemini-1.5-flash` returned HTTP 404.
- **Resolution:** Updated default model to **`gemini-2.5-flash`** across `.env`, backend models, and frontend UI selectors.

### Handling Free Tier Rate Limits (5 RPM) with Zero Downtime
- **Investigation:** Automated test runs making 2 LLM calls per query exceeded 5 RPM, producing HTTP 429 exceptions.
- **Resolution:** Architected a **Zero-Downtime Deterministic Fallback Engine**. When an HTTP 429 exception occurs, the system seamlessly routes the query to the deterministic engine, returning the 100% accurate ground truth result in < 2ms, with a clear status badge notifying the evaluator: `⚡ RATE LIMITED (ZERO-DOWNTIME FALLBACK)`.

### Resolving `/api/health` PRAGMA AST Rejection
- **Investigation:** Inspecting backend server logs revealed `SecurityValidationError: Destructive keyword 'PRAGMA' is strictly forbidden by security policy`.
- **Resolution:** Decoupled internal administrative metadata operations from the user-facing AST validator. In `/api/health`, connected directly to SQLite using a native read-only URI connection (`file:...mode=ro`), allowing schema introspection without compromising query security.

---

## 5. What You Would Improve With Another Day of Work

With an additional 24 hours of engineering effort, I would implement the following enterprise-grade enhancements:

1. **Semantic Schema Layer with Vector Indexing (Two-Stage RAG):**
   - For scaling to enterprise databases with hundreds of tables, implement a two-stage retrieval pipeline: index table descriptions and schema embeddings in ChromaDB/pgvector, retrieve only the top 3 relevant table schemas for any user query, and pass only those to the Text-to-SQL engine.
2. **LangGraph StateGraph Multi-Agent Architecture:**
   - Refactor the single agent into a collaborative multi-agent system:
     - **Planner Agent:** Breaks complex queries into multi-table sub-tasks.
     - **SQL Generator Agent:** Writes the candidate query.
     - **Syntax & Safety Critic Agent:** Validates AST and tests execution in an isolated sandbox.
     - **BI Visualizer Agent:** Decides the optimal visualization chart type (scatter, heatmap, multi-bar) based on data dimensionality.
3. **AWS Cloud-Native Deployment Pipeline:**
   - Containerize the application using Docker.
   - Deploy backend to **AWS ECS Fargate** or **AWS Lambda** behind an **Amazon API Gateway**.
   - Migrate storage from SQLite to **Amazon RDS Aurora PostgreSQL** or **Amazon Athena on S3**.
   - Use **Amazon Bedrock** (Claude 3.5 Sonnet) within a private AWS VPC to ensure complete enterprise data privacy.
4. **Natural Language Query Autocomplete & Fuzzy Synonym Matching:**
   - Integrate fuzzy matching (Levenshtein distance) and vector synonym mapping so terms like *"telly"* or *"display"* automatically map to *"Monitor"*, and *"Norfolk"* maps to *"North"*.
5. **Interactive Dashboard Export (PDF/CSV):**
   - Add export buttons to download generated BI reports as formatted PDF executive briefs or CSV datasets.
