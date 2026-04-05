"""
Oracle Database Service.

WHY: CRUD operations for KNOWLEDGE_DOCS, LITERATURE_CHUNKS, QUANTITATIVE_CHUNKS.
     Uses oracledb thin mode -- no Instant Client dependency.
     MDSK-RAG dual-source pattern: literature and quantitative data in separate tables.
RISK: CLOB insertion for chunk_text requires careful handling (P1 lesson).
INTERVIEW: "Applied MDSK-RAG dual-source collection from ACS JCIM paper."
"""

import os
import re
import json
import logging
import oracledb

logger = logging.getLogger(__name__)

ORACLE_HOST = os.getenv("ORACLE_HOST", "oracle")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_USER = os.getenv("ORACLE_USER", "fieldops")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "FREEPDB1")

_pool = None

# MDSK-RAG: chunk_type -> target table mapping
_LITERATURE_TYPES = {"text", "figure"}
_QUANTITATIVE_TYPES = {"table_row"}


async def _get_pool():
    """
    Get or create async connection pool.

    WHY: Connection pooling reduces per-query connection overhead.
    RISK: Pool exhaustion under concurrent load. max=5 sufficient for PoC.
    """
    global _pool
    if _pool is None:
        dsn = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"
        _pool = oracledb.create_pool_async(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=dsn,
            min=2,
            max=5,
        )
    return _pool


async def insert_doc(doc: dict) -> str:
    """
    Insert document metadata into KNOWLEDGE_DOCS.

    WHY: Tracks which documents have been ingested and VLM-processed.
         Deletes existing chunks from BOTH dual-source tables before re-ingestion.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # WHY: Delete existing doc + chunks to allow re-ingestion.
            #      Chunks in both tables have FK to docs, so delete chunks first.
            await cursor.execute(
                "DELETE FROM LITERATURE_CHUNKS WHERE doc_id = :1",
                [doc["doc_id"]],
            )
            await cursor.execute(
                "DELETE FROM QUANTITATIVE_CHUNKS WHERE doc_id = :1",
                [doc["doc_id"]],
            )
            await cursor.execute(
                "DELETE FROM KNOWLEDGE_DOCS WHERE doc_id = :1",
                [doc["doc_id"]],
            )
            await cursor.execute(
                """INSERT INTO KNOWLEDGE_DOCS
                   (doc_id, doc_title, doc_type, file_path, page_count, vlm_processed)
                   VALUES (:1, :2, :3, :4, :5, :6)""",
                [
                    doc["doc_id"],
                    doc["doc_title"],
                    doc["doc_type"],
                    doc.get("file_path", ""),
                    doc.get("page_count", 0),
                    1,
                ],
            )
            await conn.commit()
    logger.info(f"Inserted doc: {doc['doc_id']}")
    return doc["doc_id"]


async def insert_chunks(chunks: list[dict]) -> int:
    """
    Bulk insert chunks into dual-source tables (MDSK-RAG pattern).

    WHY: Routes chunks to LITERATURE_CHUNKS or QUANTITATIVE_CHUNKS based on chunk_type.
         text/figure -> literature, table_row -> quantitative.
    RISK: CLOB insertion needs setinputsizes for chunk_text column.
          VECTOR needs JSON string format for oracledb.
    INTERVIEW: "MDSK-RAG dual-source: literature and quantitative physically separated."
    """
    if not chunks:
        return 0

    lit_chunks = [c for c in chunks if c["chunk_type"] in _LITERATURE_TYPES]
    quant_chunks = [c for c in chunks if c["chunk_type"] in _QUANTITATIVE_TYPES]

    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Insert literature chunks (text, figure)
        if lit_chunks:
            async with conn.cursor() as cursor:
                cursor.setinputsizes(
                    None,  # chunk_id
                    None,  # doc_id
                    None,  # chunk_type
                    oracledb.DB_TYPE_CLOB,  # chunk_text
                    None,  # page_number
                    None,  # section_title
                    oracledb.DB_TYPE_VECTOR,  # embedding
                )
                rows = []
                for c in lit_chunks:
                    embedding = c.get("embedding")
                    if embedding is not None:
                        embedding = json.dumps(embedding)
                    rows.append([
                        c["chunk_id"],
                        c["doc_id"],
                        c["chunk_type"],
                        c["chunk_text"],
                        c.get("page_number"),
                        c.get("section_title", ""),
                        embedding,
                    ])
                await cursor.executemany(
                    """INSERT INTO LITERATURE_CHUNKS
                       (chunk_id, doc_id, chunk_type, chunk_text,
                        page_number, section_title, embedding)
                       VALUES (:1, :2, :3, :4, :5, :6, :7)""",
                    rows,
                )

        # Insert quantitative chunks (table_row)
        if quant_chunks:
            async with conn.cursor() as cursor:
                cursor.setinputsizes(
                    None,  # chunk_id
                    None,  # doc_id
                    None,  # chunk_type
                    oracledb.DB_TYPE_CLOB,  # chunk_text
                    None,  # page_number
                    None,  # table_id
                    oracledb.DB_TYPE_VECTOR,  # embedding
                )
                rows = []
                for c in quant_chunks:
                    embedding = c.get("embedding")
                    if embedding is not None:
                        embedding = json.dumps(embedding)
                    rows.append([
                        c["chunk_id"],
                        c["doc_id"],
                        c["chunk_type"],
                        c["chunk_text"],
                        c.get("page_number"),
                        c.get("table_id"),
                        embedding,
                    ])
                await cursor.executemany(
                    """INSERT INTO QUANTITATIVE_CHUNKS
                       (chunk_id, doc_id, chunk_type, chunk_text,
                        page_number, table_id, embedding)
                       VALUES (:1, :2, :3, :4, :5, :6, :7)""",
                    rows,
                )

        await conn.commit()

    count = len(chunks)
    logger.info(f"Inserted {count} chunks for doc '{chunks[0]['doc_id']}' "
                f"(literature: {len(lit_chunks)}, quantitative: {len(quant_chunks)})")
    return count


async def get_doc(doc_id: str) -> dict | None:
    """Get document metadata by doc_id."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT doc_id, doc_title, doc_type, file_path, page_count, vlm_processed "
                "FROM KNOWLEDGE_DOCS WHERE doc_id = :1",
                [doc_id],
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "doc_id": row[0],
                "doc_title": row[1],
                "doc_type": row[2],
                "file_path": row[3],
                "page_count": row[4],
                "vlm_processed": row[5],
            }


