"""Conversor simples de Markdown para PDF (fpdf2 + fontes DejaVu).

Cobre os construtos usados nos guias: titulos (#, ##, ###), paragrafos, listas
numeradas e com marcador (inclusive aninhadas), blocos indentados (monospace),
regra horizontal (---), codigo inline (`...`), negrito (**...**) e a tabela de
pipes da comparacao. Nao e um renderizador Markdown completo, e suficiente para
estes documentos.

Uso: _md_to_pdf.py entrada.md saida.pdf
"""

import sys
from pathlib import Path

from fpdf import FPDF

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _novo_pdf() -> FPDF:
    pdf = FPDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_font("DejaVu", "", f"{FONT_DIR}/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", f"{FONT_DIR}/DejaVuSans-Bold.ttf")
    pdf.add_font("Mono", "", f"{FONT_DIR}/DejaVuSansMono.ttf")
    pdf.add_page()
    return pdf


def _tokens(texto: str):
    """Quebra o texto em (estilo, trecho) por ` (mono) e ** (negrito)."""
    out = []
    i = 0
    estilo = "n"  # n=normal, b=negrito, c=codigo
    buf = ""
    while i < len(texto):
        if texto[i] == "`":
            if buf:
                out.append((estilo, buf)); buf = ""
            estilo = "c" if estilo != "c" else "n"
            i += 1
        elif texto.startswith("**", i):
            if buf:
                out.append((estilo, buf)); buf = ""
            estilo = "b" if estilo != "b" else "n"
            i += 2
        else:
            buf += texto[i]; i += 1
    if buf:
        out.append((estilo, buf))
    return out


def _write_inline(pdf: FPDF, texto: str, size: int = 11, lh: float = 6.0):
    for estilo, trecho in _tokens(texto):
        if estilo == "c":
            pdf.set_font("Mono", "", size - 1)
        elif estilo == "b":
            pdf.set_font("DejaVu", "B", size)
        else:
            pdf.set_font("DejaVu", "", size)
        pdf.write(lh, trecho)
    pdf.ln(lh)


def _render_tabela(pdf: FPDF, linhas: list):
    # remove a linha separadora (apenas - | espaco)
    dados = [l for l in linhas if set(l.strip()) - set("-| ")]
    rows = [[c.strip() for c in l.split("|")] for l in dados]
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    # 1a coluna mais estreita; demais dividem o resto
    if ncols == 3:
        widths = (46, 72, 72)
    else:
        w = 190 / ncols
        widths = tuple([w] * ncols)
    pdf.set_font("DejaVu", "", 9)
    with pdf.table(col_widths=widths, first_row_as_headings=True,
                   line_height=5.2, padding=1.4) as table:
        for ri, r in enumerate(rows):
            trow = table.row()
            for cell in r:
                trow.cell(cell)
    pdf.ln(3)


def converter(md_path: Path, pdf_path: Path):
    linhas = md_path.read_text(encoding="utf-8").split("\n")
    pdf = _novo_pdf()
    i = 0
    while i < len(linhas):
        ln = linhas[i]
        s = ln.strip()

        # bloco de tabela (linhas consecutivas com |)
        if "|" in ln and ln.count("|") >= 2:
            bloco = []
            while i < len(linhas) and "|" in linhas[i] and linhas[i].count("|") >= 2:
                bloco.append(linhas[i]); i += 1
            _render_tabela(pdf, bloco)
            continue

        # bloco indentado (4 espacos) -> monospace
        if ln.startswith("    ") and s:
            bloco = []
            while i < len(linhas) and (linhas[i].startswith("    ") or not linhas[i].strip()):
                if linhas[i].strip():
                    bloco.append(linhas[i][4:])
                elif bloco:
                    break
                i += 1
            pdf.set_font("Mono", "", 9.5)
            pdf.set_text_color(40, 40, 40)
            for b in bloco:
                pdf.multi_cell(0, 5, b)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
            continue

        if not s:
            i += 1
            continue

        if s == "---":
            pdf.ln(1)
            y = pdf.get_y()
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(3)
            i += 1
            continue

        if s.startswith("### "):
            pdf.ln(1); pdf.set_font("DejaVu", "B", 12)
            pdf.multi_cell(0, 6.5, s[4:]); pdf.ln(1)
            i += 1; continue
        if s.startswith("## "):
            pdf.ln(2); pdf.set_font("DejaVu", "B", 14)
            pdf.multi_cell(0, 7.5, s[3:]); pdf.ln(1.5)
            i += 1; continue
        if s.startswith("# "):
            pdf.set_font("DejaVu", "B", 18)
            pdf.multi_cell(0, 9, s[2:]); pdf.ln(3)
            i += 1; continue

        # listas: "N. " ou "- ", com indentacao opcional (aninhadas)
        indent = len(ln) - len(ln.lstrip(" "))
        import re
        m_num = re.match(r"^(\d+)\.\s+(.*)$", s)
        m_bul = re.match(r"^[-*]\s+(.*)$", s)
        if m_num or m_bul:
            x0 = pdf.l_margin + (6 if indent >= 2 else 0)
            marcador = (m_num.group(1) + ".") if m_num else "-"
            conteudo = m_num.group(2) if m_num else m_bul.group(1)
            pdf.set_x(x0)
            pdf.set_font("DejaVu", "", 11)
            pdf.cell(8 if m_num else 5, 6, marcador)
            pdf.set_x(x0 + (8 if m_num else 5))
            # texto da lista com recuo de continuacao
            pdf.set_left_margin(x0 + (8 if m_num else 5))
            _write_inline(pdf, conteudo, size=11, lh=6.0)
            pdf.set_left_margin(18)
            i += 1; continue

        # paragrafo
        _write_inline(pdf, s, size=11, lh=6.0)
        pdf.ln(1.5)
        i += 1

    pdf.output(str(pdf_path))


if __name__ == "__main__":
    converter(Path(sys.argv[1]), Path(sys.argv[2]))
