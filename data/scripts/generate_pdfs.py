"""
PDF generation from Markdown sources.

WHY: PDFs are the input format for VLM pipeline.
     Tables must render as actual HTML tables (not plain text).
     Figures must be embedded at correct positions.
RISK: Poor table rendering -> VLM cannot extract structured data.
INTERVIEW: "End-to-end pipeline: Markdown -> Figure -> PDF -> VLM -> Oracle."
"""

import os
import re
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(BASE_DIR, "figures")


class PaperPDF(FPDF):
    """Custom PDF with header/footer for academic-style documents."""

    def __init__(self, title="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_title = title
        # Use built-in fonts only (no TTF needed)

    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, self.doc_title, align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def parse_markdown_table(lines):
    """
    Parse markdown table lines into header + rows.

    WHY: Extract table data for structured PDF rendering.
         Returns (headers, rows) where each is a list of strings.
    """
    table_lines = [l for l in lines if l.strip().startswith("|")]
    if len(table_lines) < 3:
        return None, None

    def split_row(line):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        return cells

    headers = split_row(table_lines[0])
    # Skip separator line (index 1)
    rows = [split_row(l) for l in table_lines[2:]]
    return headers, rows


def render_table(pdf, headers, rows):
    """
    Render a table in the PDF with borders and shading.

    WHY: Structured table rendering critical for VLM extraction accuracy.
    """
    pdf.set_font("Helvetica", "B", 9)
    num_cols = len(headers)
    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_width = page_width / num_cols

    # Header row
    pdf.set_fill_color(220, 220, 240)
    for h in headers:
        pdf.cell(col_width, 7, _safe_latin1(h), border=1, fill=True, align="C")
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 9)
    for i, row in enumerate(rows):
        if i % 2 == 1:
            pdf.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        for cell in row:
            pdf.cell(col_width, 6, _safe_latin1(cell), border=1, fill=fill, align="C")
        pdf.ln()
    pdf.ln(4)


def render_markdown_to_pdf(md_path, pdf_path, figure_path=None, figure_after_text=None):
    """
    Convert a markdown file to PDF with tables and optional figure.

    WHY: Full pipeline from source markdown to VLM-ready PDF.
    RISK: Non-ASCII characters may fail with built-in fonts.
          Using latin-1 safe subset for compatibility.
    """
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Extract title from first heading
    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            break

    pdf = PaperPDF(title=title)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    figure_inserted = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and horizontal rules
        if not stripped or stripped.startswith("---"):
            pdf.ln(2)
            i += 1
            continue

        # Detect table block
        if stripped.startswith("|") and i + 2 < len(lines) and "---" in lines[i + 1]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            headers, rows = parse_markdown_table(table_lines)
            if headers and rows:
                render_table(pdf, headers, rows)
            continue

        # Main title (h1)
        if stripped.startswith("# ") and not stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 16)
            text = stripped.lstrip("# ").strip()
            text = _safe_latin1(text)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 8, text, align="C")
            pdf.ln(4)
            i += 1
            continue

        # Section heading (h2)
        if stripped.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            text = stripped.lstrip("# ").strip()
            text = _safe_latin1(text)
            pdf.set_x(pdf.l_margin)
            pdf.cell(0, 8, text)
            pdf.ln(6)
            i += 1
            continue

        # Subsection heading (h3)
        if stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            text = stripped.lstrip("# ").strip()
            text = _safe_latin1(text)
            pdf.set_x(pdf.l_margin)
            pdf.cell(0, 7, text)
            pdf.ln(5)
            i += 1
            continue

        # Bold metadata lines
        if stripped.startswith("**") and "**:" in stripped:
            pdf.set_font("Helvetica", "", 9)
            text = stripped.replace("**", "")
            text = _safe_latin1(text)
            if text.strip():
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 5, text)
            i += 1
            continue

        # Figure insertion trigger
        if (figure_path and not figure_inserted and figure_after_text
                and figure_after_text in stripped):
            # Render current line first
            pdf.set_font("Helvetica", "", 10)
            text = _safe_latin1(stripped.lstrip("- ").replace("**", ""))
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, text)
            # Insert figure
            if os.path.exists(figure_path):
                pdf.ln(4)
                img_width = pdf.w - pdf.l_margin - pdf.r_margin - 20
                pdf.image(figure_path, x=pdf.l_margin + 10, w=img_width)
                pdf.ln(4)
            figure_inserted = True
            i += 1
            continue

        # Regular paragraph text
        pdf.set_font("Helvetica", "", 10)
        text = stripped
        # Clean markdown formatting
        text = re.sub(r"^\s*[-*]\s+", "", text)       # bullet points
        text = re.sub(r"^\s*\d+\.\s+", "", text)      # numbered lists
        text = re.sub(r"^\s*>\s*", "", text)           # blockquotes
        text = text.replace("**", "").replace("*", "")
        text = _safe_latin1(text)
        if text.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, text)
        i += 1

    pdf.output(pdf_path)
    print(f"[OK] PDF saved: {pdf_path}")


def _safe_latin1(text):
    """
    Replace non-latin1 characters for fpdf2 built-in font compatibility.

    WHY: fpdf2 built-in fonts only support latin-1 encoding.
         Special characters must be transliterated.
    """
    replacements = {
        "\u2013": "-",   # en-dash
        "\u2014": "--",  # em-dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u00b0": "°",  # degree (latin-1 safe)
        "\u0394": "D",   # Delta
        "\u00b1": "+-",  # plus-minus
        "\u03b1": "a",   # alpha
        "\u03bc": "u",   # mu
        "\\*": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Final fallback: replace any remaining non-latin1 chars
    return text.encode("latin-1", errors="replace").decode("latin-1")


if __name__ == "__main__":
    print("=== FieldOps-AI: Generating PDFs ===")

    papers_dir = os.path.join(BASE_DIR, "papers")
    reports_dir = os.path.join(BASE_DIR, "reports")

    # Paper-A with Figure 1
    render_markdown_to_pdf(
        md_path=os.path.join(papers_dir, "paper-a-material-x-thermal-stability.md"),
        pdf_path=os.path.join(papers_dir, "paper-a-material-x-thermal-stability.pdf"),
        figure_path=os.path.join(FIGURES_DIR, "fig1_decomposition.png"),
        figure_after_text="See Figure 1",
    )

    # Paper-B with Figure 2
    render_markdown_to_pdf(
        md_path=os.path.join(papers_dir, "paper-b-equipment-a-mixing.md"),
        pdf_path=os.path.join(papers_dir, "paper-b-equipment-a-mixing.pdf"),
        figure_path=os.path.join(FIGURES_DIR, "fig2_rpm_vs_temp.png"),
        figure_after_text="See Figure 2",
    )

    # Report-A (no figure)
    render_markdown_to_pdf(
        md_path=os.path.join(reports_dir, "report-a-material-x-kneading.md"),
        pdf_path=os.path.join(reports_dir, "report-a-material-x-kneading.pdf"),
    )

    # Report-B (no figure)
    render_markdown_to_pdf(
        md_path=os.path.join(reports_dir, "report-b-material-y-grinding.md"),
        pdf_path=os.path.join(reports_dir, "report-b-material-y-grinding.pdf"),
    )

    print("=== Done: 4 PDFs generated ===")