async def get_chunk_count(doc_id: str) -> int:
    """
    Count total chunks for a document across both dual-source tables.

    WHY: MDSK-RAG splits chunks into two tables; total = literature + quantitative.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """SELECT
                     (SELECT COUNT(*) FROM LITERATURE_CHUNKS WHERE doc_id = :1) +
                     (SELECT COUNT(*) FROM QUANTITATIVE_CHUNKS WHERE doc_id = :2)
                   FROM DUAL""",
                [doc_id, doc_id],
            )
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_chunk_distribution(doc_id: str) -> dict:
    """
    Count chunks by chunk_type across both dual-source tables.

    WHY: Aggregates distribution from LITERATURE_CHUNKS + QUANTITATIVE_CHUNKS.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """SELECT chunk_type, COUNT(*) FROM (
                     SELECT chunk_type FROM LITERATURE_CHUNKS WHERE doc_id = :1
                     UNION ALL
                     SELECT chunk_type FROM QUANTITATIVE_CHUNKS WHERE doc_id = :2
                   ) GROUP BY chunk_type""",
                [doc_id, doc_id],
            )
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}


async def vector_search(query_vector: list[float], max_results: int = 10) -> list:
    """
    Dual-source vector similarity search (MDSK-RAG pattern).

    WHY: Searches LITERATURE_CHUNKS and QUANTITATIVE_CHUNKS simultaneously via UNION ALL.
         Combined results ranked by cosine distance across both collections.
    RISK: HNSW index accuracy depends on TARGET ACCURACY setting (95%).
    INTERVIEW: "MDSK-RAG dual-source: literature + quantitative searched in parallel."
    """
    from schemas.search import SearchResult

    sql = """
        SELECT * FROM (
            SELECT c.chunk_id, c.chunk_type, c.chunk_text, c.page_number,
                   c.section_title, c.doc_id,
                   d.doc_title,
                   VECTOR_DISTANCE(c.embedding, :query_vec, COSINE) as distance
            FROM LITERATURE_CHUNKS c
            JOIN KNOWLEDGE_DOCS d ON c.doc_id = d.doc_id
            UNION ALL
            SELECT c.chunk_id, c.chunk_type, c.chunk_text, c.page_number,
                   NULL as section_title, c.doc_id,
                   d.doc_title,
                   VECTOR_DISTANCE(c.embedding, :query_vec2, COSINE) as distance
            FROM QUANTITATIVE_CHUNKS c
            JOIN KNOWLEDGE_DOCS d ON c.doc_id = d.doc_id
        )
        ORDER BY distance
        FETCH FIRST :max_results ROWS ONLY
    """

    pool = await _get_pool()
    results = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            cursor.setinputsizes(
                query_vec=oracledb.DB_TYPE_VECTOR,
                query_vec2=oracledb.DB_TYPE_VECTOR,
            )
            await cursor.execute(sql, {
                "query_vec": json.dumps(query_vector),
                "query_vec2": json.dumps(query_vector),
                "max_results": max_results,
            })
            rows = await cursor.fetchall()

            # WHY: AsyncLOB.read() is a coroutine — must await inside cursor context.
            #      LOB objects become invalid after cursor/connection close.
            for row in rows:
                chunk_text = row[2]
                if hasattr(chunk_text, "read"):
                    chunk_text = await chunk_text.read()
                results.append(SearchResult(
                    chunk_id=row[0],
                    chunk_type=row[1],
                    chunk_text=str(chunk_text),
                    page_number=row[3],
                    section_title=row[4] or "",
                    doc_id=row[5],
                    doc_title=row[6],
                    similarity=round(1.0 - float(row[7]), 4),
                    search_method="vector",
                ))
    return results


