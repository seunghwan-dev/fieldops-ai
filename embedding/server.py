"""
Embedding Server for FieldOps-AI.

WHY: Serves multilingual-e5-large as an independent HTTP service.
     Generates vectors for Oracle Vector Search + BM25 Hybrid Search.
RISK: Model occupies ~2GB VRAM on load. May need CPU fallback if GPU OOM.
INTERVIEW: "Reused P1's proven e5-large + 1024-dim + cosine similarity config."
"""

import os
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FieldOps-AI Embedding Server")

model_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
model = None


@app.on_event("startup")
async def load_model():
    global model
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    dimension: int


@app.get("/health")
async def health():
    if model is None:
        return {"status": "loading"}, 503
    return {"status": "healthy", "model": model_name}


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    # WHY: e5-large benefits from "query: " or "passage: " prefix.
    #      Callers are expected to prepend the appropriate prefix.
    embeddings = model.encode(request.texts, normalize_embeddings=True)
    return EmbedResponse(
        embeddings=embeddings.tolist(),
        dimension=embeddings.shape[1]
    )
