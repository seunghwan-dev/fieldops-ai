"""
Knowledge Ingestion API Router.

WHY: Single endpoint to ingest PDF -> VLM -> chunk -> embed -> store.
     Orchestrates the full pipeline in one API call.
RISK: Long-running request (~30s per page). Consider async background task for production.
INTERVIEW: "One API call triggers: VLM extraction -> smart chunking -> embedding -> Oracle storage."
"""

import os
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from schemas.knowledge import (
    IngestResponse,
    ChunkDistribution,
    TableExtraction,
    FigureExtraction,
)
from services import vlm_service, chunking_service, embedding_service, oracle_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["knowledge"])


def _derive_doc_id(filename: str) -> str:
    """
    Derive doc_id from filename: lowercase, no extension, hyphens only.

    WHY: Consistent, human-readable document identifiers.
    """
    stem = Path(filename).stem.lower()
    return stem.replace("_", "-").replace(" ", "-")


def _infer_doc_type(filename: str) -> str:
    """Infer document type from filename prefix."""
    name = filename.lower()
    if "paper" in name:
        return "paper"
    elif "report" in name:
        return "report"
    elif "safety" in name:
        return "safety"
    return "paper"


def _extract_title_from_text(pages) -> str:
    """Extract document title from first page text content."""
    if pages and pages[0].text_content:
        lines = pages[0].text_content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                return line[:500]
    return "Untitled Document"


@router.post("/knowledge/ingest", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)):
    """
    Ingest a PDF document through the VLM pipeline.

    Pipeline: PDF -> page images -> GPT-4o Vision -> chunking -> embedding -> Oracle.

    WHY: Single API call for complete document ingestion.
    RISK: ~30s per page. 6-page PDF = ~3 min. Client must set adequate timeout.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF files are accepted.",
        )

    doc_id = _derive_doc_id(file.filename)
    logger.info(f"Starting ingestion: {file.filename} -> doc_id={doc_id}")

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        logger.info(f"[{doc_id}] Step 1: VLM extraction")
        pages = await vlm_service.extract_from_pdf(tmp_path)

        logger.info(f"[{doc_id}] Step 2: Chunking ({len(pages)} pages)")
        chunks = chunking_service.chunk_pages(pages, doc_id)

        logger.info(f"[{doc_id}] Step 3: Embedding ({len(chunks)} chunks)")
        chunk_texts = [c["chunk_text"] for c in chunks]
        embeddings = await embedding_service.embed_passages(chunk_texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb

        logger.info(f"[{doc_id}] Step 4: Oracle storage")
        doc_title = _extract_title_from_text(pages)
        doc_meta = {
            "doc_id": doc_id,
            "doc_title": doc_title,
            "doc_type": _infer_doc_type(file.filename),
            "file_path": file.filename,
            "page_count": len(pages),
        }
        await oracle_service.insert_doc(doc_meta)
        await oracle_service.insert_chunks(chunks)

        # WHY: Oracle Text index must be synced after INSERT for BM25 search to work.
        # RISK: sync may take a few seconds for large datasets.
        try:
            await oracle_service.sync_text_index()
        except Exception as e:
            # Non-fatal: BM25 will work after next sync cycle
            logger.warning(f"Text index sync warning: {e}")

        all_tables = []
        all_figures = []
        for page in pages:
            for t in page.tables:
                all_tables.append(TableExtraction(
                    table_id=t.get("table_id", ""),
                    caption=t.get("caption", ""),
                    headers=t.get("headers", []),
                    rows=t.get("rows", []),
                    row_count=len(t.get("rows", [])),
                    semantic_summary=t.get("semantic_summary", ""),
                ))
            for fig in page.figures:
                all_figures.append(FigureExtraction(
                    figure_id=fig.get("figure_id", ""),
                    type=fig.get("type", "diagram"),
                    caption=fig.get("caption", ""),
                    semantic_summary=fig.get("semantic_summary", ""),
                    key_data_points=fig.get("key_data_points", []),
                ))

        dist = ChunkDistribution(
            text=sum(1 for c in chunks if c["chunk_type"] == "text"),
            table_row=sum(1 for c in chunks if c["chunk_type"] == "table_row"),
            figure=sum(1 for c in chunks if c["chunk_type"] == "figure"),
        )

        logger.info(f"[{doc_id}] Ingestion complete: {len(chunks)} chunks")
        return IngestResponse(
            doc_id=doc_id,
            doc_title=doc_title,
            pages_processed=len(pages),
            chunks_created=len(chunks),
            chunk_distribution=dist,
            tables=all_tables,
            figures=all_figures,
        )

    finally:
        try:
            os.remove(tmp_path)
            os.rmdir(tmp_dir)
        except OSError:
            pass
