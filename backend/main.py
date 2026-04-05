"""
FieldOps-AI Backend — API Gateway.

WHY: Single entry point for all AI features. Routers added per Phase.
RISK: Oracle/Ollama/Embedding connection failure caught by readiness check.
INTERVIEW: "Built healthcheck chain first in Phase 0 to secure infrastructure stability."
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import oracledb

from routers.knowledge import router as knowledge_router
from routers.search import router as search_router
from routers.predict import router as predict_router
from routers.fusion import router as fusion_router

logging.basicConfig(level=os.getenv("LOG_LEVEL", "info").upper())
logger = logging.getLogger(__name__)

# --- Environment Variables ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
ORACLE_HOST = os.getenv("ORACLE_HOST", "oracle")
ORACLE_USER = os.getenv("ORACLE_USER", "fieldops")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "FREEPDB1")
EMBEDDING_HOST = os.getenv("EMBEDDING_HOST", "http://embedding:8001")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("FieldOps-AI Backend starting...")
    yield
    logger.info("FieldOps-AI Backend shutting down.")


app = FastAPI(
    title="FieldOps-AI",
    description="AI Agent that works so engineers don't have to",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(predict_router, prefix="/api/v1")
app.include_router(fusion_router, prefix="/api/v1")


@app.get("/health")
async def health():
    """
    Basic health check for Docker healthcheck.

    WHY: Determines service_healthy condition in docker-compose depends_on.
    """
    return {"status": "healthy", "service": "fieldops-ai-backend"}


@app.get("/readiness")
async def readiness():
    """
    Readiness check — verifies Oracle + Ollama + Embedding connectivity.

    WHY: Confirms all dependent services are ready. Part of Phase 0 completion criteria.
    INTERVIEW: "health checks process liveness; readiness checks all dependencies."
    """
    checks = {}

    # Check Oracle connection
    try:
        dsn = f"{ORACLE_HOST}:1521/{ORACLE_SERVICE}"
        conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=dsn)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        cursor.close()
        conn.close()
        checks["oracle"] = "connected"
    except Exception as e:
        checks["oracle"] = f"error: {str(e)}"

    # Check Ollama connection
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                tags = resp.json()
                models = [m["name"] for m in tags.get("models", [])]
                checks["ollama"] = f"connected, models: {models}"
            else:
                checks["ollama"] = f"error: status {resp.status_code}"
    except Exception as e:
        checks["ollama"] = f"error: {str(e)}"

    # Check Embedding connection
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{EMBEDDING_HOST}/health")
            if resp.status_code == 200:
                checks["embedding"] = "connected"
            else:
                checks["embedding"] = f"error: status {resp.status_code}"
    except Exception as e:
        checks["embedding"] = f"error: {str(e)}"

    all_ok = all("connected" in str(v) for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
    }
