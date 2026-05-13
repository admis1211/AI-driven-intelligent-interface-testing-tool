from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import config, chat, documents, health, monitor, agent, defect, testcase
from app.models.schemas import HealthResponse
from app.core.config import settings
from datetime import datetime
import os

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 LangChain 和 FAISS 的 AI 对话系统",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(health.router)
app.include_router(monitor.router)
app.include_router(agent.router)
app.include_router(defect.router)
app.include_router(testcase.router)


# Serve static files (frontend)
frontend_dir = "."
if os.path.exists("index.html"):

    @app.get("/", tags=["Frontend"])
    async def serve_index():
        return FileResponse("index.html")

    @app.get("/index.html", tags=["Frontend"])
    async def serve_index_html():
        return FileResponse("index.html")

    # Serve CSS and JS files
    if os.path.exists("styles.css"):

        @app.get("/styles.css", tags=["Frontend"])
        async def serve_css():
            return FileResponse("styles.css")

    if os.path.exists("app.js"):

        @app.get("/app.js", tags=["Frontend"])
        async def serve_js():
            return FileResponse("app.js")

    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy", version=settings.APP_VERSION, timestamp=datetime.now()
    )


@app.get("/api/health", response_model=HealthResponse)
async def api_health():
    return HealthResponse(
        status="healthy", version=settings.APP_VERSION, timestamp=datetime.now()
    )


@app.on_event("startup")
async def startup_event():
    from app.services.monitor_service import monitor_service
    import asyncio

    asyncio.create_task(monitor_service.run_monitoring())
    print("Monitor scheduler started")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
