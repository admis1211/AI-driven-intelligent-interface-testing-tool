import json
import uuid
import aiohttp
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.logger import get_logger

logger = get_logger("monitor")


class MonitorService:
    def __init__(
        self,
        config_file: str = "data/monitor_configs.json",
        history_file: str = "data/monitor_history.json",
    ):
        self.config_file = config_file
        self.history_file = history_file
        self.scheduler_task = None
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.history_file).parent.mkdir(parents=True, exist_ok=True)

        if not Path(self.config_file).exists():
            self._save_configs({"version": "1.0", "configs": []})
        if not Path(self.history_file).exists():
            self._save_history({"version": "1.0", "history": []})

    def _load_configs(self) -> Dict:
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load monitor configs: {e}")
            return {"version": "1.0", "configs": []}

    def _save_configs(self, data: Dict):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save monitor configs: {e}")

    def _load_history(self) -> Dict:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load monitor history: {e}")
            return {"version": "1.0", "history": []}

    def _save_history(self, data: Dict):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save monitor history: {e}")

    def add_config(self, config_data: Dict) -> Dict:
        config_id = str(uuid.uuid4())
        config = {
            "id": config_id,
            "name": config_data.get("name"),
            "url": config_data.get("url"),
            "method": config_data.get("method", "GET"),
            "headers": config_data.get("headers", {}),
            "params": config_data.get("params", {}),
            "body": config_data.get("body"),
            "frequency": config_data.get("frequency", 60),
            "timeout": config_data.get("timeout", 30),
            "alert_threshold": config_data.get("alert_threshold", 5.0),
            "enabled": True,
            "created_at": datetime.now().isoformat(),
        }

        data = self._load_configs()
        data["configs"].append(config)
        self._save_configs(data)

        logger.info(f"Added monitor config: {config['name']} ({config_id})")
        return config

    def get_configs(self) -> List[Dict]:
        data = self._load_configs()
        return data.get("configs", [])

    def get_config(self, config_id: str) -> Optional[Dict]:
        data = self._load_configs()
        for config in data.get("configs", []):
            if config["id"] == config_id:
                return config
        return None

    def remove_config(self, config_id: str) -> bool:
        data = self._load_configs()
        original_len = len(data["configs"])
        data["configs"] = [c for c in data["configs"] if c["id"] != config_id]

        if len(data["configs"]) < original_len:
            self._save_configs(data)

            history_data = self._load_history()
            history_data["history"] = [
                h
                for h in history_data.get("history", [])
                if h["config_id"] != config_id
            ]
            self._save_history(history_data)

            logger.info(f"Removed monitor config: {config_id}")
            return True
        return False

    def update_config(self, config_id: str, updates: Dict) -> Optional[Dict]:
        data = self._load_configs()
        for config in data.get("configs", []):
            if config["id"] == config_id:
                config.update(updates)
                self._save_configs(data)
                logger.info(f"Updated monitor config: {config_id}")
                return config
        return None

    async def check_endpoint(self, config: Dict) -> Dict:
        start_time = datetime.now()
        result = {
            "id": str(uuid.uuid4()),
            "config_id": config["id"],
            "status_code": 0,
            "response_time": 0.0,
            "success": False,
            "error_message": None,
            "checked_at": start_time.isoformat(),
        }

        url = config["url"]
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        params = config.get("params", {})
        body = config.get("body")
        timeout = config.get("timeout", 30)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=body,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    result["status_code"] = response.status
                    result["success"] = 200 <= response.status < 300

        except asyncio.TimeoutError:
            result["error_message"] = "Request timeout"
        except aiohttp.ClientError as e:
            result["error_message"] = str(e)
        except Exception as e:
            result["error_message"] = str(e)

        result["response_time"] = (datetime.now() - start_time).total_seconds()

        self._save_history_result(result)

        return result

    def _save_history_result(self, result: Dict):
        data = self._load_history()
        data["history"].append(result)

        max_history = 10000
        if len(data["history"]) > max_history:
            data["history"] = data["history"][-max_history:]

        self._save_history(data)

    def get_history(self, config_id: str, limit: int = 100) -> List[Dict]:
        data = self._load_history()
        history = [h for h in data.get("history", []) if h["config_id"] == config_id]
        return history[-limit:]

    def get_stats(self, config_id: str, hours: int = 24) -> Dict:
        data = self._load_history()
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        history = [
            h
            for h in data.get("history", [])
            if h["config_id"] == config_id and h["checked_at"] >= cutoff
        ]

        if not history:
            return {
                "config_id": config_id,
                "total_checks": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "uptime_percentage": 100.0,
                "last_check": None,
            }

        success_count = sum(1 for h in history if h["success"])
        failure_count = len(history) - success_count
        response_times = [h["response_time"] for h in history]

        return {
            "config_id": config_id,
            "total_checks": len(history),
            "success_count": success_count,
            "failure_count": failure_count,
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "uptime_percentage": (success_count / len(history)) * 100,
            "last_check": history[-1]["checked_at"],
        }

    async def run_monitoring(self):
        while True:
            try:
                configs = self.get_configs()
                for config in configs:
                    if config.get("enabled", True):
                        result = await self.check_endpoint(config)

                        if not result["success"]:
                            logger.warning(
                                f"Monitor alert: {config['name']} failed - {result.get('error_message')}"
                            )

                        if result["response_time"] > config.get("alert_threshold", 5.0):
                            logger.warning(
                                f"Monitor alert: {config['name']} slow response - {result['response_time']:.2f}s"
                            )

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(60)

    def start_scheduler(self):
        if self.scheduler_task is None:
            self.scheduler_task = asyncio.create_task(self.run_monitoring())
            logger.info("Monitor scheduler started")


monitor_service = MonitorService()
