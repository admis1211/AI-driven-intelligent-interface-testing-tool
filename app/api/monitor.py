from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.schemas import (
    MonitorConfig,
    MonitorConfigResponse,
    MonitorHistoryResponse,
    MonitorStats,
    MonitorReportResponse,
)
from app.services.monitor_service import monitor_service

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.post("/add", response_model=MonitorConfigResponse)
async def add_monitor(config: MonitorConfig):
    config_data = config.model_dump()
    result = monitor_service.add_config(config_data)
    return result


@router.get("/list")
async def list_monitors():
    configs = monitor_service.get_configs()
    return {"configs": configs, "total": len(configs)}


@router.get("/{config_id}")
async def get_monitor(config_id: str):
    config = monitor_service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Monitor config not found")
    return config


@router.post("/remove")
async def remove_monitor(request: dict):
    config_id = request.get("config_id")
    if not config_id:
        raise HTTPException(status_code=400, detail="config_id is required")
    success = monitor_service.remove_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Monitor config not found")
    return {"message": "Monitor removed successfully"}


@router.post("/{config_id}/toggle")
async def toggle_monitor(config_id: str, enabled: bool):
    config = monitor_service.update_config(config_id, {"enabled": enabled})
    if not config:
        raise HTTPException(status_code=404, detail="Monitor config not found")
    return config


@router.get("/history/{config_id}")
async def get_history(config_id: str, limit: int = 100):
    history = monitor_service.get_history(config_id, limit)
    return {"history": history, "total": len(history)}


@router.get("/stats/{config_id}")
async def get_stats(config_id: str, hours: int = 24):
    config = monitor_service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Monitor config not found")

    stats = monitor_service.get_stats(config_id, hours)
    stats["config_name"] = config["name"]
    return stats


@router.get("/report")
async def get_report(
    start_date: Optional[str] = None, end_date: Optional[str] = None, hours: int = 24
):
    configs = monitor_service.get_configs()
    stats_list = []

    for config in configs:
        stats = monitor_service.get_stats(config["id"], hours)
        stats["config_name"] = config["name"]
        stats_list.append(stats)

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(hours=hours)

    return {
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
        "stats": stats_list,
    }


@router.post("/check/{config_id}")
async def check_endpoint(config_id: str):
    import asyncio

    config = monitor_service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Monitor config not found")

    result = await monitor_service.check_endpoint(config)
    return result