async def bm25_search(query_text: str, max_results: int = 10) -> list:
    """
    Dual-source BM25 full-text search (MDSK-RAG pattern).

    WHY: Searches both LITERATURE_CHUNKS and QUANTITATIVE_CHUNKS via UNION ALL.
         Exact keyword matching for material names, equipment IDs, chemical formulas.
    RISK: Oracle Text index (CTXSYS.CONTEXT) needs sync after INSERT.
    INTERVIEW: "BM25 catches what vector search misses -- exact terms like model numbers."
    """
    from schemas.search import SearchResult

    # WHY: Oracle Text CONTAINS treats space-separated words as exact phrase.
    #      Must join words with AND operator for multi-keyword matching.
    # RISK: Special chars (°, %, &) break CONTAINS syntax — strip them first.
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', query_text).strip()
    words = [w for w in cleaned.split() if len(w) >= 2]
    if not words:
        return []
    escaped_query = " AND ".join(words)

    sql = """
        SELECT * FROM (
            SELECT c.chunk_id, c.chunk_type, c.chunk_text, c.page_number,
                   c.section_title, c.doc_id,
                   d.doc_title,
                   SCORE(1) as relevance_score
            FROM LITERATURE_CHUNKS c
            JOIN KNOWLEDGE_DOCS d ON c.doc_id = d.doc_id
            WHERE CONTAINS(c.chunk_text, :query_text, 1) > 0
            UNION ALL
            SELECT c.chunk_id, c.chunk_type, c.chunk_text, c.page_number,
                   NULL as section_title, c.doc_id,
                   d.doc_title,
                   SCORE(1) as relevance_score
            FROM QUANTITATIVE_CHUNKS c
            JOIN KNOWLEDGE_DOCS d ON c.doc_id = d.doc_id
            WHERE CONTAINS(c.chunk_text, :query_text2, 1) > 0
        )
        ORDER BY relevance_score DESC
        FETCH FIRST :max_results ROWS ONLY
    """

    pool = await _get_pool()
    results = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, {
                "query_text": escaped_query,
                "query_text2": escaped_query,
                "max_results": max_results,
            })
            rows = await cursor.fetchall()

            # WHY: AsyncLOB.read() must be awaited inside cursor context.
            for row in rows:
                bm25_score = float(row[7]) if row[7] else 0
                normalized_similarity = min(0.80 + (bm25_score / 500), 1.0)
                chunk_text = row[2]
                if hasattr(chunk_text, "read"):
                    chunk_text = await chunk_text.read()
                results.append(SearchResult(
                    chunk_id=row[0],
                    chunk_type=row[1],
                    chunk_text=str(chunk_text),
                    page_number=row[3],
                    section_title=row[4] or "",
                    doc_id=row[5],
                    doc_title=row[6],
                    similarity=round(normalized_similarity, 4),
                    search_method="bm25",
                ))
    return results


async def sync_text_index():
    """
    Sync Oracle Text indexes for both dual-source tables.

    WHY: CTXSYS.CONTEXT index is not auto-synced on INSERT.
         Must call CTX_DDL.SYNC_INDEX for both literature and quantitative indexes.
    RISK: fieldops user needs CTXAPP role for CTX_DDL access.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "BEGIN CTX_DDL.SYNC_INDEX('idx_literature_text'); END;"
            )
            await cursor.execute(
                "BEGIN CTX_DDL.SYNC_INDEX('idx_quantitative_text'); END;"
            )
        await conn.commit()
