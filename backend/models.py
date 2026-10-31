"""
Pydantic Data Schemas
Defines request and response models for the BI Assistant API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question about sales data")
    use_llm: Optional[bool] = Field(True, description="Whether to attempt LLM agent before deterministic fallback")

class MetricCard(BaseModel):
    label: str
    value: str
    subtitle: Optional[str] = None
    delta: Optional[str] = None

class ChartData(BaseModel):
    chart_type: str = Field(..., description="bar, line, or doughnut")
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]

class QueryResponse(BaseModel):
    query: str
    status: str = Field("success", description="success, error, or refused")
    answer: str
    sql_query: Optional[str] = None
    execution_time_ms: float = 0.0
    row_count: int = 0
    columns: List[str] = []
    data: List[Dict[str, Any]] = []
    metrics: List[MetricCard] = []
    chart: Optional[ChartData] = None
    engine_used: str = "deterministic_semantic_engine"
    explanation: Optional[str] = None
    error_message: Optional[str] = None

class AuditItem(BaseModel):
    transaction_id: str
    issue: str
    action: str
    severity: str
    resolved: bool

class DataHealthResponse(BaseModel):
    total_records: int
    table_name: str
    database_file: str
    columns: List[Dict[str, str]]
    audit_log: List[AuditItem]
    status: str
