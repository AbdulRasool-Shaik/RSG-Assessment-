# Technical Interview Preparation Guide
## Mini AI Business Intelligence Assistant — Interview Playbook

**Candidate Role:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  
**Reporting To:** Jeevan Kumar, RSG  
**Key Focus Areas:** Agentic AI, Generative AI, Vectorless RAG, LangChain, Google ADK, Dify, Safe Text-to-SQL, SQLite, Security Guardrails

---

## Table of Contents
1. [The 60-Second Elevator Pitch](#1-the-60-second-elevator-pitch)
2. [The 3-Minute Architectural Deep-Dive](#2-the-3-minute-architectural-deep-dive)
3. [Core Concepts Breakdown (The "Must-Knows")](#3-core-concepts-breakdown)
   - [Agentic AI vs. Standard Generative AI](#agentic-ai-vs-standard-generative-ai)
   - [Vectorless RAG vs. Vector RAG](#vectorless-rag-vs-vector-rag)
   - [Agentic Frameworks: LangChain, Google ADK, Dify](#agentic-frameworks-langchain-google-adk-dify)
4. [25+ Technical Interview Questions & High-Scoring Answers](#4-25-technical-interview-questions--high-scoring-answers)
   - [Category A: Agentic AI & LLM Systems](#category-a-agentic-ai--llm-systems)
   - [Category B: Data Engineering & SQL Architecture](#category-b-data-engineering--sql-architecture)
   - [Category C: Security, Guardrails & Safe Text-to-SQL](#category-c-security-guardrails--safe-text-to-sql)
   - [Category D: Production Scalability & AWS Cloud Deployment](#category-d-production-scalability--aws-cloud-deployment)
   - [Category E: Testing, Edge Cases & Data Quality](#category-e-testing-edge-cases--data-quality)
5. [Live Demonstration Script (Step-by-Step)](#5-live-demonstration-script)

---

## 1. The 60-Second Elevator Pitch

> *"For this challenge, I designed and built a **Mini AI Business Intelligence Assistant** that allows business users to ask natural language questions about sales data and receive deterministic, verified answers backed by database queries.*
>
> *Rather than building a basic LLM chatbot that hallucinates numbers, I implemented a **Vectorless RAG architecture**. The system converts natural language into validated SQLite queries using schema grounding. To ensure security, every query passes through a **four-tier defense-in-depth model**, including **AST token parsing with `sqlparse`**, blocking any destructive operations, and executing in a **read-only database URI sandbox**.*
>
> *I also designed an automated **ETL pipeline** that cleans edge cases like corrupted unit prices via catalog imputation and standardizes dates to ISO-8601. The solution features a high-performance **FastAPI backend**, an interactive UI with dynamic **Chart.js visualizations and an SQL Inspector**, and a **100% passing automated test suite** with 12 comprehensive unit and integration tests."*

---

## 2. The 3-Minute Architectural Deep-Dive

When the interviewer asks: *"Can you walk me through the architecture of your application?"*, follow this structured narrative:

1. **Layer 1 — Data Ingestion & Forensic ETL (`backend/etl.py`):**
   - *"Before querying, data quality is paramount. During dataset profiling, I found that row 50 (`TXN0051`) contained corrupted non-numeric bytes for `Unit_price`. Rather than deleting the row, which would omit $6,000 of Laptop Stand sales, my ETL pipeline analyzed price consistency across the catalog, found that Laptop Stands are strictly $1,200.00, and cleanly imputed the value with a logged audit trail. I also normalized `DD-MM-YYYY` dates into ISO-8601 `YYYY-MM-DD` so SQLite's native `strftime` functions work efficiently."*

2. **Layer 2 — Dual-Mode Query Coordinator (`backend/llm_agent.py` & `backend/deterministic_engine.py`):**
   - *"The system features a dual-engine design. In **Agentic LLM Mode**, it sends the schema and user intent to an LLM using few-shot prompt grounding. It features an **autonomous reflection loop**: if an SQL query throws an error, the agent intercepts the exception and asks the LLM to self-correct (up to 2 retries). In **Deterministic Mode**, it serves all 5 core questions and date variations offline with zero API key dependencies, guaranteeing that evaluators can clone and test the repo with zero setup friction."*

3. **Layer 3 — AST Security Sandbox (`backend/security.py`):**
   - *"Security was a primary requirement. We enforce a four-tier defense:
     1. System prompt grounding.
     2. AST token inspection via `sqlparse` ensuring root statement is strictly `SELECT` or `WITH`.
     3. Mutation blocking against `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, and semicolon-chained queries.
     4. Physical engine isolation: the SQLite connection is opened with `mode=ro` (read-only URI).*

4. **Layer 4 & 5 — Presentation & Verification (`frontend/`):**
   - *"The user receives a structured answer with key metrics cards, an interactive Chart.js visualization, a tabular view of supporting database rows, and a collapsible **SQL Inspector** so business stakeholders can audit the exact query that produced the numbers."*

---

## 3. Core Concepts Breakdown

### Agentic AI vs. Standard Generative AI
- **Standard Generative AI:** Single-shot prompt-and-response. The model generates text sequentially without interacting with external tools, verifying its reasoning, or validating facts. It is prone to hallucination when asked to calculate sums or aggregations.
- **Agentic AI:** An autonomous system governed by cognitive patterns:
  1. **Tool Use:** The LLM delegates arithmetic and data retrieval to specialized external tools (e.g., SQLite engine) rather than calculating numbers internally.
  2. **Reflection & Self-Correction:** The agent inspects its own output, validates syntax, and adjusts its strategy when an error occurs.
  3. **Planning:** Decomposing multi-step business questions (e.g., *"How did revenue change between April and May?"*) into discrete analytical sub-tasks.
  4. **Guardrails:** Intercepting adversarial, destructive, or out-of-domain requests before execution.

### Vectorless RAG vs. Vector RAG
- **Vector RAG (Embeddings + Vector Stores like Pinecone/Chroma):**
  - Chunks text and matches queries using vector cosine similarity.
  - **Fatal Flaw for BI:** Vector similarity cannot perform aggregations (`SUM`, `AVG`, `MAX`, `GROUP BY`), date filtering, or percentage growth calculations. It leads to hallucinations and incorrect figures.
- **Vectorless RAG (Structured RAG / Text-to-SQL / Graph RAG):**
  - Keeps tabular data in relational or columnar databases.
  - Uses the LLM to understand intent and generate structured database queries (`SELECT ...`) grounded in the schema.
  - The database computes exact numbers. Result: **100% mathematical accuracy, zero arithmetic hallucination, and full query auditability.**

### Agentic Frameworks: LangChain, Google ADK, Dify
- **LangChain / LangGraph:** Industry-standard Python framework for chaining tools, managing memory, and building cyclic multi-agent state machines (`StateGraph`).
- **Google ADK (Agent Development Kit):** Tailored for Gemini models, offering optimized function-calling mechanisms, schema integration, and structured output parsing.
- **Dify:** An open-source LLM application development platform featuring a visual workflow canvas for building RAG pipelines and agentic tool orchestrations.
- **Why our implementation shines:** We implemented the core agentic patterns (reflection loop, tool use, AST validation) directly in clean, maintainable Python while structuring the coordinator so LangChain or Google ADK can be swapped in with one line of code.

---

## 4. 25+ Technical Interview Questions & High-Scoring Answers

### Category A: Agentic AI & LLM Systems

#### Q1: Why did you use Text-to-SQL instead of feeding the CSV into the LLM context window?
**Answer:**
> *"Feeding raw CSV data into an LLM context window has three fatal limitations:
> 1. **Token Cost & Context Limits:** As datasets grow from 50 rows to 500,000 rows, context windows overflow and API latency/cost skyrockets.
> 2. **Loss of Determinism:** LLMs are probabilistic token predictors, not calculators. They frequently make arithmetic errors when summing dozens of floating-point numbers.
> 3. **Scalability:** With Vectorless RAG (Text-to-SQL), we pass only a lightweight schema (~300 tokens) to the model. The database performs the heavy aggregation in milliseconds with 100% deterministic precision."*

#### Q2: How does your agent implement self-correction (reflection)?
**Answer:**
> *"In `backend/llm_agent.py`, the `_run_llm_agent_loop` wraps query generation in a reflection loop. When the model generates an SQL query, it is immediately tested against `validate_sql_query()` and executed in a sandbox. If an exception occurs (e.g., syntax error or unknown column), the exception string is captured and injected back into the LLM prompt: `'Previous query failed with error: {err}. Please self-correct and output a valid SQLite query.'` The model re-reasons and fixes the query, achieving autonomous error recovery."*

#### Q3: How do you prevent the LLM from hallucinating column names or tables that don't exist?
**Answer:**
> *"We ground the LLM using a strict system prompt containing the exact table name (`sales`) and all 13 column types and descriptions. Furthermore, in our AST security layer, queries referencing any table other than `sales` are rejected before execution."*

---

### Category B: Data Engineering & SQL Architecture

#### Q4: How did you handle data anomalies in the provided CSV file?
**Answer:**
> *"During our exploratory forensic profiling, we identified three anomalies:
> 1. **`TXN0051`:** The `Unit_price` contained non-numeric corrupted characters (`NaN`). Rather than dropping the row (which would cause a $6,000 revenue omission), we analyzed the entire dataset and proved that `Laptop Stand` has a strictly constant unit price of $1,200.00 across all other records. We imputed $1,200.00 and logged an audit entry.
> 2. **`TXN0033`:** Had `Status = 'Returned'`. In business intelligence, returns must be excluded from realized revenue calculations. We preserved the row for transactional completeness but added `status = 'Completed'` filters to revenue queries.
> 3. **`TXN0034`:** Had `Quantity = 0`. Yields $0 revenue; preserved for transactional logging.
> 4. **Date Formatting:** Normalized `DD-MM-YYYY` to ISO-8601 `YYYY-MM-DD` so SQLite's `strftime` functions work correctly."*

#### Q5: What is the exact difference between Gross Revenue and Net Revenue in this dataset?
**Answer:**
> *"Gross Revenue is `Quantity * Unit_price`. Net Revenue is `(Quantity * Unit_price) - Discount_amount`. Only four transactions in this dataset had discounts (ranging from $500 to $2,500), totaling $4,500.00 in promotional discounts. For completed orders, Gross Revenue is **$1,449,700.00** and Net Revenue is **$1,445,200.00**."*

#### Q6: Why did you create indexes on `order_date`, `order_month`, `product`, and `region`?
**Answer:**
> *"SQLite performs full table scans ($O(N)$) unless indexed. Since the 5 core analytical questions group and filter by month, product, region, and status, creating B-tree indexes reduces lookup and grouping complexity to $O(\log N)$, ensuring sub-millisecond query execution."*

---

### Category C: Security, Guardrails & Safe Text-to-SQL

#### Q7: How do you prevent SQL injection attacks through natural language prompts?
**Answer:**
> *"We implement a four-tier defense-in-depth model:
> 1. **System Prompt Constraint:** Instructs the LLM to output only single `SELECT` statements.
> 2. **AST Tokenizer (`sqlparse`):** Parses the query into grammatical syntax tokens, verifying that the root statement type is strictly `SELECT` or `WITH`.
> 3. **Keyword Blacklisting & Comment Strip:** Tokens like `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`, and SQL comment syntax (`--`, `/*`) are blocked.
> 4. **Physical Read-Only Sandbox:** The database connection is opened with `file:sales_bi.db?mode=ro`. Even if an attacker bypassed the AST parser, SQLite's core engine physically blocks write operations at the OS/filesystem level."*

#### Q8: Can someone bypass your security with semicolon query chaining (e.g., `SELECT 1; DROP TABLE sales;`)?
**Answer:**
> *"No. Our AST validator explicitly checks for semicolons and asserts that `len(parsed) == 1`. Any query containing multiple statements is rejected with `SecurityValidationError: Multiple SQL statements or semicolon-chained queries are strictly prohibited.`"*

#### Q9: How do you handle out-of-domain or adversarial user questions (e.g., 'What is the capital of France?')?
**Answer:**
> *"The query router inspects user intent against the sales intelligence domain. If the question cannot be mapped to the sales schema, the system returns a polite refusal with `status='refused'`, listing the 5 supported analytical domains without invoking unnecessary SQL or LLM calls."*

---

### Category D: Production Scalability & AWS Cloud Deployment

#### Q10: The Job Description mentions AWS services like Lambda, S3, SageMaker, and Lex. How would you deploy this application on AWS?
**Answer:**
> *"Here is my cloud-native AWS architecture:
> 1. **Storage (Amazon S3 & Athena / RDS Aurora):** Raw transaction CSVs are uploaded to an Amazon S3 bucket. An S3 Event Notification triggers an AWS Lambda ETL function that cleans the data and writes it to Amazon RDS PostgreSQL (or Aurora Serverless).
> 2. **Compute (AWS Lambda / ECS Fargate):** The FastAPI backend can be containerized with Docker and deployed on AWS ECS Fargate or AWS Lambda (via Mangum ASGI adapter) for auto-scaling serverless execution.
> 3. **AI/LLM Layer (Amazon Bedrock / SageMaker):** For enterprise data privacy, we use **Amazon Bedrock** (Anthropic Claude 3.5 Sonnet or Amazon Titan) to generate SQL queries via private VPC endpoints, avoiding public internet routing.
> 4. **Conversational Front-End (Amazon Lex):** Can integrate Amazon Lex to provide voice and chatbot interfaces for mobile business executives."*

#### Q11: How would you scale this to handle millions of transactions across hundreds of tables?
**Answer:**
> *"For enterprise scale:
> 1. **Columnar Data Warehouse:** Migrate from SQLite to **ClickHouse**, **Snowflake**, or **AWS Redshift**, which are optimized for OLAP aggregations.
> 2. **Semantic Schema Layer:** Instead of passing the entire raw database schema to the LLM, use a semantic layer (like Cube.js or dbt Semantic Layer) where pre-defined metrics and dimensions are cataloged.
> 3. **Vector-Indexed Schema Retrieval (Two-Stage RAG):** For a database with 500 tables, use a vector index on table and column metadata to retrieve only the top 3 relevant table schemas into the LLM prompt.
> 4. **Query Result Caching:** Implement a Redis cache for frequently asked questions (e.g., monthly trends), caching the result for 1 hour to reduce database load."*

---

### Category E: Testing, Edge Cases & Data Quality

#### Q12: How did you test your application?
**Answer:**
> *"I built an automated test suite using `pytest` and FastAPI's `TestClient` located in `tests/test_assistant.py`. It contains 12 automated test cases covering:
> 1. **All 5 Core Questions:** Verifying that total revenue ($1,445,200.00), top product (Monitor), monthly trend (peak May), top region (South), and month-over-month growth (+32.32%) match mathematical ground truth.
> 2. **Edge Cases:** Verifying that `TXN0051` price imputation works and that returned order `TXN0033` ($19,000) is excluded from completed revenue.
> 3. **Security Injections:** Verifying that `DROP TABLE`, `UPDATE`, and semicolon chaining are blocked with `SecurityValidationError`.
> 4. **Out-of-Domain Scoping:** Verifying that unrelated queries are gracefully refused."*

---

## 5. Live Demonstration Script

Follow this step-by-step walkthrough when presenting your screen during the interview:

1. **Step 1: Start the Server:**
   ```bash
   python backend/app.py
   ```
   *Point out:* *"Notice how on startup, the ETL pipeline automatically checks database integrity and loads 51 rows."*

2. **Step 2: Show the Data Health Modal:**
   - Click the **Data Health** button in the top right.
   - *Explain:* *"Here is our forensic audit log. Notice row `TXN0051` where unit price was missing; our ETL identified that Laptop Stands have a constant price of $1,200.00 and imputed it with full transparency."*

3. **Step 3: Test Benchmark Question 1 (Total Revenue):**
   - Click the **Total Revenue** chip.
   - *Explain:* *"Notice the structured output: Net Realized Revenue is $1,445,200.00, Gross is $1,449,700.00, and $4,500.00 in discounts. Below, the SQL Inspector displays the exact SQL query executed in our read-only sandbox in under 2 milliseconds."*

4. **Step 4: Test Benchmark Question 3 (Monthly Trend):**
   - Click the **Monthly Trend** chip.
   - *Explain:* *"Here, the assistant detects a time-series intent, aggregates revenue chronologically by month using our ISO-8601 indexed `order_month` column, and renders an interactive line chart showing the growth up to the peak in May 2026."*

5. **Step 5: Test Benchmark Question 4 (Regional Sales):**
   - Click the **Top Region** chip.
   - *Explain:* *"South is identified as #1 in both revenue ($411,200.00) and volume (182 units), with an interactive doughnut chart showing geographic market share."*

6. **Step 6: Demonstrate Security Guardrail:**
   - Type in the input box: `What is total revenue? DROP TABLE sales;`
   - *Explain:* *"Watch how the AST security engine immediately intercepts the malicious semicolon chaining and forbidden `DROP` token, blocks the query, and protects database integrity."*

7. **Step 7: Run Automated Tests:**
   - Open terminal and run:
     ```bash
     python -m pytest tests/test_assistant.py -v
     ```
   - *Explain:* *"All 12 test cases pass in 1.4 seconds, validating mathematical accuracy, edge cases, and security policies."*
