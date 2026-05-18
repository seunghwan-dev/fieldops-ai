"""
A. Core API Tests — Knowledge Ingest & Search (A03-A13).

WHY: Knowledge pipeline is the foundation.
     VLM ingestion (A03-A07) feeds Oracle DB.
     Hybrid search (A08-A13) validates RAG retrieval.
INTERVIEW: "VLM extracts tables and figures with semantic meaning, not just OCR text."
"""
import pytest
from unittest.mock import patch, AsyncMock
import io
import uuid

from schemas.knowledge import VLMPageResult


def _build_vlm_pages(mock_vlm_response):
    """
    Convert fixture dict into list[VLMPageResult] matching vlm_service.extract_from_pdf return type.

    WHY: extract_from_pdf returns list[VLMPageResult], not raw dict.
         Mock must match the real function signature for downstream chunking to work.
    """
    text_block = mock_vlm_response["text_blocks"][0]
    table = mock_vlm_response["tables"][0]
    figure = mock_vlm_response["figures"][0]

    pages = [
        VLMPageResult(
            page_number=1,
            content_type="text",
            text_content=text_block["content"],
        ),
        VLMPageResult(
            page_number=2,
            content_type="table",
            text_content="",
            tables=[{
                "table_id": "table_1",
                "caption": "Thermal decomposition data",
                "headers": table["headers"],
                "rows": table["rows"],
                "semantic_summary": "Onset temperature decreases with RPM.",
            }],
        ),
        VLMPageResult(
            page_number=3,
            content_type="figure",
            text_content="",
            figures=[{
                "figure_id": "fig_1",
                "type": "line_chart",
                "caption": figure["description"],
                "semantic_summary": figure["semantic_summary"],
                "key_data_points": ["onset ~180°C", "rapid above 200°C"],
            }],
        ),
    ]
    return pages


class TestKnowledgeIngest:
    """A03-A07: Knowledge ingestion (VLM mocked, Oracle+embedding real)."""

    def test_ingest_pdf_success(self, test_client, sample_pdf_path, mock_vlm_response):
        """
        A03: POST PDF -> 200, chunks_created > 0.

        WHY: Core ingestion endpoint. VLM mocked for determinism.
        PATCH TARGET: services.vlm_service.extract_from_pdf (called by knowledge.py line 93).
        """
        pages = _build_vlm_pages(mock_vlm_response)
        with patch("services.vlm_service.extract_from_pdf",
                   new_callable=AsyncMock, return_value=pages):
            with open(sample_pdf_path, "rb") as f:
                response = test_client.post(
                    "/api/v1/knowledge/ingest",
                    files={"file": ("paper_a.pdf", f, "application/pdf")}
                )
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_created"] > 0

    def test_ingest_returns_extraction(self, test_client, sample_pdf_path, mock_vlm_response):
        """A04: Response includes tables[] and figures[]."""
        pages = _build_vlm_pages(mock_vlm_response)
        # WHY: unique marker => file_hash differs => status="updated" path
        #      re-runs VLM, so tables/figures are populated. Without it the
        #      work-3 dedup short-circuit returns empty extraction.
        with open(sample_pdf_path, "rb") as f:
            content = f.read() + b"\n%run_id=test_ingest_returns_extraction\n"
        with patch("services.vlm_service.extract_from_pdf",
                   new_callable=AsyncMock, return_value=pages):
            response = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", content, "application/pdf")}
            )
        data = response.json()
        assert len(data["tables"]) >= 1 or len(data["figures"]) >= 1

    def test_ingest_table_extraction(self, test_client, sample_pdf_path, mock_vlm_response):
        """
        A05: Table has >= 4 column headers.

        WHY: VLM should extract structured table data.
        """
        pages = _build_vlm_pages(mock_vlm_response)
        # WHY: unique marker forces status="updated" so VLM re-runs and the
        #      response carries tables (work-3 dedup would short-circuit empty).
        with open(sample_pdf_path, "rb") as f:
            content = f.read() + b"\n%run_id=test_ingest_table_extraction\n"
        with patch("services.vlm_service.extract_from_pdf",
                   new_callable=AsyncMock, return_value=pages):
            response = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", content, "application/pdf")}
            )
        data = response.json()
        tables = data["tables"]
        assert len(tables) >= 1
        assert len(tables[0]["headers"]) >= 4

    def test_ingest_figure_semantic(self, test_client, sample_pdf_path, mock_vlm_response):
        """
        A06: Figure semantic_summary contains "200" or "thermal".

        WHY: VLM reads graph *meaning*, not just OCR text.
        INTERVIEW: "OCR reads letters. VLM reads meaning."
        """
        pages = _build_vlm_pages(mock_vlm_response)
        # WHY: unique marker forces status="updated" so VLM re-runs and the
        #      response carries figures (work-3 dedup would short-circuit empty).
        with open(sample_pdf_path, "rb") as f:
            content = f.read() + b"\n%run_id=test_ingest_figure_semantic\n"
        with patch("services.vlm_service.extract_from_pdf",
                   new_callable=AsyncMock, return_value=pages):
            response = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", content, "application/pdf")}
            )
        data = response.json()
        figures = data["figures"]
        assert len(figures) >= 1
        summary = figures[0]["semantic_summary"].lower()
        assert "200" in summary or "thermal" in summary

    def test_ingest_invalid_file(self, test_client):
        """
        A07: POST .txt -> 400.

        WHY: Only PDF supported. Validated at router level before VLM call.
        """
        fake_txt = io.BytesIO(b"This is not a PDF")
        response = test_client.post(
            "/api/v1/knowledge/ingest",
            files={"file": ("test.txt", fake_txt, "text/plain")}
        )
        assert response.status_code in [400, 415, 422]


