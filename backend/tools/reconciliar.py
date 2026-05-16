"""Reconciliação de aceite — aponta para o FECHAMENTO real da AutoTruck,
roda o ENGINE sobre os insumos da planilha deles e confronta, centavo a
centavo, com o ANALITICO declarado por eles.

Uso:
  cd backend && .venv/bin/python -m tools.reconciliar <FECHAMENTO.xlsx> [saida.xlsx]

Critério de aceite: nenhuma linha em FALHA (|Δ| ≤ R$ 0,01).
Código de saída 0 = APROVADO, 1 = REPROVADO.
"""

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.autotruck.ingestao import reconciliar

H = Font(bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor="1F4E79")
OK = PatternFill("solid", fgColor="C6EFCE")
WARN = PatternFill("solid", fgColor="FFEB9C")
BAD = PatternFill("solid", fgColor="FFC7CE")
MONEY = "#,##0.00"


def _xlsx(rec, destino: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "RECONCILIACAO"
    ws["A1"] = "RECONCILIAÇÃO DE ACEITE — FECHAMENTO AutoTruck"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Arquivo: {Path(rec.arquivo).name}"
    ws["A3"] = (f"Eventos lidos da aba RATEIO: {rec.n_eventos} | seções com dados: "
                f"{', '.join(rec.secoes_com_dados) or '—'}")
    ws["A4"] = ("Critério: |Δ| ≤ R$ 0,01. 'Engine' = nosso motor rodando sobre os "
                "eventos da planilha DELES; 'declarado' = ANALITICO deles.")
    ws["A4"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A4:F4")
    cab = ["grupo", "item", "declarado (ANALITICO)", "calculado (engine/identidade)",
           "Δ", "status"]
    for i, c in enumerate(cab, 1):
        cell = ws.cell(6, i, c)
        cell.font = H
        cell.fill = HF
    for j, ln in enumerate(rec.linhas, start=7):
        ws.cell(j, 1, ln.grupo)
        ws.cell(j, 2, ln.item)
        ws.cell(j, 3, ln.declarado).number_format = MONEY
        ws.cell(j, 4, ln.calculado).number_format = MONEY
        ws.cell(j, 5, ln.delta).number_format = MONEY
        st = ws.cell(j, 6, ln.status)
        st.fill = OK if ln.status == "OK" else (BAD if ln.status == "FALHA" else WARN)
    fim = 7 + len(rec.linhas) + 1
    ws.cell(fim, 1, "RESULTADO").font = Font(bold=True)
    res = ws.cell(fim, 2, "APROVADO ✅" if rec.aprovado else "REPROVADO ❌")
    res.fill = OK if rec.aprovado else BAD
    res.font = Font(bold=True)
    for col, w in {"A": 24, "B": 42, "C": 22, "D": 28, "E": 12, "F": 24}.items():
        ws.column_dimensions[col].width = w
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = sys.argv[1]
    rec = reconciliar(src)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        "/root/projetos/Mut/simulacoes") / f"RECONCILIACAO_{Path(src).stem}.xlsx"
    _xlsx(rec, out)

    print(f"\nReconciliação — {Path(src).name}")
    print(f"Eventos lidos da aba RATEIO: {rec.n_eventos}  |  seções com dados: "
          f"{', '.join(rec.secoes_com_dados) or '—'}\n")
    g = None
    for ln in rec.linhas:
        if ln.grupo != g:
            g = ln.grupo
            print(f"— {g} —")
        print(f"  {ln.item:<42} decl={ln.declarado:>14,.2f}  "
              f"calc={ln.calculado:>14,.2f}  Δ={ln.delta:>9,.2f}  [{ln.status}]")
    print(f"\nRESULTADO: {'APROVADO ✅' if rec.aprovado else 'REPROVADO ❌'}")
    print(f"→ planilha de reconciliação: {out}")
    return 0 if rec.aprovado else 1


if __name__ == "__main__":
    raise SystemExit(main())
