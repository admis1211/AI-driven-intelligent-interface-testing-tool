from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConfigUpdate(BaseModel):
    key: str
    value: Any


class ConfigResponse(BaseModel):
    key: str
    value: Any
    type: str


class APIConfig(BaseModel):
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.7


class APIConfigResponse(BaseModel):
    api_base: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = 0.7


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_context: bool = True
    selected_documents: Optional[List[str]] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[Dict[str, Any]]] = None


class ChatSession(BaseModel):
    session_id: str
    created_at: datetime
    last_message: Optional[str] = None
    message_count: int = 0

    model_config = {"protected_namespaces": ()}


class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSession]
    total: int


class DeleteSessionResponse(BaseModel):
    success: bool
    message: str


class DocumentUpload(BaseModel):
    filename: str
    size: int
    uploaded_at: datetime
    status: str = "pending"


class DocumentListResponse(BaseModel):
    documents: List[DocumentUpload]
    total: int


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class MonitorConfig(BaseModel):
    name: str
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, Any]] = {}
    body: Optional[Dict[str, Any]] = None
    frequency: int = 60
    timeout: int = 30
    alert_threshold: float = 5.0


class MonitorConfigResponse(BaseModel):
    id: str
    name: str
    url: str
    method: str
    headers: Dict[str, str]
    params: Dict[str, Any]
    body: Optional[Dict[str, Any]]
    frequency: int
    timeout: int
    alert_threshold: float
    enabled: bool
    created_at: datetime


class MonitorHistoryResponse(BaseModel):
    id: str
    config_id: str
    status_code: int
    response_time: float
    success: bool
    error_message: Optional[str]
    checked_at: datetime


class MonitorStats(BaseModel):
    config_id: str
    config_name: str
    total_checks: int
    success_count: int
    failure_count: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    uptime_percentage: float
    last_check: Optional[datetime]


class MonitorReportResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    stats: List[MonitorStats]


class AgentTestRequest(BaseModel):
    document_ids: List[str]
    endpoint_url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    test_scenarios: Optional[List[str]] = None


class AgentTestResponse(BaseModel):
    test_id: str
    status: str
    progress: int = 0
    message: str


class TestScenarioResult(BaseModel):
    scenario: str
    request_method: str
    request_url: str
    request_headers: Optional[Dict[str, str]]
    request_params: Optional[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    response_status: int
    response_body: Optional[Any]
    response_time: float
    passed: bool
    error: Optional[str] = None


class AgentTestReport(BaseModel):
    test_id: str
    endpoint_url: str
    method: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    results: List[TestScenarioResult]
    start_time: datetime
    end_time: datetime
    summary: str
    suggestions: List[str]


class DefectPredictRequest(BaseModel):
    document_ids: List[str]
    endpoint_url: Optional[str] = None
    method: Optional[str] = "GET"


class DefectPredictResponse(BaseModel):
    report_id: str
    status: str
    message: str


class DefectItem(BaseModel):
    category: str
    severity: str
    description: str
    location: str
    suggestion: str


class DefectReport(BaseModel):
    report_id: str
    documents: List[str]
    endpoint_url: Optional[str]
    method: str
    defects: List[DefectItem]
    test_focus: List[str]
    risk_level: str
    summary: str
    created_at: datetime


class TestCaseItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    method: str
    url: str
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    priority: str = "P1"

    model_config = {"protected_namespaces": ()}


class TestCaseGenerateRequest(BaseModel):
    document_ids: List[str]
    endpoint_url: str
    method: str = "GET"
    count: int = Field(default=10, ge=1, le=50)


class TestCaseGenerateResponse(BaseModel):
    testcases: List[TestCaseItem]
    count: int


class TestCaseExportRequest(BaseModel):
    format: str
    testcases: List[TestCaseItem]
