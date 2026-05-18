"""
Pydantic models for Knowledge Ingestion API.

WHY: Type-safe request/response models for VLM pipeline.
RISK: None. Standard Pydantic pattern.
INTERVIEW: "Explicit schemas make the API self-documenting via Swagger."
"""

from typing import Literal

from pydantic import BaseModel, field_validator


class TableExtraction(BaseModel):
    table_id: str
    caption: str = ""
    headers: list[str] = []
    rows: list[list[str]] = []
    row_count: int = 0
    semantic_summary: str = ""

    @field_validator("headers", mode="before")
    @classmethod
    def coerce_headers(cls, v):
        return [str(x) for x in v] if v else []

    @field_validator("rows", mode="before")
    @classmethod
    def coerce_rows(cls, v):
        return [[str(cell) for cell in row] for row in v] if v else []


class FigureExtraction(BaseModel):
    figure_id: str
    type: str = "diagram"  # line_chart, bar_chart, diagram
    caption: str = ""
    semantic_summary: str = ""
    key_data_points: list[str] = []


class ChunkDistribution(BaseModel):
    text: int = 0
    table_row: int = 0
    figure: int = 0


class IngestResponse(BaseModel):
    doc_id: str
    doc_title: str
    pages_processed: int
    chunks_created: int
    chunk_distribution: ChunkDistribution
    tables: list[TableExtraction] = []
    figures: list[FigureExtraction] = []
    # WHY: status indicates idempotency outcome:
    #   "new" = first ingestion (no prior doc_id)
    #   "updated" = same doc_id, different bytes (old chunks replaced)
    #   "unchanged" = same doc_id + same hash (VLM/embedding skipped, returned existing)
    # file_hash is SHA-256 of the raw uploaded bytes (byte-level identity).
    status: Literal["new", "updated", "unchanged"]
    file_hash: str  # SHA-256 hex digest (64 chars)


class VLMPageResult(BaseModel):
    page_number: int
    content_type: str = "text"  # text, table, figure, mixed
    text_content: str = ""
    tables: list[dict] = []
    figures: list[dict] = []
