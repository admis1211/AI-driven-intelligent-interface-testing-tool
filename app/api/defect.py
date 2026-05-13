from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import (
    DefectPredictRequest,
    DefectPredictResponse,
    DefectReport,
)
from app.services.defect_service import defect_service

router = APIRouter(prefix="/api/defect", tags=["defect"])


@router.post("/predict", response_model=DefectPredictResponse)
async def predict_defects(request: DefectPredictRequest):
    if not request.document_ids:
        raise HTTPException(status_code=400, detail="必须选择至少一个文档")

    result = await defect_service.predict(
        document_ids=request.document_ids,
        endpoint_url=request.endpoint_url,
        method=request.method or "GET",
    )
    return result


@router.get("/report/{report_id}", response_model=DefectReport)
async def get_defect_report(report_id: str):
    report = defect_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report


@router.get("/reports")
async def list_defect_reports():
    reports = defect_service.list_reports()
    return {"reports": reports, "total": len(reports)}
