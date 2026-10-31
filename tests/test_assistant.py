"""
Automated Test Suite for Mini AI Business Intelligence Assistant
Validates:
1. Core Benchmark Questions (5 cases)
2. Edge Cases (Corrupted Unit Price Imputation, Returned Orders Exclusion, Zero Quantity)
3. Security Guardrails (AST Injection Blocking, DDL/DML Prevention, Read-Only Enforcement)
4. Out-of-Domain Refusal
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.etl import run_etl, DB_PATH
from backend.security import validate_sql_query, execute_safe_query, SecurityValidationError

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database is loaded and cleaned before running tests."""
    run_etl()

# --- 1. CORE BENCHMARK TESTS (5 Questions) ---

def test_q1_total_revenue():
    """Validates Question 1: What is the total revenue?"""
    response = client.post("/api/query", json={"query": "What is the total revenue?", "use_llm": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sql_query"] is not None
    assert "SELECT" in data["sql_query"].upper()
    assert len(data["data"]) == 1
    # Verify exact ground truth net revenue: $1,445,200.00
    assert data["data"][0]["total_net_revenue"] == 1445200.00
    assert data["data"][0]["completed_orders"] == 50

def test_q2_highest_product():
    """Validates Question 2: Which product generated the highest revenue?"""
    response = client.post("/api/query", json={"query": "Which product generated the highest revenue?", "use_llm": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Monitor is #1 with $473,000.00
    top_product = data["data"][0]
    assert top_product["product"] == "Monitor"
    assert top_product["total_net_revenue"] == 473000.00

def test_q3_monthly_trend():
    """Validates Question 3: What is the monthly revenue trend?"""
    response = client.post("/api/query", json={"query": "What is the monthly revenue trend?", "use_llm": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 6  # 6 months (Jan - Jun 2026)
    
    # Peak month must be May 2026 (2026-05) with 318,500.00
    may_data = next(r for r in data["data"] if r["month"] == "2026-05")
    assert may_data["monthly_net_revenue"] == 318500.00

def test_q4_highest_region():
    """Validates Question 4: Which region generated the highest sales?"""
    response = client.post("/api/query", json={"query": "Which region generated the highest sales?", "use_llm": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # South region is #1 in both revenue ($411,200.00) and volume (182 units)
    top_region = data["data"][0]
    assert top_region["region"] == "South"
    assert top_region["net_revenue"] == 411200.00
    assert top_region["units_sold"] == 182

def test_q5_month_comparison():
    """Validates Question 5: How did revenue change between two months?"""
    response = client.post("/api/query", json={"query": "How did revenue change between April and May?", "use_llm": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 2
    # April ($240,700) to May ($318,500) -> +$77,800 (+32.32%)
    assert any("increased by $77,800.00" in data["answer"] or "+32.32%" in data["answer"] for _ in [1])

# --- 2. EDGE CASE TESTS ---

def test_edge_case_imputed_txn0051():
    """Edge Case: Verifies that corrupted Unit_price in TXN0051 was imputed cleanly to 1200.0."""
    cols, rows, _ = execute_safe_query(DB_PATH, "SELECT * FROM sales WHERE transaction_id = 'TXN0051'")
    assert len(rows) == 1
    row = rows[0]
    assert row["product"] == "Laptop Stand"
    assert row["unit_price"] == 1200.0
    assert row["net_revenue"] == 6000.0  # 5 units * 1200.0

def test_edge_case_returned_order_excluded():
    """Edge Case: Verifies that returned order TXN0033 ($19,000) is excluded from completed revenue."""
    cols, rows, _ = execute_safe_query(
        DB_PATH, 
        "SELECT SUM(net_revenue) as rev FROM sales WHERE status = 'Completed'"
    )
    completed_rev = rows[0]["rev"]
    
    cols_all, rows_all, _ = execute_safe_query(
        DB_PATH, 
        "SELECT SUM(net_revenue) as rev FROM sales"
    )
    all_rev = rows_all[0]["rev"]
    
    # Difference must be exactly 19,000 (TXN0033: 2 Monitors * 9500)
    assert all_rev - completed_rev == 19000.0

# --- 3. SECURITY & GUARDRAIL TESTS ---

def test_security_ast_blocks_drop_table():
    """Security: Verifies that AST validation blocks destructive DROP TABLE queries."""
    with pytest.raises(SecurityValidationError) as exc:
        validate_sql_query("DROP TABLE sales")
    assert "forbidden" in str(exc.value).lower()

def test_security_ast_blocks_semicolon_chaining():
    """Security: Verifies that stacked query injection via semicolons is blocked."""
    with pytest.raises(SecurityValidationError) as exc:
        validate_sql_query("SELECT * FROM sales; DROP TABLE sales;")
    assert "Multiple SQL statements" in str(exc.value)

def test_security_ast_blocks_update():
    """Security: Verifies that UPDATE mutations are blocked."""
    with pytest.raises(SecurityValidationError) as exc:
        validate_sql_query("UPDATE sales SET net_revenue = 0")
    assert "Only read-only SELECT queries are allowed" in str(exc.value)

def test_security_injection_via_api():
    """Security: Verifies that malicious user queries via API are intercepted and refused."""
    response = client.post("/api/query", json={"query": "Show me total revenue; DROP TABLE sales;", "use_llm": False})
    data = response.json()
    assert data["status"] in ("refused", "error")
    # Verify table sales still exists and is untouched
    cols, rows, _ = execute_safe_query(DB_PATH, "SELECT COUNT(*) as count FROM sales")
    assert rows[0]["count"] == 51

# --- 4. OUT-OF-DOMAIN / INVALID QUERIES ---

def test_out_of_domain_refusal():
    """Guardrails: Verifies that out-of-domain questions are politely refused."""
    response = client.post("/api/query", json={"query": "What is the weather in Hyderabad today?", "use_llm": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refused"
    assert "Sales Business Intelligence Assistant" in data["answer"]

def test_verify_api_key_endpoint():
    """Verifies that the /api/verify-key endpoint correctly rejects empty and invalid keys."""
    res_empty = client.post("/api/verify-key", json={"api_key": ""})
    assert res_empty.status_code == 200
    assert res_empty.json()["valid"] is False

    res_fake = client.post("/api/verify-key", json={"api_key": "fake_test_key_12345"})
    assert res_fake.status_code == 200
    assert res_fake.json()["valid"] is False
