"""
Batch ingestion script -- loads all PDFs into Oracle via /api/v1/knowledge/ingest.

WHY: One-command data initialization. Run after docker compose up.
RISK: VLM API calls take ~30s per page. 4 PDFs x ~6 pages = ~12 min total.
INTERVIEW: "Separated data generation from ingestion for reproducibility."
"""

import os
import sys
import time
from pathlib import Path
import httpx

API_URL = os.getenv("FIELDOPS_API_URL", "http://localhost:8000")
INGEST_ENDPOINT = f"{API_URL}/api/v1/knowledge/ingest"

BASE_DIR = Path(__file__).resolve().parent.parent


def find_pdfs() -> list[Path]:
    """Find all PDFs in papers/ and reports/ directories."""
    pdfs = []
    for subdir in ["papers", "reports"]:
        pdf_dir = BASE_DIR / subdir
        if pdf_dir.exists():
            pdfs.extend(sorted(pdf_dir.glob("*.pdf")))
    return pdfs


def ingest_one(pdf_path: Path, index: int, total: int) -> dict | None:
    """
    Ingest a single PDF via the API.

    WHY: Per-file ingestion with progress reporting.
    RISK: 5-minute timeout per PDF to account for VLM processing time.
    """
    print(f"[{index}/{total}] Ingesting {pdf_path.name}...")
    start = time.time()

    try:
        with httpx.Client(timeout=300.0) as client:
            with open(pdf_path, "rb") as f:
                resp = client.post(
                    INGEST_ENDPOINT,
                    files={"file": (pdf_path.name, f, "application/pdf")},
                )

            elapsed = time.time() - start

            if resp.status_code == 200:
                data = resp.json()
                dist = data.get("chunk_distribution", {})
                print(f"  OK ({elapsed:.1f}s) | doc_id: {data['doc_id']} | "
                      f"chunks: {data['chunks_created']} "
                      f"(text={dist.get('text', 0)}, "
                      f"table_row={dist.get('table_row', 0)}, "
                      f"figure={dist.get('figure', 0)})")
                return data
            else:
                print(f"  FAIL ({elapsed:.1f}s) | status: {resp.status_code} | "
                      f"detail: {resp.text[:200]}")
                return None

    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR ({elapsed:.1f}s) | {e}")
        return None


def main():
    print("=== FieldOps-AI: Batch Ingestion ===")
    print(f"API endpoint: {INGEST_ENDPOINT}")
    print()

    pdfs = find_pdfs()
    if not pdfs:
        print("ERROR: No PDF files found in data/papers/ or data/reports/")
        sys.exit(1)

    print(f"Found {len(pdfs)} PDFs:")
    for p in pdfs:
        print(f"  - {p.name}")
    print()

    total_start = time.time()
    results = []
    for i, pdf in enumerate(pdfs, 1):
        result = ingest_one(pdf, i, len(pdfs))
        results.append(result)
        print()

    total_elapsed = time.time() - total_start
    successful = [r for r in results if r is not None]
    total_chunks = sum(r["chunks_created"] for r in successful)

    print("=== Summary ===")
    print(f"Documents: {len(successful)}/{len(pdfs)} succeeded")
    print(f"Total chunks: {total_chunks}")
    print(f"Total time: {total_elapsed:.1f}s")
    print("=== Done ===")


if __name__ == "__main__":
    main()
