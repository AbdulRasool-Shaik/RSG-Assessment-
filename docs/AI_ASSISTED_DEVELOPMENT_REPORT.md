# AI-Assisted Development Report

**Candidate Name:** Tharun Parsa  
**Role:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  
**Assessment:** AI-Assisted Development Challenge: Mini AI Business Intelligence Assistant  
**Date:** October 2026  

---

## 1. Which AI Tools You Used

During the research, architecture, development, and testing phases of this project, the following AI-assisted tools and cognitive engines were utilized:

1. **Antigravity AI Agentic IDE (DeepMind Advanced Agentic Coding Engine):**
   - Used as the primary agentic pair-programming orchestrator for autonomous workspace exploration, file manipulation, and terminal execution.
2. **Claude 3.5 Sonnet / Gemini 1.5 Pro (Generative AI Models):**
   - Utilized for conceptual architecture design, AST tokenization logic, prompt engineering for Vectorless RAG, and generating synthetic security attack vectors.
3. **Python `sqlparse` Abstract Syntax Tree (AST) Analyzer:**
   - Employed as an algorithmic lexical and grammatical token parser for verifying SQL safety before execution.

---

## 2. How You Used AI During Development

AI tools were employed systematically as cognitive force-multipliers across all five phases of software development:

### A. Data Forensic Discovery & Profiling
- AI was used to execute automated pandas profiling scripts across `ai_bi_assistant_sales_data - GET.csv`.
- Prompted AI to detect distribution anomalies, verify price consistency across categories, and inspect non-numeric byte patterns in `TXN0051`.
- Formulated the modal catalog price imputation rule ($1,200.00 for Laptop Stand).

### B. Prompt Engineering & Vectorless RAG Architecture
- Designed a concise, schema-grounded system prompt embedding the SQLite data dictionary and business constraints (e.g., filtering `status = 'Completed'`).
- Integrated an **autonomous reflection loop**: structuring prompt feedback loops where database execution errors or AST validation rejections are passed back to the model for self-correction.

### C. Security Sandbox & Guardrail Implementation
- Formulated a four-tier defense-in-depth model with AI:
  1. System prompt constraints.
  2. AST token analysis using `sqlparse` to block DDL/DML mutations (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `EXEC`).
  3. Semicolon and multi-statement blocking to prevent stacked query injection.
  4. Physical SQLite read-only URI sandbox (`file:...mode=ro`).

### D. Automated Test Case Generation
- AI assisted in synthesizing a 12-test automated test suite covering all 5 core benchmark questions, data imputation verification, returned transaction exclusions, SQL injection attempts, and out-of-domain refusals.

---

## 3. Which Problems You Encountered

During development, we encountered four significant technical challenges:

1. **Corrupted Byte Sequence in Transaction `TXN0051`:**
   - The raw CSV contained a non-standard byte sequence (`\x96` resulting in `NaN`) in the `Unit_price` column of row 50 (`TXN0051`). Standard loading routines failed or resulted in `NaN` propagation that corrupted downstream revenue sums.
2. **SQLite Date Incompatibility with `DD-MM-YYYY` Format:**
   - The sales transactions were timestamped in `DD-MM-YYYY` format (e.g., `03-01-2026`). In SQLite, dates stored as plain text strings in this format cannot be sorted chronologically or grouped using SQLite's native `strftime('%Y-%m', ...)` function, because string comparison treats day `03` as less than `15` regardless of month.
3. **Ambiguity Between Gross Revenue, Net Revenue, and Returned Items:**
   - Transaction `TXN0033` had a status of `Returned` (Monitor, 2 units, $19,000.00). If included in total revenue, it artificially inflates net realized revenue from $1,445,200.00 to $1,464,200.00. Furthermore, four transactions had non-zero discount values.
4. **FastAPI Lifespan and Client Deprecations in Python 3.14:**
   - The Python runtime environment flagged legacy `@app.on_event("startup")` decorators as deprecated in modern Starlette/FastAPI.

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

### Modernizing FastAPI Lifespan Handler
- **Resolution:** Replaced `@app.on_event("startup")` with the modern `asynccontextmanager` `lifespan` handler, ensuring zero deprecation warnings and forward compatibility.

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
