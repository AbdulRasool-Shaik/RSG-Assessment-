# Technical Interview Preparation Playbook
## Comprehensive Candidate Defense Guide — Mini AI Business Intelligence Assistant

**Candidate Name:** Tharun Parsa  
**Target Role:** Graduate Engineer Trainee (Python with Generative AI Engineer) — RSG  
**Reporting Manager / Evaluator:** Jeevan Kumar, RSG, Hyderabad  
**Core Technologies:** Agentic AI, Generative AI, Vectorless RAG, LangChain/LangGraph, Google ADK, Dify, Safe Text-to-SQL, SQLite Sandboxing, AST Guardrails, FastAPI, AWS Cloud  

---

## Table of Contents
1. [The 60-Second Elevator Pitch](#1-the-60-second-elevator-pitch)
2. [The 3-Minute Architectural Deep-Dive](#2-the-3-minute-architectural-deep-dive)
3. [25 Comprehensive Technical Interview Questions & High-Scoring Answers](#3-25-comprehensive-technical-interview-questions--high-scoring-answers)
   - [Category A: Agentic AI & LLM Systems (Q1 – Q6)](#category-a-agentic-ai--llm-systems)
   - [Category B: Data Engineering & SQL Architecture (Q7 – Q11)](#category-b-data-engineering--sql-architecture)
   - [Category C: Security, Guardrails & Safe Text-to-SQL (Q12 – Q16)](#category-c-security-guardrails--safe-text-to-sql)
   - [Category D: Production Scalability & AWS Cloud Deployment (Q17 – Q21)](#category-d-production-scalability--aws-cloud-deployment)
   - [Category E: Testing, Edge Cases & Data Quality (Q22 – Q25)](#category-e-testing-edge-cases--data-quality)
4. [Live Demonstration Script (Step-by-Step)](#4-live-demonstration-script)

---

## 1. The 60-Second Elevator Pitch

> *"For this challenge, I designed and built a **Mini AI Business Intelligence Assistant** that allows business users to ask natural language questions about sales data and receive deterministic, verified answers backed by database queries.
>
> Rather than building a basic LLM chatbot that hallucinates numbers over raw text, I implemented a **Vectorless RAG architecture**. The system converts natural language into validated SQLite queries using schema grounding. To ensure security, every query passes through a **four-tier defense-in-depth model**, including **AST token parsing with `sqlparse`**, blocking any destructive operations, and executing in a **read-only database URI sandbox**.
>
> I also designed an automated **ETL pipeline** that cleans edge cases like corrupted unit prices via catalog imputation and standardizes dates to ISO-8601. The solution features a high-performance **FastAPI backend**, an interactive UI with dynamic **Chart.js visualizations and an SQL Inspector**, and a **100% passing automated test suite** with 16 comprehensive unit and integration tests."*

---

## 2. The 3-Minute Architectural Deep-Dive

When the interviewer asks: *"Can you walk me through the architecture of your application?"*, follow this structured narrative:

1. **Layer 1 — Data Ingestion & Forensic ETL (`backend/etl.py`):**
   - *"Before querying, data quality is paramount. During dataset profiling, I found that row 50 (`TXN0051`) contained corrupted non-numeric bytes for `Unit_price`. Rather than deleting the row, which would omit $6,000 of Laptop Stand sales, my ETL pipeline analyzed price consistency across the catalog, found that Laptop Stands are strictly $1,200.00, and cleanly imputed the value with a logged audit trail. I also normalized `DD-MM-YYYY` dates into ISO-8601 `YYYY-MM-DD` so SQLite's native `strftime` functions work efficiently."*

2. **Layer 2 — Dual-Mode Query Coordinator (`backend/llm_agent.py` & `backend/deterministic_engine.py`):**
   - *"The system features a dual-engine design. In **Agentic LLM Mode**, it sends the schema and user intent to Google Gemini (`gemini-2.5-flash`) using few-shot prompt grounding. It features an **autonomous reflection loop**: if an SQL query throws an error, the agent intercepts the exception and asks the LLM to self-correct (up to 2 retries). In **Deterministic Mode**, it serves all 5 core questions and date variations offline with zero API key dependencies, guaranteeing that evaluators can clone and test the repo with zero setup friction."*

3. **Layer 3 — AST Security Sandbox (`backend/security.py`):**
   - *"Security was a primary requirement. We enforce a four-tier defense:
     1. System prompt grounding.
     2. AST token inspection via `sqlparse` ensuring root statement is strictly `SELECT` or `WITH`.
     3. Mutation blocking against `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`, `PRAGMA` and semicolon-chained queries.
     4. Physical engine isolation: the SQLite connection is opened with `mode=ro` (read-only URI)."*

4. **Layer 4 & 5 — Presentation & Verification (`frontend/`):**
   - *"The user receives a structured answer with key metrics cards, an interactive Chart.js visualization, a tabular view of supporting database rows, and a collapsible **SQL Inspector** so business stakeholders can audit the exact query that produced the numbers."*

---

## 3. 25 Comprehensive Technical Interview Questions & High-Scoring Answers

### Category A: Agentic AI & LLM Systems

#### Q1: Why did you use Text-to-SQL instead of feeding the CSV into the LLM context window?
**Answer:**
> *"Feeding raw CSV data into an LLM context window has three fatal limitations:
> 1. **Token Cost & Context Limits:** As datasets grow from 50 rows to 500,000 rows, context windows overflow and API latency/cost skyrockets.
> 2. **Loss of Determinism:** LLMs are probabilistic token predictors, not calculators. They frequently make arithmetic errors when summing dozens of floating-point numbers.
> 3. **Scalability:** With Vectorless RAG (Text-to-SQL), we pass only a lightweight schema (~300 tokens) to the model. The database performs the heavy aggregation in milliseconds with 100% deterministic precision."*

#### Q2: How does your agent implement self-correction (reflection)?
**Answer:**
> *"In `backend/llm_agent.py`, query generation is wrapped in an autonomous reflection loop. When the model generates an SQL query, it is immediately tested against `validate_sql_query()` and executed in a sandbox. If an exception occurs (e.g., syntax error or unknown column), the exception string is captured and injected back into the LLM prompt: `'Previous query failed with error: {err}. Please self-correct and output a valid SQLite query.'` The model re-reasons and fixes the query, achieving autonomous error recovery."*

#### Q3: How do you prevent the LLM from hallucinating column names or tables that don't exist?
**Answer:**
> *"We ground the LLM using a strict system prompt containing the exact table name (`sales`) and all 13 column types and descriptions. Furthermore, in our AST security layer, queries referencing any table other than `sales` are rejected before execution."*

#### Q4: How does your system handle Google AI Studio Free Tier rate limits (5 RPM)?
**Answer:**
> *"Google AI Studio Free Tier enforces a strict quota of 5 requests per minute. When rapid sequential queries occur, our coordinator intercepts the HTTP 429 quota exception and automatically routes the request to our Zero-Downtime Deterministic Fallback Engine. The user receives a sub-2ms accurate response with an informative UI badge: `⚡ RATE LIMITED (ZERO-DOWNTIME FALLBACK)`, ensuring high availability with zero server crashes."*

#### Q5: Why did you select `gemini-2.5-flash` instead of older models or local models?
**Answer:**
> *"`gemini-2.5-flash` provides the optimal balance of speed (< 1.5s time-to-first-token), native JSON Schema enforcement (`response_mime_type="application/json"`), and superior SQL syntax comprehension compared to older models like `gemini-1.5-flash`. Furthermore, using cloud-hosted Gemini avoids requiring evaluators to download multi-gigabyte local Ollama models on their test machines."*

#### Q6: What is the fundamental difference between an Agentic AI workflow and simple Prompt Engineering?
**Answer:**
> *"Prompt engineering is static text formatting targeting a single LLM inference call. Agentic AI is an autonomous, multi-step software system combining LLM reasoning with tool execution, state management, iterative reflection, guardrail enforcement, and deterministic fallbacks."*

---

### Category B: Data Engineering & SQL Architecture

#### Q7: How did you handle data anomalies in the provided CSV file?
**Answer:**
> *"During our exploratory forensic profiling, we identified three anomalies:
> 1. **`TXN0051`:** The `Unit_price` contained non-numeric corrupted characters (`NaN`). Rather than dropping the row (which would cause a $6,000 revenue omission), we analyzed the entire dataset and proved that `Laptop Stand` has a strictly constant unit price of $1,200.00 across all other records. We imputed $1,200.00 and logged an audit entry.
> 2. **`TXN0033`:** Had `Status = 'Returned'`. In business intelligence, returns must be excluded from realized revenue calculations. We preserved the row for transactional completeness but added `status = 'Completed'` filters to revenue queries.
> 3. **`TXN0034`:** Had `Quantity = 0`. Yields $0 revenue; preserved for transactional logging.
> 4. **Date Formatting:** Normalized `DD-MM-YYYY` to ISO-8601 `YYYY-MM-DD` so SQLite's `strftime` functions work correctly."*

#### Q8: What is the exact difference between Gross Revenue and Net Revenue in this dataset?
**Answer:**
> *"Gross Revenue is `Quantity * Unit_price`. Net Revenue is `(Quantity * Unit_price) - Discount_amount`. Only four transactions in this dataset had discounts (ranging from $500 to $2,500), totaling $4,500.00 in promotional discounts. For completed orders, Gross Revenue is **$1,449,700.00** and Net Revenue is **$1,445,200.00**."*

#### Q9: Why did you create indexes on `order_date`, `order_month`, `product`, and `region`?
**Answer:**
> *"SQLite performs full table scans ($O(N)$) unless indexed. Since the 5 core analytical questions group and filter by month, product, region, and status, creating B-tree indexes reduces lookup and grouping complexity to $O(\log N)$, ensuring sub-millisecond query execution."*

#### Q10: Why did you choose SQLite over PostgreSQL or MySQL for this challenge?
**Answer:**
> *"SQLite is an embedded, zero-configuration database included in Python's standard library. It requires no Docker containers, passwords, or port bindings, giving evaluators a frictionless 60-second setup experience. Crucially, SQLite supports a read-only URI sandbox (`file:...mode=ro`) which physically guarantees OS-level file protection."*

#### Q11: How does your ETL pipeline ensure idempotency?
**Answer:**
> *"During server startup, the ETL engine checks if `sales_bi.db` exists. If so, it verifies row count and checksum integrity. If re-running, it uses atomic table replacement (`CREATE TABLE sales_stage; ...; ALTER TABLE ... RENAME`) so that failed runs never leave the database in a corrupted partial state."*

---

### Category C: Security, Guardrails & Safe Text-to-SQL

#### Q12: How do you prevent SQL injection attacks through natural language prompts?
**Answer:**
> *"We implement a four-tier defense-in-depth model:
> 1. **System Prompt Constraint:** Instructs the LLM to output only single `SELECT` statements.
> 2. **AST Tokenizer (`sqlparse`):** Parses the query into grammatical syntax tokens, verifying that the root statement type is strictly `SELECT` or `WITH`.
> 3. **Keyword Blacklisting & Comment Strip:** Tokens like `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`, `PRAGMA` are permanently blocked.
> 4. **Physical Read-Only Sandbox:** The database connection is opened with `file:sales_bi.db?mode=ro`. Even if an attacker bypassed the AST parser, SQLite's core engine physically blocks write operations at the OS/filesystem level."*

#### Q13: Why is AST token parsing superior to regex keyword matching?
**Answer:**
> *"Regular expressions are brittle and easily bypassed by attackers using SQL comments (`/**/DROP/**/`), newline characters, string concatenation, or obscure unicode encodings. AST parsers like `sqlparse` analyze the underlying lexical grammar and syntax tree, ensuring structural immunity."*

#### Q14: Can someone bypass your security with semicolon query chaining (e.g., `SELECT 1; DROP TABLE sales;`)?
**Answer:**
> *"No. Our AST validator explicitly checks for semicolons and asserts that `len(parsed) == 1`. Any query containing multiple statements is rejected with `SecurityValidationError: Multiple SQL statements or semicolon-chained queries are strictly prohibited.`"*

#### Q15: How do you handle out-of-domain or adversarial user questions (e.g., 'What is the capital of France?')?
**Answer:**
> *"The query router inspects user intent against the sales intelligence domain. If the question cannot be mapped to the sales schema, the system returns a polite refusal with `status='refused'`, listing the supported analytical domains without invoking unnecessary SQL or LLM calls."*

#### Q16: How do you handle sensitive credentials like API keys securely?
**Answer:**
> *"We follow the 12-factor application security standard: `GEMINI_API_KEY` is loaded server-side from a gitignored `.env` file via `python-dotenv`. For evaluator convenience, the web UI allows entering a temporary session key, but the server never logs or exposes the underlying secret keys in logs or client-side bundles."*

---

### Category D: Production Scalability & AWS Cloud Deployment

#### Q17: The Job Description mentions AWS services like Lambda, S3, SageMaker, and Lex. How would you deploy this application on AWS?
**Answer:**
> *"Here is my cloud-native AWS architecture:
> 1. **Storage (Amazon S3 & Athena / RDS Aurora):** Raw transaction CSVs are uploaded to an Amazon S3 bucket. An S3 Event Notification triggers an AWS Lambda ETL function that cleans the data and writes it to Amazon RDS PostgreSQL (or Aurora Serverless).
> 2. **Compute (AWS Lambda / ECS Fargate):** The FastAPI backend can be containerized with Docker and deployed on AWS ECS Fargate or AWS Lambda (via Mangum ASGI adapter) for auto-scaling serverless execution.
> 3. **AI/LLM Layer (Amazon Bedrock / SageMaker):** For enterprise data privacy, we use **Amazon Bedrock** (Anthropic Claude 3.5 Sonnet or Amazon Titan) to generate SQL queries via private VPC endpoints, avoiding public internet routing.
> 4. **Conversational Front-End (Amazon Lex):** Can integrate Amazon Lex to provide voice and chatbot interfaces for mobile business executives."*

#### Q18: How would you scale this to handle millions of transactions across hundreds of tables?
**Answer:**
> *"For enterprise scale:
> 1. **Columnar Data Warehouse:** Migrate from SQLite to **ClickHouse**, **Snowflake**, or **AWS Redshift**, which are optimized for OLAP aggregations.
> 2. **Semantic Schema Layer:** Instead of passing the entire raw database schema to the LLM, use a semantic layer (like Cube.js or dbt Semantic Layer) where pre-defined metrics and dimensions are cataloged.
> 3. **Vector-Indexed Schema Retrieval (Two-Stage RAG):** For a database with 500 tables, use a vector index on table and column metadata to retrieve only the top 3 relevant table schemas into the LLM prompt.
> 4. **Query Result Caching:** Implement a Redis cache for frequently asked questions (e.g., monthly trends), caching the result for 1 hour to reduce database load."*

#### Q19: How do you optimize LLM token costs in high-volume production?
**Answer:**
> *"1. **Semantic Prompt Caching:** Pre-cache repetitive schema tokens using Gemini/Anthropic prompt caching.
> 2. **Small / Distilled Models for SQL:** Use lightweight 8B models (e.g., CodeLlama or Gemini Flash) for SQL generation rather than costly 70B+ frontier models.
> 3. **Redis Query Caching:** Cache identical or semantically identical queries for 1-2 hours."*

#### Q20: How would you implement observability and monitoring for this system?
**Answer:**
> *"Integrate **OpenTelemetry** with **Langfuse** or **Arize Phoenix** to trace every LLM generation step (latency, prompt tokens, completion tokens, reflection attempts). Stream FastAPI application metrics to AWS CloudWatch with alarms on 5xx error rates and AST security violation spikes."*

#### Q21: How do you build automated CI/CD evaluation for Text-to-SQL accuracy?
**Answer:**
> *"Use frameworks like **Ragas** or **DeepEval** in GitHub Actions. For every pull request, run a benchmark suite of 50 ground-truth questions, asserting both SQL AST validity and exact numeric matching against a staging database."*

---

### Category E: Testing, Edge Cases & Data Quality

#### Q22: How did you test your application?
**Answer:**
> *"I built an automated test suite using `pytest` and FastAPI's `TestClient` located in `tests/test_assistant.py`. It contains **16 automated test cases** covering:
> 1. **All 5 Core Questions:** Verifying that total revenue ($1,445,200.00), top product (Monitor), monthly trend (peak May), top region (South), and month-over-month growth (+32.32%) match mathematical ground truth.
> 2. **Edge Cases:** Verifying that `TXN0051` price imputation works and that returned order `TXN0033` ($19,000) is excluded from completed revenue.
> 3. **Security Injections:** Verifying that `DROP TABLE`, `UPDATE`, and semicolon chaining are blocked with `SecurityValidationError`.
> 4. **Out-of-Domain Scoping:** Verifying that unrelated queries are gracefully refused.
> 5. **System Endpoints:** Verifying `/api/health`, `/api/verify-key`, and `/api/config`."*

#### Q23: Why did you test with `TestClient` instead of manual API calls?
**Answer:**
> *"`TestClient` executes the complete ASGI request lifecycle in-process, catching routing errors, Pydantic serialization bugs, and middleware exceptions without relying on external network ports or background processes."*

#### Q24: What happens if an evaluator runs the application without an active internet connection?
**Answer:**
> *"The application detects the network failure or missing API key and automatically switches to the Deterministic Engine. All 5 core questions, date variations, and data health endpoints respond in under 2ms with zero errors, ensuring the evaluator experiences 100% functionality."*

#### Q25: How would you defend your engineering decisions if an interviewer challenges you?
**Answer:**
> *"I anchor my defense in empirical metrics and clear trade-off analysis:
> 1. Every decision is documented in our **10 Architectural Decision Records (ADRs)** with explicit problem statements, alternatives, and rationale.
> 2. I explain trade-offs transparently—such as choosing SQLite for evaluator zero-friction rather than PostgreSQL, and choosing Text-to-SQL for arithmetic precision over vector embeddings.
> 3. I provide immediate verifiable proof: running `pytest` to demonstrate 16 passing tests in 2 seconds."*

---

## 4. Live Demonstration Script

Refer to [LIVE_DEMO_SCRIPT.md](file:///c:/Users/THARUN%20PARSA/Downloads/rsg/interview_preparation/LIVE_DEMO_SCRIPT.md) for the complete screen-sharing script and presentation checklist.
