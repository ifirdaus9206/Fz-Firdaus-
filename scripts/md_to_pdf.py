#!/data/data/com.termux/files/usr/bin/env python3
# md_to_pdf.py — Markdown -> PDF untuk gudang telefon (Termux Android, NO ROOT).
# Tiada pandoc/LaTeX: guna `markdown` -> HTML, kemudian fpdf2 write_html.
# Font DejaVu WAJIB (aksara → … — · tiada dalam font core PDF).
#
# Guna:
#   python3 md_to_pdf.py <input.md> <output.pdf> [--tajuk TAJUK]
#
# Prinsip: SETIAP blok dirender dalam try/except. Kalau write_html gagal pada
# sesuatu tag, blok itu jatuh ke teks biasa — PDF mesti tetap terhasil.

import argparse
import os
import re
import sys
from html.parser import HTMLParser

import markdown
from fpdf import FPDF
from fpdf.enums import WrapMode
from fpdf.fonts import FontFace

FONT_DIR = "/data/data/com.termux/files/usr/share/fonts/TTF"
DEJAVU = os.path.join(FONT_DIR, "DejaVuSans.ttf")
DEJAVU_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
DEJAVU_I = os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf")
DEJAVU_BI = os.path.join(FONT_DIR, "DejaVuSans-BoldOblique.ttf")
MONO = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
MONO_B = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")

JUDUL_DOKUMEN = ""


