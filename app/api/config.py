from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ConfigUpdate,
    ConfigResponse,
    APIConfig,
    APIConfigResponse,
)
from app.core.config import settings
from app.services.llm_service import llm_service
import os

router = APIRouter(prefix="/api/config", tags=["configuration"])

CONFIG_MAPPING = {
    "APP_NAME": (settings.APP_NAME, "string"),
    "APP_VERSION": (settings.APP_VERSION, "string"),
    "OPENAI_MODEL": (settings.OPENAI_MODEL, "string"),
    "OPENAI_TEMPERATURE": (settings.OPENAI_TEMPERATURE, "float"),
}

user_api_config = {
    "api_key": None,
    "api_base": None,
    "model_name": None,
    "temperature": settings.OPENAI_TEMPERATURE,
}


@router.get("/api", response_model=APIConfigResponse)
async def get_api_config():
    return APIConfigResponse(
        api_base=user_api_config.get("api_base") or settings.OPENAI_API_BASE,
        model_name=user_api_config.get("model_name") or settings.OPENAI_MODEL,
        temperature=user_api_config.get("temperature", settings.OPENAI_TEMPERATURE),
    )


@router.post("/api")
async def update_api_config(config: APIConfig):
    try:
        if config.api_key is not None:
            user_api_config["api_key"] = config.api_key
        if config.api_base is not None:
            user_api_config["api_base"] = config.api_base
        if config.model_name is not None:
            user_api_config["model_name"] = config.model_name
        if config.temperature is not None:
            user_api_config["temperature"] = config.temperature

        llm_service.update_config(
            api_key=user_api_config["api_key"],
            api_base=user_api_config["api_base"],
            model_name=user_api_config["model_name"],
            temperature=user_api_config["temperature"],
        )

        return {
            "message": "API配置已更新",
            "api_base": user_api_config.get("api_base") or settings.OPENAI_API_BASE,
            "model_name": user_api_config.get("model_name") or settings.OPENAI_MODEL,
            "temperature": user_api_config.get(
                "temperature", settings.OPENAI_TEMPERATURE
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新API配置失败: {str(e)}")


@router.get("/", response_model=list[ConfigResponse])
async def get_all_configs():
    return [
        ConfigResponse(key=key, value=value[0], type=value[1])
        for key, value in CONFIG_MAPPING.items()
    ]


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(key: str):
    if key not in CONFIG_MAPPING:
        raise HTTPException(status_code=404, detail=f"配置项 {key} 不存在")

    value, config_type = CONFIG_MAPPING[key]
    return ConfigResponse(key=key, value=value, type=config_type)


@router.put("/{key}")
async def update_config(key: str, config: ConfigUpdate):
    if key not in CONFIG_MAPPING:
        raise HTTPException(status_code=404, detail=f"配置项 {key} 不存在")

    old_value, config_type = CONFIG_MAPPING[key]

    try:
        if config_type == "int":
            new_value = int(config.value)
        elif config_type == "float":
            new_value = float(config.value)
        else:
            new_value = config.value

        setattr(settings, key, new_value)
        CONFIG_MAPPING[key] = (new_value, config_type)

        return {"message": f"配置项 {key} 已更新", "new_value": new_value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新配置失败: {str(e)}")
