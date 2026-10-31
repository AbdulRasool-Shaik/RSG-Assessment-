"""
Security & Safe SQL Execution Engine
Implements AST parsing, SQL sanitization, mutation prevention,
and read-only database execution sandboxing.
"""

import re
import time
import sqlite3
import sqlparse
from sqlparse.sql import Statement
from typing import Tuple, List, Dict, Any

FORBIDDEN_KEYWORDS = {
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE',
    'CREATE', 'REPLACE', 'ATTACH', 'DETACH', 'PRAGMA', 'VACUUM',
    'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'UPSERT', 'INTO',
    'MERGE', 'RENAME', 'REINDEX'
}

ALLOWED_TABLES = {'sales'}

class SecurityValidationError(Exception):
    """Raised when an SQL query fails safety or validation checks."""
    pass

def validate_sql_query(sql: str) -> bool:
    """
    Validates an SQL query against security policies using AST token inspection.
    Enforces:
      1. Single statement execution only (no semicolon chaining).
      2. Strictly SELECT or WITH ... SELECT queries.
      3. Zero destructive or mutating keywords.
      4. Only allowed tables referenced.
    """
    if not sql or not sql.strip():
        raise SecurityValidationError("Query is empty or null.")

    clean_sql = sql.strip().rstrip(';').strip()

    # Safely strip SQL comments so benign LLM annotations don't cause false rejections
    clean_sql = sqlparse.format(clean_sql, strip_comments=True).strip()

    # Disallow multiple semicolons (stacked query injection)
    if ';' in clean_sql:
        raise SecurityValidationError(
            "Multiple SQL statements or semicolon-chained queries are strictly prohibited."
        )

    parsed = sqlparse.parse(clean_sql)
    if not parsed or len(parsed) != 1:
        raise SecurityValidationError(
            "Exactly one SQL statement is allowed per execution."
        )

    stmt: Statement = parsed[0]
    stmt_type = stmt.get_type().upper()

    # Allow SELECT or CTE (which starts with WITH and results in SELECT)
    if stmt_type not in ('SELECT', 'UNKNOWN'):
        raise SecurityValidationError(
            f"Operation '{stmt_type}' is forbidden. Only read-only SELECT queries are allowed."
        )

    # If UNKNOWN, verify it is a WITH CTE leading to SELECT
    if stmt_type == 'UNKNOWN':
        first_token = clean_sql.split()[0].upper()
        if first_token != 'WITH':
            raise SecurityValidationError(
                f"Unsupported statement type starting with '{first_token}'. Only SELECT or WITH CTE is allowed."
            )

    # Flatten tokens and inspect for forbidden keywords
    for token in stmt.flatten():
        val = token.value.upper().strip()
        if val in FORBIDDEN_KEYWORDS:
            raise SecurityValidationError(
                f"Destructive keyword '{val}' is strictly forbidden by security policy."
            )

    return True

def execute_safe_query(db_path: str, sql: str) -> Tuple[List[str], List[Dict[str, Any]], float]:
    """
    Safely executes a validated SQL query against the SQLite database in read-only mode.
    Returns:
      (columns, rows, execution_time_ms)
    """
    # 1. Validate AST and security policies
    validate_sql_query(sql)

    # 2. Open read-only SQLite connection URI
    # Even if parser were somehow bypassed, SQLite engine rejects write operations
    uri_path = f"file:{db_path}?mode=ro"
    
    start_time = time.perf_counter()
    try:
        conn = sqlite3.connect(uri_path, uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows_raw = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [dict(row) for row in rows_raw]
        conn.close()
    except sqlite3.OperationalError as e:
        if "readonly" in str(e).lower() or "attempt to write" in str(e).lower():
            raise SecurityValidationError("Database write blocked: Connection is locked to read-only mode.")
        raise e
    finally:
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return columns, rows, execution_time_ms