class TestKnowledgeSearch:
    """A08-A13: Hybrid search (Vector + BM25 + RRF). Real Oracle + e5-large."""

    def test_search_returns_results(self, test_client):
        """A08: "Material X safe temperature" -> results >= 1."""
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X safe temperature"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) >= 1

    def test_search_top_similarity(self, test_client):
        """
        A09: Top result similarity >= 0.80.

        INTERVIEW: "Empirical calibration: design 0.75 -> actual 0.80."
        """
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X safe temperature"}
        )
        data = response.json()
        assert len(data["results"]) >= 1
        assert data["results"][0]["similarity"] >= 0.80

    def test_search_source_citation(self, test_client):
        """A10: Results include "paper-a" source."""
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X safe temperature"}
        )
        data = response.json()
        results_str = str(data["results"]).lower()
        assert "paper-a" in results_str or "paper_a" in results_str

    def test_search_answer_generated(self, test_client):
        """
        A11: AI answer >= 50 characters.

        WHY: RAG synthesizes answer, not just lists results.
        """
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X safe temperature"}
        )
        data = response.json()
        assert len(data["answer"]) >= 50

    def test_search_table_row_hit(self, test_client):
        """A12: "Material X 60rpm onset" -> table chunk in results."""
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X 60rpm onset"}
        )
        data = response.json()
        assert "table" in str(data).lower()

    def test_search_no_results(self, test_client):
        """
        A13: "quantum physics unrelated" -> empty results.

        WHY: Threshold 0.80 should filter irrelevant queries.
        """
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "quantum physics unrelated topic"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 0


