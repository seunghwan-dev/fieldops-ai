"""
Smart Chunking Service.

WHY: Different chunk strategies for different content types.
     Text: section-level (~400 tokens). Table: row-level with headers.
     Figure: semantic summary as single chunk.
     MDSK-RAG: Each chunk tagged with destination (literature / quantitative).
RISK: Oversized chunks degrade retrieval precision. Undersized lose context.
INTERVIEW: "Three chunking strategies + MDSK-RAG dual-source routing."
"""

import logging
from schemas.knowledge import VLMPageResult

logger = logging.getLogger(__name__)

# Approximate tokens per character (English text)
CHARS_PER_TOKEN = 4
MAX_CHUNK_TOKENS = 400
MAX_CHUNK_CHARS = MAX_CHUNK_TOKENS * CHARS_PER_TOKEN


def _split_text_by_paragraphs(text: str, max_chars: int) -> list[str]:
    """
    Split text at paragraph boundaries, respecting max_chars limit.

    WHY: Paragraph-level splits preserve semantic coherence better
         than arbitrary character-level cuts.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) + 2 > max_chars:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def _extract_section_title(text: str) -> str:
    """
    Extract section title from chunk text if it starts with a heading pattern.

    WHY: Section title metadata improves retrieval context.
    """
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) < 200:
            return line
    return ""


def _chunk_text(text_content: str, doc_id: str, page_num: int, seq_start: int) -> tuple[list[dict], int]:
    """
    Chunk text content at paragraph boundaries (~400 tokens each).

    WHY: Section-level chunking preserves context for RAG retrieval.
    """
    if not text_content.strip():
        return [], seq_start

    parts = _split_text_by_paragraphs(text_content, MAX_CHUNK_CHARS)
    chunks = []
    seq = seq_start

    for part in parts:
        if not part.strip():
            continue
        seq += 1
        chunks.append({
            "chunk_id": f"{doc_id}_p{page_num}_c{seq}",
            "doc_id": doc_id,
            "chunk_type": "text",
            "chunk_text": part,
            "page_number": page_num,
            "section_title": _extract_section_title(part),
            "table_id": None,
        })

    return chunks, seq


def _chunk_table(table: dict, doc_id: str, page_num: int, seq_start: int) -> tuple[list[dict], int]:
    """
    Chunk table rows: header + each row = 1 chunk.

    WHY: Row-level chunking enables precise retrieval of individual data points.
         Format: "Table {id} | Header1: Value1 | Header2: Value2 | ..."
    INTERVIEW: "Table row chunking lets RAG find 'onset temp at 60rpm' directly."
    """
    table_id = table.get("table_id", "table_unknown")
    headers = table.get("headers", [])
    rows = table.get("rows", [])
    chunks = []
    seq = seq_start

    for row in rows:
        pairs = []
        for h, v in zip(headers, row):
            pairs.append(f"{h}: {v}")
        chunk_text = f"Table {table_id} | " + " | ".join(pairs)

        seq += 1
        chunks.append({
            "chunk_id": f"{doc_id}_p{page_num}_c{seq}",
            "doc_id": doc_id,
            "chunk_type": "table_row",
            "chunk_text": chunk_text,
            "page_number": page_num,
            "section_title": table.get("caption", ""),
            "table_id": table_id,
        })

    return chunks, seq


def _chunk_figure(figure: dict, doc_id: str, page_num: int, seq_start: int) -> tuple[list[dict], int]:
    """
    Chunk figure: semantic_summary + key_data_points = 1 chunk.

    WHY: Figure semantic summary enables retrieval of visual insights.
    """
    summary = figure.get("semantic_summary", "")
    key_points = figure.get("key_data_points", [])
    figure_id = figure.get("figure_id", "fig_unknown")

    parts = [summary]
    if key_points:
        parts.append("Key data points: " + "; ".join(key_points))
    chunk_text = " ".join(parts)

    if not chunk_text.strip():
        return [], seq_start

    seq = seq_start + 1
    chunk = {
        "chunk_id": f"{doc_id}_p{page_num}_c{seq}",
        "doc_id": doc_id,
        "chunk_type": "figure",
        "chunk_text": chunk_text,
        "page_number": page_num,
        "section_title": figure.get("caption", ""),
        "table_id": None,
    }
    return [chunk], seq


def chunk_pages(pages: list[VLMPageResult], doc_id: str) -> list[dict]:
    """
    Chunk all VLM page results into retrieval-ready chunks.

    WHY: Orchestrates text/table/figure chunking across all pages.
    RISK: Chunk count varies with VLM extraction quality.
          Expected: ~45-55 chunks for 4 FieldOps-AI documents.
    """
    all_chunks = []
    seq = 0

    for page in pages:
        if page.text_content.strip():
            text_chunks, seq = _chunk_text(
                page.text_content, doc_id, page.page_number, seq
            )
            all_chunks.extend(text_chunks)

        for table in page.tables:
            table_chunks, seq = _chunk_table(
                table, doc_id, page.page_number, seq
            )
            all_chunks.extend(table_chunks)

        for figure in page.figures:
            figure_chunks, seq = _chunk_figure(
                figure, doc_id, page.page_number, seq
            )
            all_chunks.extend(figure_chunks)

    logger.info(f"Doc '{doc_id}': {len(all_chunks)} chunks created "
                f"(text: {sum(1 for c in all_chunks if c['chunk_type'] == 'text')}, "
                f"table_row: {sum(1 for c in all_chunks if c['chunk_type'] == 'table_row')}, "
                f"figure: {sum(1 for c in all_chunks if c['chunk_type'] == 'figure')})")
    return all_chunks
