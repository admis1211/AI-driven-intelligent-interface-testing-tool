from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    AgentTestRequest,
    AgentTestResponse,
    AgentTestReport,
)
from app.services.agent_service import agent_service

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/test", response_model=AgentTestResponse)
async def run_agent_test(request: AgentTestRequest):
    result = await agent_service.run_test(
        document_ids=request.document_ids,
        endpoint_url=request.endpoint_url,
        method=request.method,
        headers=request.headers,
        params=request.params,
        body=request.body,
        expected_status=request.expected_status,
        test_scenarios=request.test_scenarios,
    )
    return result


@router.get("/test/{test_id}")
async def get_test_status(test_id: str):
    status = agent_service.get_status(test_id)
    if not status:
        raise HTTPException(status_code=404, detail="Test not found")
    return status


@router.get("/test/{test_id}/report", response_model=AgentTestReport)
async def get_test_report(test_id: str):
    report = agent_service.get_report(test_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