# --------------------------------------------------------------------------- #
# Utiliti teks
# --------------------------------------------------------------------------- #
class _Teks(HTMLParser):
    """Buang tag, kekalkan teks (untuk fallback teks biasa)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bahagian = []

    def handle_data(self, d):
        self.bahagian.append(d)

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "li", "tr", "h1", "h2", "h3", "h4"):
            self.bahagian.append(" ")

    def handle_endtag(self, tag):
        if tag in ("p", "li", "tr", "h1", "h2", "h3", "h4"):
            self.bahagian.append(" ")


def teks_biasa(s):
    p = _Teks()
    try:
        p.feed(s)
        p.close()
        out = "".join(p.bahagian)
    except Exception:
        out = re.sub(r"<[^>]+>", " ", s)
    out = out.replace("\u00a0", " ")
    return re.sub(r"[ \t]+", " ", out).strip()


def pecah_token(s, had=26):
    """Tambah ruang dalam token terlalu panjang (URL) supaya tak melimpah."""
    def _f(m):
        t = m.group(0)
        if len(t) <= had:
            return t
        return " ".join(t[i:i + had] for i in range(0, len(t), had))
    return re.sub(r"\S{%d,}" % (had + 1), _f, s)


def bersih_inline(s):
    """Normalisasi HTML inline kepada set tag yang fpdf2 tahu render."""
    s = re.sub(r"<\s*(strong|b)\s*>", "<b>", s, flags=re.I)
    s = re.sub(r"<\s*/\s*(strong|b)\s*>", "</b>", s, flags=re.I)
    s = re.sub(r"<\s*(em|i)\s*>", "<i>", s, flags=re.I)
    s = re.sub(r"<\s*/\s*(em|i)\s*>", "</i>", s, flags=re.I)
    s = re.sub(r"<\s*(del|s|strike)\s*>", "", s, flags=re.I)
    s = re.sub(r"<\s*/\s*(del|s|strike)\s*>", "", s, flags=re.I)
    # <code> inline -> teks biasa (font mono melalui write_html tak selamat unicode)
    s = re.sub(r"<\s*/?\s*code[^>]*>", "", s, flags=re.I)
    s = re.sub(r"<\s*/?\s*(span|div|small|sup|sub|mark|kbd|samp|var|abbr)[^>]*>", "", s,
               flags=re.I)
    # pautan -> teks + URL dalam kurungan
    def _a(m):
        href = (m.group(1) or "").strip().strip('"').strip("'")
        teks = m.group(2)
        if not href or href.startswith("#") or href.startswith("mailto:"):
            return teks
        if teks_biasa(teks).strip().rstrip("/") == href.strip().rstrip("/"):
            return f'<a href="{href}">{teks}</a>'
        return f'<a href="{href}">{teks}</a> ({href})'
    s = re.sub(r'<a\s+[^>]*href\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]+))[^>]*>(.*?)</a>',
               lambda m: _a(_A(m)), s, flags=re.I | re.S)
    s = re.sub(r"<br\s*/?>", "<br>", s, flags=re.I)
    # Teks literal seperti <nama> (asalnya dalam backtick/kod) BUKAN tag:
    # escape semua '<' yang tidak memulakan tag yang kita sokong.
    s = re.sub(r"<(?!/?(?:b|i|u|br|a)\b)", "&lt;", s, flags=re.I)
    return s.strip()


class _A:
    """Pembantu padanan <a> (kumpulan: 1=href penuh, 2/3/4 varian, 5=teks)."""

    def __init__(self, m):
        self._m = m

    def group(self, i):
        if i == 1:
            g = self._m.group(1) or ""
            return g
        if i == 2:
            return self._m.group(2) or self._m.group(3) or self._m.group(4) or ""
        return self._m.group(5) if i == 5 else ""


# --------------------------------------------------------------------------- #
# Parser HTML -> senarai blok
# --------------------------------------------------------------------------- #
BLOK = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "pre",
        "blockquote", "table", "hr"}


class ParserBlok(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blok = []
        self.buf = None          # buffer html blok semasa
        self.buf_tag = None
        self.pre = None          # buffer teks mentah <pre>
        self.senarai = []        # stack konteks senarai
        self.item = []           # stack item senarai {level, buf}
        self.jadual = None
        self.baris = None
        self.sel = None
        self.sel_tag = None
        self.ada_th = False
        self.quote = None
        self.quote_kedalaman = 0

    # -- helper --
    def _tutup_buf(self):
        if self.buf is not None and self.buf_tag:
            html = "".join(self.buf).strip()
            if html:
                self.blok.append({"jenis": "teks", "tag": self.buf_tag, "html": html})
        self.buf = None
        self.buf_tag = None

    # -- HTMLParser --
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.pre is not None:
            return
        if self.quote is not None:
            if tag == "blockquote":
                self.quote_kedalaman += 1
            self.quote.append(self.get_starttag_text() or f"<{tag}>")
            return
        if self.jadual is not None:
            if tag == "tr":
                self.baris = []
            elif tag in ("td", "th"):
                self.sel = []
                self.sel_tag = tag
                if tag == "th":
                    self.ada_th = True
            elif tag == "br" and self.sel is not None:
                self.sel.append(" ")
            return

        if tag == "pre":
            self._tutup_buf()
            self.pre = []
            return
        if tag == "table":
            self._tutup_buf()
            self.jadual = []
            self.ada_th = False
            return
        if tag == "blockquote":
            self._tutup_buf()
            self.quote = []
            self.quote_kedalaman = 1
            return
        if tag == "hr":
            self._tutup_buf()
            self.blok.append({"jenis": "hr"})
            return
        if tag in ("ul", "ol"):
            # item induk yang belum siap mesti didahulukan
            if self.item:
                it = self.item[-1]
                if "".join(it["buf"]).strip():
                    self.senarai[-1]["item"].append(
                        {"level": it["level"], "html": "".join(it["buf"]).strip()})
                    it["buf"] = []
            self._tutup_buf()
            self.senarai.append({"tag": tag, "item": [], "n": 0})
            return
        if tag == "li":
            if self.senarai:
                self.item.append({"level": len(self.senarai) - 1, "buf": []})
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self._tutup_buf()
            self.buf = []
            self.buf_tag = tag
            return
        # inline
        if self.buf is not None:
            self.buf.append(self.get_starttag_text() or f"<{tag}>")
        elif self.senarai and self.item:
            self.item[-1]["buf"].append(self.get_starttag_text() or f"<{tag}>")

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if self.pre is not None:
            return
        if self.quote is not None:
            self.quote.append(self.get_starttag_text() or f"<{tag}/>")
            return
        if self.jadual is not None:
            if tag == "br" and self.sel is not None:
                self.sel.append(" ")
            return
        if tag == "hr":
            self.blok.append({"jenis": "hr"})
        elif tag == "br":
            if self.buf is not None:
                self.buf.append("<br>")
            elif self.senarai and self.item:
                self.item[-1]["buf"].append("<br>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.pre is not None:
            if tag == "pre":
                self.blok.append({"jenis": "kod", "teks": "".join(self.pre)})
                self.pre = None
            return
        if self.quote is not None:
            if tag == "blockquote":
                self.quote_kedalaman -= 1
                if self.quote_kedalaman <= 0:
                    html = "".join(self.quote)
                    self.quote = None
                    para = re.findall(r"<p[^>]*>(.*?)</p>", html, re.S)
                    if not para:
                        para = [html]
                    self.blok.append({"jenis": "petikan", "para": para})
                else:
                    self.quote.append(f"</{tag}>")
            else:
                self.quote.append(f"</{tag}>")
            return
        if self.jadual is not None:
            if tag in ("td", "th"):
                if self.sel is not None:
                    self.baris = self.baris if self.baris is not None else []
                    self.baris.append(teks_biasa("".join(self.sel)))
                self.sel = None
            elif tag == "tr":
                if self.baris:
                    self.jadual.append(self.baris)
                self.baris = None
            elif tag == "table":
                if self.jadual:
                    self.blok.append({"jenis": "jadual", "baris": self.jadual,
                                      "kepala": self.ada_th or len(self.jadual) > 1})
                self.jadual = None
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self._tutup_buf()
            return
        if tag == "li":
            if self.item:
                it = self.item.pop()
                html = "".join(it["buf"]).strip()
                if html and self.senarai:
                    self.senarai[-1]["item"].append({"level": it["level"], "html": html})
            return
        if tag in ("ul", "ol"):
            if self.senarai:
                konteks = self.senarai.pop()
                if self.senarai:
                    self.senarai[-1]["item"].extend(konteks["item"])
                else:
                    self.blok.append({"jenis": "senarai", "tag": konteks["tag"],
                                      "item": konteks["item"]})
            return
        if self.buf is not None:
            self.buf.append(f"</{tag}>")
        elif self.senarai and self.item:
            self.item[-1]["buf"].append(f"</{tag}>")

    def handle_data(self, data):
        if self.pre is not None:
            self.pre.append(data)
            return
        if self.quote is not None:
            self.quote.append(data)
            return
        if self.jadual is not None:
            if self.sel is not None:
                self.sel.append(data)
            return
        if self.buf is not None:
            self.buf.append(data)
        elif self.senarai and self.item:
            self.item[-1]["buf"].append(data)

    def tutup(self):
        try:
            self.close()
        except Exception:
            pass
        if self.pre is not None:
            self.blok.append({"jenis": "kod", "teks": "".join(self.pre)})
            self.pre = None
        if self.jadual:
            self.blok.append({"jenis": "jadual", "baris": self.jadual,
                              "kepala": self.ada_th or len(self.jadual) > 1})
            self.jadual = None
        self._tutup_buf()
        if self.senarai:
            konteks = self.senarai[0]
            if konteks["item"]:
                self.blok.append({"jenis": "senarai", "tag": konteks["tag"],
                                  "item": konteks["item"]})
            self.senarai = []
        return self.blok


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
class PDFUIM(FPDF):
    def __init__(self, nama_fail):
        super().__init__(format="A4", unit="mm")
        self.nama_fail = nama_fail
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, 20)
        self.set_title(JUDUL_DOKUMEN or nama_fail)
        self.set_creator("Hermes UIM md_to_pdf")
        self.add_font("DejaVu", "", DEJAVU)
        self.add_font("DejaVu", "B", DEJAVU_B)
        self.add_font("DejaVu", "I", DEJAVU_I)
        self.add_font("DejaVu", "BI", DEJAVU_BI)
        self.add_font("DejaVuMono", "", MONO)
        self.add_font("DejaVuMono", "B", MONO_B)
        self.set_font("DejaVu", "", 10)

    # footer setiap halaman
    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f"UIM · {self.nama_fail} · halaman {self.page_no()}",
                  align="C")
        self.set_text_color(0, 0, 0)

    # -- helper --
    def ruang(self, tinggi):
        if self.get_y() + tinggi > self.page_break_trigger:
            self.add_page()

    def _font(self, gaya="", saiz=10, mono=False):
        self.set_font("DejaVuMono" if mono else "DejaVu", gaya, saiz)

    def tulis_html(self, html, saiz=10, gaya="", align="J", tinggi=5.2, inden=0.0):
        """write_html dengan fallback teks biasa."""
        html = bersih_inline(html)
        if not html:
            return
        x0 = self.l_margin + inden
        self._font(gaya, saiz)
        self.set_x(x0)
        try:
            self.write_html(html, align=align)
        except Exception:
            # jatuh ke teks biasa — jangan crash
            self._font(gaya, saiz)
            self.set_x(x0)
            lebar = self.epw - inden
            self.multi_cell(lebar, tinggi, pecah_token(teks_biasa(html)),
                            align=align, wrapmode=WrapMode.CHAR)
        self._font("", 10)

    # -- blok --
    def blok_teks(self, tag, html):
        saiz = {"h1": 17, "h2": 14, "h3": 12, "h4": 10.8, "h5": 10.5, "h6": 10}[tag] \
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6") else 10
        tinggi = saiz * 0.55 + 2.4
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.ruang(tinggi + 6)
            self.ln(2.2)
            self.set_text_color(20, 20, 20)
            self.tulis_html(html, saiz=saiz, gaya="B", align="L", tinggi=tinggi)
            self.set_text_color(0, 0, 0)
            if tag == "h1":
                y = self.get_y() + 1
                self.set_draw_color(180, 180, 180)
                self.line(self.l_margin, y, self.l_margin + self.epw, y)
                self.ln(2.4)
            else:
                self.ln(1.2)
        else:
            self.ruang(tinggi + 2)
            self.tulis_html(html, saiz=10, align="J", tinggi=5.2)
            self.ln(1.9)

    def blok_senarai(self, tag, item):
        self.ruang(8)
        for it in item:
            inden = 5.0 + 5.0 * it["level"]
            self.ruang(7)
            y0 = self.get_y()
            x_teks = self.l_margin + inden
            self._font("", 10)
            penanda = "•" if it["level"] == 0 else "–"
            self.set_xy(self.l_margin + inden - 4.5, y0)
            self.cell(4, 5.2, penanda, align="R")
            self.set_xy(x_teks, y0)
            lebar = self.epw - inden
            html = bersih_inline(it["html"])
            try:
                self.write_html(html, align="J")
            except Exception:
                self._font("", 10)
                self.set_xy(x_teks, y0)
                self.multi_cell(lebar, 5.2, pecah_token(teks_biasa(html)),
                                align="J", wrapmode=WrapMode.CHAR)
            self._font("", 10)
            self.ln(0.9)
        self.ln(1.6)

    def blok_senarai_bernombor(self, item):
        self.ruang(8)
        kira = {}
        for it in item:
            lvl = it["level"]
            kira[lvl] = kira.get(lvl, 0) + 1
            inden = 5.0 + 5.0 * lvl
            self.ruang(7)
            y0 = self.get_y()
            x_teks = self.l_margin + inden
            self._font("", 10)
            self.set_xy(self.l_margin + inden - 8.0, y0)
            self.cell(7.5, 5.2, f"{kira[lvl]}.", align="R")
            self.set_xy(x_teks, y0)
            html = bersih_inline(it["html"])
            try:
                self.write_html(html, align="J")
            except Exception:
                self._font("", 10)
                self.set_xy(x_teks, y0)
                self.multi_cell(self.epw - inden, 5.2,
                                pecah_token(teks_biasa(html)),
                                align="J", wrapmode=WrapMode.CHAR)
            self._font("", 10)
            self.ln(0.9)
        self.ln(1.6)

    def blok_kod(self, teks):
        teks = teks.rstrip("\n")
        if not teks.strip():
            return
        self._font("", 8, mono=True)
        baris = teks.split("\n")
        tinggi_baris = 4.3
        # anggar tinggi (untuk elak kod terpotong di hujung halaman)
        anggar = min(len(baris) * tinggi_baris + 4, 120)
        self.ruang(anggar)
        x0 = self.l_margin
        y0 = self.get_y()
        halaman0 = self.page_no()
        self.set_fill_color(242, 242, 242)
        self.set_left_margin(x0 + 2.5)
        self.set_x(x0 + 2.5)
        try:
            self.multi_cell(self.epw - 5, tinggi_baris, teks, border=0, fill=True,
                            align="L", wrapmode=WrapMode.WORD)
        except Exception:
            self.set_x(x0 + 2.5)
            self.multi_cell(self.epw - 5, tinggi_baris, teks, border=0, fill=True,
                            align="L", wrapmode=WrapMode.CHAR)
        self.set_left_margin(x0)
        if self.page_no() == halaman0:
            self.set_draw_color(205, 205, 205)
            self.rect(x0, y0 - 1.2, self.epw, self.get_y() - y0 + 2.4)
        self.ln(3.0)
        self._font("", 10)

    def blok_petikan(self, para):
        for p in para:
            teks = bersih_inline(p)
            if not teks.strip():
                continue
            self.ruang(8)
            y0 = self.get_y()
            self.set_draw_color(150, 150, 150)
            self.set_left_margin(self.l_margin + 4)
            self.set_x(self.l_margin + 4)
            self.set_text_color(70, 70, 70)
            self.tulis_html(teks, saiz=9.5, gaya="I", align="L", tinggi=4.9,
                            inden=4)
            self.set_text_color(0, 0, 0)
            y1 = self.get_y()
            self.set_left_margin(15)
            self.set_draw_color(170, 170, 170)
            self.set_line_width(0.7)
            self.line(self.l_margin + 1.2, y0, self.l_margin + 1.2, max(y1 - 1, y0 + 2))
            self.set_line_width(0.2)
            self.ln(1.4)
        self.ln(1.0)

    def blok_jadual(self, baris, kepala=True):
        if not baris:
            return
        ncol = max(len(r) for r in baris)
        baris = [r + [""] * (ncol - len(r)) for r in baris]
        # lebar lajur berkadar dengan panjang kandungan (min 11mm)
        bobot = []
        for c in range(ncol):
            panjang = max(len(r[c]) for r in baris)
            bobot.append(max(6, min(panjang, 34)))
        jumlah = sum(bobot)
        lebar = [max(11.0, self.epw * b / jumlah) for b in bobot]
        skala = self.epw / sum(lebar)
        lebar = [w * skala for w in lebar]

        self.ruang(14)
        self._font("", 8.2)
        self.set_draw_color(160, 160, 160)
        self.set_line_width(0.25)
        try:
            with self.table(col_widths=lebar,
                            borders_layout="ALL",
                            first_row_as_headings=kepala,
                            headings_style=FontFace(emphasis="BOLD",
                                                    fill_color=(233, 233, 233)),
                            text_align="LEFT",
                            line_height=4.4,
                            padding=1.3,
                            wrapmode=WrapMode.WORD) as t:
                for r in baris:
                    row = t.row()
                    for c in r:
                        row.cell(pecah_token(c, 30))
        except Exception:
            # fallback: teks biasa berkotak
            for r in baris:
                self._font("", 8)
                self.multi_cell(self.epw, 4.6, " | ".join(r), border=1,
                                wrapmode=WrapMode.CHAR)
        self.set_line_width(0.2)
        self.ln(3.0)
        self._font("", 10)

    def garisan(self):
        self.ruang(8)
        self.ln(2)
        y = self.get_y()
        self.set_draw_color(190, 190, 190)
        self.line(self.l_margin, y, self.l_margin + self.epw, y)
        self.ln(3.2)


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def render(blok, pdf):
    for b in blok:
        try:
            j = b["jenis"]
            if j == "teks":
                pdf.blok_teks(b["tag"], b["html"])
            elif j == "senarai":
                if b["tag"] == "ol":
                    pdf.blok_senarai_bernombor(b["item"])
                else:
                    pdf.blok_senarai(b["tag"], b["item"])
            elif j == "kod":
                pdf.blok_kod(b["teks"])
            elif j == "petikan":
                pdf.blok_petikan(b["para"])
            elif j == "jadual":
                pdf.blok_jadual(b["baris"], b.get("kepala", True))
            elif j == "hr":
                pdf.garisan()
        except Exception as e:  # blok gagal -> teks biasa, jangan mati
            sys.stderr.write(f"AMARAN: blok {b.get('jenis')} gagal ({e}); "
                             f"jatuh ke teks biasa\n")
            try:
                teks = b.get("teks") or teks_biasa(b.get("html", "") or "")
                if not teks and b.get("jenis") == "jadual":
                    teks = "\n".join(" | ".join(r) for r in b.get("baris", []))
                if not teks and b.get("jenis") == "senarai":
                    teks = "\n".join("• " + teks_biasa(i["html"]) for i in b["item"])
                pdf._font("", 10)
                pdf.multi_cell(pdf.epw, 5.2, pecah_token(teks or ""),
                               wrapmode=WrapMode.CHAR)
                pdf.ln(2)
            except Exception as e2:
                sys.stderr.write(f"AMARAN: fallback teks juga gagal ({e2})\n")


def main():
    global JUDUL_DOKUMEN
    ap = argparse.ArgumentParser(
        description="Markdown -> PDF (fpdf2 + markdown), Termux Android.")
    ap.add_argument("input", help="fail Markdown")
    ap.add_argument("output", help="fail PDF keluaran")
    ap.add_argument("--tajuk", default="", help="tajuk dokumen (pilihan)")
    a = ap.parse_args()

    if not os.path.isfile(a.input):
        sys.stderr.write(f"GAGAL: input tidak wujud: {a.input}\n")
        return 2
    for f in (DEJAVU, DEJAVU_B, DEJAVU_I, DEJAVU_BI, MONO):
        if not os.path.isfile(f):
            sys.stderr.write(f"GAGAL: font tidak dijumpai: {f}\n")
            return 3

    try:
        with open(a.input, "r", encoding="utf-8", errors="replace") as fh:
            md = fh.read()
    except Exception as e:
        sys.stderr.write(f"GAGAL: tak boleh baca input: {e}\n")
        return 4

    JUDUL_DOKUMEN = a.tajuk.strip()

    try:
        html = markdown.markdown(
            md,
            extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
            output_format="html5",
        )
    except Exception as e:
        sys.stderr.write(f"GAGAL: markdown -> html: {e}\n")
        return 5

    parser = ParserBlok()
    try:
        parser.feed(html)
        blok = parser.tutup()
    except Exception as e:
        sys.stderr.write(f"AMARAN: parser HTML bermasalah ({e}); guna teks mentah\n")
        blok = [{"jenis": "kod", "teks": md}]

    pdf = PDFUIM(os.path.basename(a.input))
    pdf.set_title(JUDUL_DOKUMEN or os.path.basename(a.input))
    pdf.add_page()

    if JUDUL_DOKUMEN:
        pdf._font("B", 18)
        pdf.multi_cell(pdf.epw, 9, JUDUL_DOKUMEN, align="L",
                       wrapmode=WrapMode.CHAR)
        y = pdf.get_y() + 1.2
        pdf.set_draw_color(150, 150, 150)
        pdf.line(pdf.l_margin, y, pdf.l_margin + pdf.epw, y)
        pdf.ln(6)
        pdf._font("", 10)

    render(blok, pdf)

    out = os.path.abspath(a.output)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    try:
        pdf.output(out)
    except Exception as e:
        sys.stderr.write(f"GAGAL: tulis PDF: {e}\n")
        return 6

    saiz = os.path.getsize(out)
    if saiz <= 0:
        sys.stderr.write("GAGAL: PDF 0 bait\n")
        return 7
    print(f"PDF: {out}")
    print(f"  saiz    : {saiz} bait")
    print(f"  halaman : {pdf.page_no()}")
    print(f"  blok    : {len(blok)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
