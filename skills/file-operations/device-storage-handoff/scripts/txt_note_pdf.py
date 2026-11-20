#!/usr/bin/env python3
"""txt_note_pdf.py — render a plain-text instruction sheet (.txt) to a clean A4 PDF.

Why this exists: Markdown → PDF (markdown + fpdf2.write_html) is the right path for .md reports,
but a hand-written plain-text note (rule lines, "BAHAGIAN …" headings, indented commands) has no
markdown to parse. This renderer walks the lines instead, so nothing is lost and no HTML
sanitizer can eat placeholder text.

Usage:
    python3 txt_note_pdf.py <input.txt> [output.pdf] [--title "JUDUL"]

Requirements: pip install fpdf2 pypdf   (fonts from $PREFIX/share/fonts/TTF on Termux)

Verify afterwards (never skip):
    python3 -c "from pypdf import PdfReader;r=PdfReader('<out>.pdf');t=''.join(p.extract_text() for p in r.pages);print(len(r.pages));print('URL' in t, 'password' in t)"
"""
from __future__ import annotations

import os
import sys

from fpdf import FPDF

FONT_DIR = os.path.join(os.environ.get("PREFIX", "/usr"), "share/fonts/TTF")
BODY_PT, CODE_PT, HEAD_PT = 10.5, 9.0, 12.0
MARGIN = 14


class Nota(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(120)
        self.cell(0, 6, f"{getattr(self, 'doc_title', 'Nota')}  ·  halaman {self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0)


def build(src: str, dst: str, title: str = "NOTA") -> None:
    lines = open(src, encoding="utf-8").read().splitlines()
    pdf = Nota(orientation="P", unit="mm", format="A4")
    pdf.doc_title = title
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=16)
    for style, fname in (("", "DejaVuSans.ttf"), ("B", "DejaVuSans-Bold.ttf")):
        pdf.add_font("DejaVu", style, os.path.join(FONT_DIR, fname))
    for style, fname in (("", "DejaVuSansMono.ttf"), ("B", "DejaVuSansMono-Bold.ttf")):
        pdf.add_font("Mono", style, os.path.join(FONT_DIR, fname))
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.add_page()

    def row(h: float, text: str, **kw) -> None:
        """Always reset x: a bare multi_cell(0, …) after a filled cell raises
        'Not enough horizontal space to render a single character'."""
        pdf.set_x(MARGIN)
        pdf.multi_cell(pdf.epw, h, text, **kw)

    pdf.set_font("DejaVu", "B", 15)
    row(8, title)
    pdf.ln(2)
    pdf.set_draw_color(180)
    pdf.line(MARGIN, pdf.get_y(), 210 - MARGIN, pdf.get_y())
    pdf.ln(4)

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            pdf.ln(2.2)
            continue
        if set(stripped) <= {"═", "="} and len(stripped) >= 4:
            pdf.set_draw_color(150)
            pdf.line(MARGIN, pdf.get_y(), 210 - MARGIN, pdf.get_y())
            pdf.ln(3)
            continue
        if set(stripped) <= {"-"} and len(stripped) >= 4:
            pdf.ln(0.8)
            continue
        if stripped.upper().startswith(("BAHAGIAN", "SECTION", "LANGKAH")):
            if pdf.get_y() > 250:
                pdf.add_page()
            pdf.ln(1.5)
            pdf.set_font("DejaVu", "B", HEAD_PT)
            pdf.set_fill_color(235, 238, 242)
            row(6.2, stripped, fill=True)
            pdf.ln(1.5)
            pdf.set_font("DejaVu", "", BODY_PT)
            continue
        if line.startswith("   ") or stripped.startswith(("~/", "sv ", "curl ", "hermes", "sudo ")):
            pdf.set_font("Mono", "", CODE_PT)
            pdf.set_fill_color(245, 246, 248)
            pdf.set_text_color(20, 60, 120)
            row(5.0, stripped, fill=True)
            pdf.set_text_color(0)
            pdf.set_font("DejaVu", "", BODY_PT)
            continue

        pdf.set_font("DejaVu", "", BODY_PT)
        row(5.6, stripped)

    pdf.output(dst)


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Render a plain-text note to PDF.")
    ap.add_argument("input", help="source .txt")
    ap.add_argument("output", nargs="?", help="destination .pdf (default: same stem)")
    ap.add_argument("--title", default="NOTA", help="header/footer title")
    ns = ap.parse_args(argv)

    src = os.path.expanduser(ns.input)
    dst = os.path.expanduser(ns.output) if ns.output else os.path.splitext(src)[0] + ".pdf"
    if not os.path.isfile(src):
        print(f"tiada fail: {src}")
        return 2
    build(src, dst, ns.title)
    print(f"PDF: {dst} ({os.path.getsize(dst)} bait)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
