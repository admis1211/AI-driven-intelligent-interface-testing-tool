from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import json
from app.models.schemas import (
    TestCaseGenerateRequest,
    TestCaseGenerateResponse,
    TestCaseItem,
)
from app.services.testcase_service import testcase_service

router = APIRouter(prefix="/api/testcase", tags=["testcase"])


@router.post("/generate", response_model=TestCaseGenerateResponse)
async def generate_testcases(request: TestCaseGenerateRequest):
    """根据文档生成测试用例"""
    testcases = await testcase_service.generate_testcases(
        document_ids=request.document_ids,
        endpoint_url=request.endpoint_url,
        method=request.method,
        count=request.count,
    )
    return TestCaseGenerateResponse(testcases=testcases, count=len(testcases))


@router.post("/export/json")
async def export_json(testcases: List[TestCaseItem]):
    """导出测试用例为JSON格式"""
    json_str = testcase_service.export_json(testcases)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=testcases.json"},
    )


@router.post("/export/postman")
async def export_postman(testcases: List[TestCaseItem]):
    """导出测试用例为Postman Collection格式"""
    collection = testcase_service.export_postman(testcases)
    json_str = json.dumps(collection, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=postman_collection.json"},
    )


@router.post("/export/excel")
async def export_excel(testcases: List[TestCaseItem]):
    """导出测试用例为Excel格式"""
    try:
        excel_data = testcase_service.export_excel(testcases)
        return StreamingResponse(
            iter([excel_data]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=testcases.xlsx"},
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
