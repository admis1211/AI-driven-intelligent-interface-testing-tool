import uuid
import json
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.schemas import (
    DefectPredictRequest,
    DefectPredictResponse,
    DefectReport,
    DefectItem,
)
from app.services.llm_service import llm_service
from app.services import document_manager
from app.core.config import settings
import os


class DefectService:
    def __init__(self):
        self.reports: Dict[str, dict] = {}

    async def predict(
        self,
        document_ids: List[str],
        endpoint_url: Optional[str] = None,
        method: str = "GET",
    ) -> DefectPredictResponse:
        report_id = str(uuid.uuid4())

        try:
            document_contents = []
            doc_names = []

            for doc in document_manager.uploaded_files:
                if doc.filename in document_ids:
                    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
                    if os.path.exists(file_path):
                        from app.services.document_service import document_reader

                        content = document_reader.read_document(file_path)
                        if content:
                            document_contents.append(content)
                            doc_names.append(doc.filename)

            if not document_contents:
                return DefectPredictResponse(
                    report_id=report_id, status="failed", message="未找到有效的文档内容"
                )

            combined_content = "\n\n".join(document_contents)

            endpoint_info = ""
            if endpoint_url:
                endpoint_info = f"\n目标接口:\n- URL: {endpoint_url}\n- 方法: {method}"

            prompt = self._build_prompt(combined_content, endpoint_info)

            response = llm_service.llm.invoke(prompt)
            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            parsed = self._parse_llm_response(response_text)

            report = {
                "report_id": report_id,
                "documents": doc_names,
                "endpoint_url": endpoint_url,
                "method": method,
                "defects": parsed.get("defects", []),
                "test_focus": parsed.get("test_focus", []),
                "risk_level": parsed.get("risk_level", "low"),
                "summary": parsed.get("summary", ""),
                "created_at": datetime.now(),
            }

            self.reports[report_id] = report

            return DefectPredictResponse(
                report_id=report_id,
                status="completed",
                message=f"分析完成，发现 {len(parsed.get('defects', []))} 个缺陷",
            )

        except Exception as e:
            return DefectPredictResponse(
                report_id=report_id, status="failed", message=f"分析失败: {str(e)}"
            )

    def _build_prompt(self, document_content: str, endpoint_info: str) -> str:
        return f"""你是一个专业的接口测试工程师。请分析以下接口文档，预测可能存在的缺陷。

文档内容：
{document_content}
{endpoint_info}

请从以下6个维度分析：
1. 参数校验（必填参数、类型校验、长度校验）
2. 返回值格式（字段完整性、类型一致性）
3. 安全性（SQL注入、XSS、CSRF、权限校验）
4. 并发安全（竞态条件、锁机制）
5. 错误处理（异常捕获、错误信息）
6. 业务逻辑（边界条件、逻辑漏洞）

请严格输出JSON格式（不要有其他内容）：
{{
  "defects": [
    {{
      "category": "安全性",
      "severity": "high",
      "description": "描述",
      "location": "位置",
      "suggestion": "建议"
    }}
  ],
  "test_focus": ["测试重点1", "测试重点2"],
  "risk_level": "high",
  "summary": "总结"
}}"""

    def _parse_llm_response(self, response_text: str) -> dict:
        try:
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        return {
            "defects": [],
            "test_focus": [],
            "risk_level": "unknown",
            "summary": "无法解析AI响应",
        }

    def get_report(self, report_id: str) -> Optional[DefectReport]:
        report = self.reports.get(report_id)
        if not report:
            return None

        defects = []
        for d in report.get("defects", []):
            defects.append(
                DefectItem(
                    category=d.get("category", "未知"),
                    severity=d.get("severity", "low"),
                    description=d.get("description", ""),
                    location=d.get("location", ""),
                    suggestion=d.get("suggestion", ""),
                )
            )

        return DefectReport(
            report_id=report["report_id"],
            documents=report["documents"],
            endpoint_url=report.get("endpoint_url"),
            method=report["method"],
            defects=defects,
            test_focus=report.get("test_focus", []),
            risk_level=report.get("risk_level", "low"),
            summary=report.get("summary", ""),
            created_at=report["created_at"],
        )

    def list_reports(self) -> List[dict]:
        return [
            {
                "report_id": r["report_id"],
                "documents": r["documents"],
                "endpoint_url": r.get("endpoint_url"),
                "risk_level": r.get("risk_level", "low"),
                "defect_count": len(r.get("defects", [])),
                "created_at": r["created_at"].isoformat(),
            }
            for r in self.reports.values()
        ]


defect_service = DefectService()
