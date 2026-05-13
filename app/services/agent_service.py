import uuid
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.schemas import (
    AgentTestResponse,
    TestScenarioResult,
    AgentTestReport,
)


class AgentService:
    def __init__(self):
        self.tests: Dict[str, dict] = {}

    async def run_test(
        self,
        document_ids: List[str],
        endpoint_url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
        test_scenarios: Optional[List[str]] = None,
    ) -> AgentTestResponse:
        test_id = str(uuid.uuid4())

        scenarios = test_scenarios or self._generate_default_scenarios()

        self.tests[test_id] = {
            "test_id": test_id,
            "endpoint_url": endpoint_url,
            "method": method,
            "headers": headers or {},
            "params": params or {},
            "body": body,
            "expected_status": expected_status,
            "scenarios": scenarios,
            "status": "running",
            "progress": 0,
            "results": [],
            "start_time": datetime.now(),
            "end_time": None,
            "summary": "",
            "suggestions": [],
        }

        results = []
        for i, scenario in enumerate(scenarios):
            result = await self._execute_scenario(
                scenario=scenario,
                endpoint_url=endpoint_url,
                method=method,
                headers=headers or {},
                params=params or {},
                body=body,
                expected_status=expected_status,
            )
            results.append(result)

            progress = int((i + 1) / len(scenarios) * 100)
            self.tests[test_id]["progress"] = progress
            self.tests[test_id]["results"] = results

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        pass_rate = (passed / len(results) * 100) if results else 0

        self.tests[test_id]["status"] = "completed"
        self.tests[test_id]["progress"] = 100
        self.tests[test_id]["end_time"] = datetime.now()
        self.tests[test_id]["summary"] = (
            f"测试完成: {passed}/{len(results)} 通过 ({pass_rate:.1f}%)"
        )
        self.tests[test_id]["suggestions"] = self._generate_suggestions(results)

        return AgentTestResponse(
            test_id=test_id,
            status="completed",
            progress=100,
            message=self.tests[test_id]["summary"],
        )

    async def _execute_scenario(
        self,
        scenario: str,
        endpoint_url: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        body: Optional[Dict[str, Any]],
        expected_status: int,
    ) -> TestScenarioResult:
        start_time = datetime.now()

        modified_params = self._modify_params_for_scenario(scenario, params)
        modified_body = self._modify_body_for_scenario(scenario, body)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=endpoint_url,
                    headers=headers,
                    params=modified_params,
                    json=modified_body if method in ["POST", "PUT", "PATCH"] else None,
                )

                response_time = (datetime.now() - start_time).total_seconds()
                passed = response.status_code == expected_status

                return TestScenarioResult(
                    scenario=scenario,
                    request_method=method,
                    request_url=endpoint_url,
                    request_headers=headers,
                    request_params=modified_params,
                    request_body=modified_body,
                    response_status=response.status_code,
                    response_body=response.text[:500] if response.text else None,
                    response_time=response_time,
                    passed=passed,
                    error=None,
                )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return TestScenarioResult(
                scenario=scenario,
                request_method=method,
                request_url=endpoint_url,
                request_headers=headers,
                request_params=modified_params,
                request_body=modified_body,
                response_status=0,
                response_body=None,
                response_time=response_time,
                passed=False,
                error=str(e),
            )

    def _generate_default_scenarios(self) -> List[str]:
        return [
            "正常请求",
            "空参数",
            "超长参数",
            "特殊字符",
        ]

    def _modify_params_for_scenario(
        self, scenario: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        modified = params.copy() if params else {}

        if scenario == "空参数":
            modified = {}
        elif scenario == "超长参数":
            for key in modified:
                modified[key] = "a" * 10000
        elif scenario == "特殊字符":
            for key in modified:
                modified[key] = "<script>alert('xss')</script>"

        return modified

    def _modify_body_for_scenario(
        self, scenario: str, body: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if not body:
            return None

        modified = body.copy()

        if scenario == "空参数":
            modified = {}
        elif scenario == "超长参数":
            for key in modified:
                if isinstance(modified[key], str):
                    modified[key] = "a" * 10000
        elif scenario == "特殊字符":
            for key in modified:
                if isinstance(modified[key], str):
                    modified[key] = "<script>alert('xss')</script>"

        return modified

    def _generate_suggestions(self, results: List[TestScenarioResult]) -> List[str]:
        suggestions = []

        failed = [r for r in results if not r.passed]

        if failed:
            for result in failed:
                if result.error:
                    suggestions.append(f"场景 '{result.scenario}' 失败: {result.error}")
                elif result.response_status != 200:
                    suggestions.append(
                        f"场景 '{result.scenario}' 返回状态码 {result.response_status}，预期 200"
                    )

        if not suggestions:
            suggestions.append("所有测试场景通过！接口工作正常。")

        return suggestions

    def get_status(self, test_id: str) -> Optional[dict]:
        test = self.tests.get(test_id)
        if not test:
            return None
        return {
            "test_id": test["test_id"],
            "status": test["status"],
            "progress": test["progress"],
            "message": test.get("summary", ""),
        }

    def get_report(self, test_id: str) -> Optional[AgentTestReport]:
        test = self.tests.get(test_id)
        if not test:
            return None

        results = test.get("results", [])
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        pass_rate = (passed / len(results) * 100) if results else 0

        return AgentTestReport(
            test_id=test["test_id"],
            endpoint_url=test["endpoint_url"],
            method=test["method"],
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=failed,
            pass_rate=pass_rate,
            results=results,
            start_time=test["start_time"],
            end_time=test.get("end_time") or datetime.now(),
            summary=test.get("summary", ""),
            suggestions=test.get("suggestions", []),
        )


agent_service = AgentService()