class TestKnowledgeIngestDedup:
    """
    A14-A16: SHA-256 based deduplication / idempotent re-ingestion.

    WHY: Re-uploading the SAME bytes must skip the expensive VLM/embedding
         pipeline and return status="unchanged". A modified file must re-run it.
    NOTE: test_client is module-scoped over a PERSISTENT Oracle volume, so each
          test injects a per-run uuid nonce into the file bytes + filename.
          This guarantees a novel hash/doc_id, making call_count deterministic
          across repeated pytest runs.
    PATCH TARGET: services.vlm_service.extract_from_pdf (knowledge.py pipeline).
    """

    @classmethod
    def teardown_class(cls):
        """
        Remove dedup-* docs so they don't pollute the shared persistent Oracle
        corpus that sibling search tests (e.g. A12 test_search_table_row_hit)
        depend on.

        WHY: Uses a SYNCHRONOUS oracledb connection (same pattern as
             main.py /readiness) — NOT the async pool. asyncio.run() here would
             create a new event loop and clash with the module-scoped
             test_client's loop (conftest's documented pitfall).
        """
        import os
        import oracledb

        dsn = (f"{os.getenv('ORACLE_HOST', 'oracle')}:"
               f"{int(os.getenv('ORACLE_PORT', '1521'))}/"
               f"{os.getenv('ORACLE_SERVICE', 'FREEPDB1')}")
        conn = oracledb.connect(
            user=os.getenv("ORACLE_USER", "fieldops"),
            password=os.getenv("ORACLE_PASSWORD", ""),
            dsn=dsn,
        )
        try:
            cur = conn.cursor()
            # FK order: chunks (both dual-source tables) before docs.
            cur.execute("DELETE FROM LITERATURE_CHUNKS WHERE doc_id LIKE 'dedup-%'")
            cur.execute("DELETE FROM QUANTITATIVE_CHUNKS WHERE doc_id LIKE 'dedup-%'")
            cur.execute("DELETE FROM KNOWLEDGE_DOCS WHERE doc_id LIKE 'dedup-%'")
            conn.commit()
        finally:
            conn.close()

    def test_ingest_returns_status_new(self, test_client, sample_pdf_path, mock_vlm_response):
        """A14: First ingest of a fresh file -> status='new', 64-hex file_hash."""
        pages = _build_vlm_pages(mock_vlm_response)
        nonce = uuid.uuid4().hex
        with open(sample_pdf_path, "rb") as f:
            content = f.read() + f"\n%nonce={nonce}\n".encode()
        with patch("services.vlm_service.extract_from_pdf",
                   new_callable=AsyncMock, return_value=pages):
            response = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": (f"dedup_new_{nonce}.pdf", content, "application/pdf")},
            )
        assert response.status_code == 200
        data = response.json()
        # WHY: unique nonce filename => doc_id never seen before => "new".
        assert data["status"] == "new"
        assert len(data["file_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in data["file_hash"])

    def test_ingest_duplicate_returns_unchanged(self, test_client, sample_pdf_path, mock_vlm_response):
        """A15: Same bytes uploaded twice -> 2nd is 'unchanged', VLM skipped."""
        pages = _build_vlm_pages(mock_vlm_response)
        nonce = uuid.uuid4().hex
        # WHY: per-run nonce => the first upload's hash is guaranteed novel even
        #      on a persistent volume, so VLM call_count is deterministic.
        with open(sample_pdf_path, "rb") as f:
            content = f.read() + f"\n%nonce={nonce}\n".encode()
        fname = f"dedup_same_{nonce}.pdf"
        with patch("services.vlm_service.extract_from_pdf",
                   new_callable=AsyncMock, return_value=pages) as mock_vlm:
            r1 = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": (fname, content, "application/pdf")},
            )
            assert r1.status_code == 200
            r2 = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": (fname, content, "application/pdf")},
            )
            assert r2.status_code == 200
        assert r2.json()["status"] == "unchanged"
        assert r2.json()["file_hash"] == r1.json()["file_hash"]
        # VLM ran only for r1; r2 short-circuited before the pipeline.
        assert mock_vlm.call_count == 1

    def test_ingest_modified_returns_updated(self, test_client, sample_pdf_path, mock_vlm_response):
        """A16: Modified bytes (same filename) -> 'updated', VLM re-runs."""
        pages = _build_vlm_pages(mock_vlm_response)
        nonce = uuid.uuid4().hex
        with open(sample_pdf_path, "rb") as f:
            original = f.read() + f"\n%nonce={nonce}\n".encode()
        modified = original + b"\n%modified for test\n"  # SHA-256 differs
        fname = f"dedup_mod_{nonce}.pdf"
        with patch("services.vlm_service.extract_from_pdf",
                   new_callable=AsyncMock, return_value=pages) as mock_vlm:
            r1 = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": (fname, original, "application/pdf")},
            )
            assert r1.status_code == 200
            r2 = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": (fname, modified, "application/pdf")},
            )
            assert r2.status_code == 200
        assert r2.json()["status"] == "updated"
        assert r2.json()["file_hash"] != r1.json()["file_hash"]
        # VLM ran for both r1 (new) and r2 (updated).
        assert mock_vlm.call_count == 2
