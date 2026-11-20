#!/usr/bin/env python3
"""txt_to_pdf.py — turn a plain-text instruction note into a phone-readable PDF.

Why: a `.txt` attachment is often unopenable on a phone ("tak boleh buka", nothing
lands in the notes app). A PDF renders as a downloadable document instead.

Usage:
    python3 txt_to_pdf.py IN.txt [OUT.pdf]

Conventions in the input text (deliberately simple, no markdown parser):
    BAHAGIAN … / SECTION …   -> filled bold heading
    a line of only '=' or '─'/'═' -> horizontal rule
    a line of only '-'        -> ignored (underline of a heading)
    lines indented 3+ spaces, or starting with `hermes-up`/`sv `/`curl `/`~/`
                              -> monospace, tinted, shaded (commands)
    everything else           -> body text

Pitfalls encoded here (each one cost a run):
  * fpdf2 raises "Not enough horizontal space to render a single character" when
    multi_cell(w=0) is called with x already at the right margin (happens after a
    filled cell). Always set_x(left_margin) and pass epw explicitly — see row().
  * DejaVu fonts must be registered by path; the built-in core fonts are latin-1
    and will explode on '·', '→', '×', '—'.
  * alias_nb_pages() + a footer() override gives "page N/M" without bookkeeping.
"""
from __future__ import annotations

import os
import sys

from fpdf import FPDF

FONT_DIR = os.environ.get("PREFIX", "/data/data/com.termux/files/usr") + "/share/fonts/TTF"
MARGIN = 14
BODY_PT, CODE_PT, HEAD_PT = 10.5, 9.0, 12.0


class Nota(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(120)
        self.cell(0, 6, f"halaman {self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0)


def build(src: str, dst: str, title: str = "NOTA", subtitle: str = "") -> None:
    lines = open(src, encoding="utf-8").read().splitlines()
    pdf = Nota(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
    pdf.add_font("Mono", "", os.path.join(FONT_DIR, "DejaVuSansMono.ttf"))
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.add_page()

    def row(h: float, text: str, **kw) -> None:
        pdf.set_x(MARGIN)          # never rely on a previous cell's x
        pdf.multi_cell(pdf.epw, h, text, **kw)

    pdf.set_font("DejaVu", "B", 15)
    row(8, title)
    if subtitle:
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(90)
        row(5, subtitle)
        pdf.set_text_color(0)
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
        if set(stripped) <= {"═", "=", "─"} and len(stripped) >= 4:
            pdf.set_draw_color(150)
            pdf.line(MARGIN, pdf.get_y(), 210 - MARGIN, pdf.get_y())
            pdf.ln(3)
            continue
        if stripped.startswith(("BAHAGIAN", "SECTION")):
            if pdf.get_y() > 250:
                pdf.add_page()
            pdf.ln(1.5)
            pdf.set_font("DejaVu", "B", HEAD_PT)
            pdf.set_fill_color(235, 238, 242)
            row(6.2, stripped, fill=True)
            pdf.ln(1.5)
            pdf.set_font("DejaVu", "", BODY_PT)
            continue
        if set(stripped) <= {"-"} and len(stripped) >= 4:
            pdf.ln(0.8)
            continue
        if line.startswith("   ") or stripped.startswith(("hermes-up", "sv ", "curl ", "~/")):
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = os.path.expanduser(sys.argv[1])
    dst = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".pdf"
    build(src, dst)
    print(f"PDF: {dst} ({os.path.getsize(dst)} bait)")
