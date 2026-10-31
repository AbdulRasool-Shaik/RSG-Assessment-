"""
FastAPI Application Entrypoint
Serves REST API endpoints for the Mini AI Business Intelligence Assistant
and hosts the interactive web UI.
"""

import os
import requests
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
load_dotenv(override=True)

from .etl import run_etl, DB_PATH, get_audit_log, RAW_CSV_PATH
from .models import QueryRequest, QueryResponse, DataHealthResponse, AuditItem
from .llm_agent import AgenticQueryCoordinator
from .security import SecurityValidationError, execute_safe_query

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database exists and is cleaned/indexed upon server start."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Running ETL pipeline...")
        run_etl()
    print("Mini AI BI Assistant backend started successfully.")
    yield

app = FastAPI(
    title="Mini AI Business Intelligence Assistant",
    description="Vectorless RAG & Agentic Text-to-SQL Assistant for Sales Intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Coordinator
coordinator = AgenticQueryCoordinator(DB_PATH)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.post("/api/query", response_model=QueryResponse, summary="Submit natural language sales question")
def handle_query(payload: QueryRequest):
    """
    Processes a natural language business question, validates SQL security,
    executes against SQLite, and returns a structured BI response.
    Supports real-time Google Gemini via dynamic api_key or fallback.
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )
    
    try:
        active_model = payload.model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        response = coordinator.execute(
            query=payload.query.strip(),
            api_key=payload.api_key,
            model_name=active_model,
            prefer_llm=payload.use_llm
        )
        return response
    except SecurityValidationError as sec_err:
        return QueryResponse(
            query=payload.query,
            status="error",
            answer=f"**Security Guardrail Triggered:** {str(sec_err)}",
            engine_used="security_validator",
            error_message=str(sec_err)
        )
    except Exception as e:
        return QueryResponse(
            query=payload.query,
            status="error",
            answer=f"**Error processing query:** {str(e)}",
            engine_used="error_handler",
            error_message=str(e)
        )

@app.post("/api/verify-key", summary="Validate a Google AI Studio Gemini API Key")
def verify_api_key(payload: Dict[str, str]):
    """Verifies that a supplied Google AI Studio key is functional."""
    key = payload.get("api_key", "").strip()
    if not key:
        return {"valid": False, "message": "API key cannot be empty."}
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            models_data = res.json().get("models", [])
            model_names = [m.get("name", "") for m in models_data]
            active_m = "gemini-2.5-flash" if any("gemini-2.5-flash" in n for n in model_names) else "gemini-flash-latest"
            return {"valid": True, "model": active_m, "message": f"Google AI Studio Key connected successfully ({active_m})!"}
        return {"valid": False, "message": f"Google AI Studio rejected key (HTTP {res.status_code})."}
    except Exception as e:
        return {"valid": False, "message": f"Connection error: {str(e)}"}

@app.get("/api/config", summary="Get backend AI configuration status")
def get_config():
    """Returns backend configuration including whether GEMINI_API_KEY is active in .env."""
    load_dotenv(override=True)
    has_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    return {
        "backend_has_key": has_key,
        "default_model": model,
        "status": "ready"
    }

@app.get("/api/health", response_model=DataHealthResponse, summary="Get database health and ETL audit log")
def get_health():
    """Returns database connection status, schema information, and data cleaning audit logs."""
    try:
        cols, rows, _ = execute_safe_query(DB_PATH, "SELECT COUNT(*) as count FROM sales")
        total = rows[0]["count"] if rows else 0
        
        cols_info, schema_rows, _ = execute_safe_query(DB_PATH, "PRAGMA table_info(sales)")
        schema_list = [{"name": r["name"], "type": r["type"]} for r in schema_rows] if schema_rows else []
        
        audit_items = [AuditItem(**item) for item in get_audit_log()]
        
        return DataHealthResponse(
            total_records=total,
            table_name="sales",
            database_file=os.path.basename(DB_PATH),
            columns=schema_list,
            audit_log=audit_items,
            status="healthy"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database health check failed: {e}")

@app.get("/api/sample-questions", summary="Get the 5 core benchmark questions")
def get_sample_questions():
    """Returns recommended questions aligned with the challenge specification."""
    return {
        "benchmark_questions": [
            {
                "id": 1,
                "question": "What is the total revenue?",
                "category": "High-Level Financials",
                "description": "Calculates net completed revenue, gross invoiced revenue, and discount sums."
            },
            {
                "id": 2,
                "question": "Which product generated the highest revenue?",
                "category": "Product Analytics",
                "description": "Ranks products by total net revenue and units sold."
            },
            {
                "id": 3,
                "question": "What is the monthly revenue trend?",
                "category": "Time Series",
                "description": "Chronological monthly net revenue trajectory (Jan–Jun 2026)."
            },
            {
                "id": 4,
                "question": "Which region generated the highest sales?",
                "category": "Geographic Performance",
                "description": "Regional revenue breakdown across North, South, East, and West."
            },
            {
                "id": 5,
                "question": "How did revenue change between two months?",
                "category": "Comparative Analysis",
                "description": "Compares April vs. May 2026 revenue with absolute variance and percentage delta."
            }
        ]
    }

# Mount frontend static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "Frontend UI file not found. REST API is active."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
