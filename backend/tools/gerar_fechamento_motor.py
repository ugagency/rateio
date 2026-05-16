"""Gera o FECHAMENTO de saída no LAYOUT IDÊNTICO ao da AutoTruck.

Usa o arquivo FECHAMENTO real como template (preserva abas, formatação,
estrutura) e escreve, **nas mesmas células** do ANALITICO, os valores
calculados pelo NOSSO engine sobre os eventos da aba RATEIO deles.
Anexa a aba CONFERENCIA_MOTOR comparando, célula a célula, o valor
ORIGINAL deles × o do engine (Δ deve ser 0,00).

Uso: cd backend && .venv/bin/python -m tools.gerar_fechamento_motor \
        [FECHAMENTO_origem.xlsx] [saida.xlsx]
"""

import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill

from app.autotruck.engine import calcular_rateio_at
from app.autotruck.ingestao import ler_fechamento

OK = PatternFill("solid", fgColor="C6EFCE")
BAD = PatternFill("solid", fgColor="FFC7CE")
H = Font(bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor="1F4E79")
MONEY = "#,##0.00"


def _mapa_analitico(ws):
    """Localiza, por rótulo (layout-robusto), as células de valor do
    ANALITICO. Devolve {chave: (row, col)}. Col D(4)=LEVES/PESADOS-assoc;
    Col G(7)=MOTOS/PESADOS-terc."""
    m = {}
    cl = cm = None  # contexto LEVES / MOTOS: ASSOC | TERC | PESADOS
    for r in range(1, ws.max_row + 1):
        sL = str(ws.cell(r, 3).value or "").strip().upper()
        sM = str(ws.cell(r, 6).value or "").strip().upper()
        if sL == "RATEIO LEVES":
            m["leves_rateio"] = (r, 4)
        if sM == "RATEIO MOTOS":
            m["motos_rateio"] = (r, 7)
        if sL == "LEVES ASSOCIADOS":
            cl = "ASSOC"; m["leves_assoc"] = (r, 4)
        elif sL == "LEVES TERCEIROS":
            cl = "TERC"; m["leves_terc_hdr"] = (r, 4)
        elif sL.startswith("PESADOS"):
            cl = "PESADOS"; m["pesados_assoc_hdr"] = (r, 4)
        if sM == "MOTOS ASSOCIADOS":
            cm = "ASSOC"; m["motos_assoc"] = (r, 7)
        elif sM == "MOTOS TERCEIROS":
            cm = "TERC"; m["motos_terc_hdr"] = (r, 7)
        elif sM.startswith("PESADOS"):
            cm = "PESADOS"; m["pesados_terc_hdr"] = (r, 7)
        if sL == "INDENIZAÇÃO INTEGRAL":
            m[{"ASSOC": "leves_int", "TERC": "leves_terc_int",
               "PESADOS": "pesados_int"}[cl]] = (r, 4)
        if sL == "INDENIZAÇÃO PARCIAL":
            m[{"ASSOC": "leves_par", "TERC": "leves_terc_par",
               "PESADOS": "pesados_par"}[cl]] = (r, 4)
        if sL == "TOTAL" and cl == "TERC":
            m["leves_terc_tot"] = (r, 4)
        if sL == "TOTAL" and cl == "PESADOS":
            m["pesados_tot"] = (r, 4)
        if sM == "INDENIZAÇÃO INTEGRAL":
            m[{"ASSOC": "motos_int", "TERC": "motos_terc_int",
               "PESADOS": "pesados_terc_int"}[cm]] = (r, 7)
        if sM == "INDENIZAÇÃO PARCIAL":
            m[{"ASSOC": "motos_par", "TERC": "motos_terc_par",
               "PESADOS": "pesados_terc_par"}[cm]] = (r, 7)
        if sM == "TOTAL" and cm == "TERC":
            m["motos_terc_tot"] = (r, 7)
        if sM == "TOTAL" and cm == "PESADOS":
            m["pesados_terc_tot"] = (r, 7)
        if sM == "PESADOS TERCEIROS":
            m["pesados_terc_hdr"] = (r, 7)
    return m


def _terc_split(eventos, seg, tipo):
    return round(sum(e.custo_a_ratear for e in eventos
                     if e.segmento == seg and e.envolvimento == "TERCEIRO"
                     and e.tipo_evento == tipo), 2)


def gerar(origem: str, saida: str) -> str:
    f = ler_fechamento(origem)
    r = calcular_rateio_at(mes_ano_ref="FECHAMENTO", veiculos=[], eventos=f.eventos)
    seg = {s.segmento: s for s in r.segmentos}
    ev = r.eventos_rateados

    val = {
        "leves_rateio": r.consolidado.bruto_leves,
        "leves_assoc": r.consolidado.bruto_leves,
        "leves_int": seg["LEVES"].custo_integrais,
        "leves_par": seg["LEVES"].custo_parciais,
        "leves_terc_hdr": -round(r.consolidado.recuperacao_terceiros_leves, 2),
        "leves_terc_int": _terc_split(ev, "LEVES", "INTEGRAL"),
        "leves_terc_par": _terc_split(ev, "LEVES", "PARCIAL"),
        "leves_terc_tot": round(r.consolidado.recuperacao_terceiros_leves, 2),
        "motos_rateio": r.consolidado.bruto_motos,
        "motos_assoc": r.consolidado.bruto_motos,
        "motos_int": seg["MOTOS"].custo_integrais,
        "motos_par": seg["MOTOS"].custo_parciais,
        "motos_terc_hdr": -round(r.consolidado.recuperacao_terceiros_motos, 2),
        "motos_terc_int": _terc_split(ev, "MOTOS", "INTEGRAL"),
        "motos_terc_par": _terc_split(ev, "MOTOS", "PARCIAL"),
        "motos_terc_tot": round(r.consolidado.recuperacao_terceiros_motos, 2),
        "pesados_terc_hdr": -_terc_split(ev, "PESADOS", "INTEGRAL")
        - _terc_split(ev, "PESADOS", "PARCIAL"),
        "pesados_terc_int": _terc_split(ev, "PESADOS", "INTEGRAL"),
        "pesados_terc_par": _terc_split(ev, "PESADOS", "PARCIAL"),
        "pesados_terc_tot": _terc_split(ev, "PESADOS", "INTEGRAL")
        + _terc_split(ev, "PESADOS", "PARCIAL"),
    }

    # valores ORIGINAIS *calculados* deles (a planilha deles usa fórmulas)
    wb_val = openpyxl.load_workbook(origem, data_only=True)
    orig_ws = wb_val["ANALITICO"]

    wb = openpyxl.load_workbook(origem)          # preserva layout/formatos
    ws = wb["ANALITICO"]
    mp = _mapa_analitico(ws)

    conf = []  # (rotulo, original, engine, delta)
    for chave, (row, col) in mp.items():
        if chave not in val:
            continue
        ov = orig_ws.cell(row, col).value
        orig = float(ov) if isinstance(ov, (int, float)) else 0.0
        novo = round(val[chave], 2)
        ws.cell(row, col, novo).number_format = MONEY
        conf.append((f"{chave}  (cél. {openpyxl.utils.get_column_letter(col)}{row})",
                     round(orig, 2), novo, round(novo - orig, 2)))

    cs = wb.create_sheet("CONFERENCIA_MOTOR")
    cs["A1"] = "CONFERÊNCIA — ANALITICO original (AutoTruck) × motor"
    cs["A1"].font = Font(bold=True, size=13)
    cs["A2"] = ("Mesma célula, mesmo layout. 'original' = valor que estava no "
                "arquivo de vocês; 'engine' = recalculado pelo motor sobre os "
                "eventos da aba RATEIO. Δ = 0,00 ⇒ idêntico célula a célula.")
    cs.merge_cells("A2:D2")
    for i, c in enumerate(["métrica (célula)", "original (vocês)", "engine (motor)", "Δ"], 1):
        x = cs.cell(4, i, c); x.font = H; x.fill = HF
    falhas = 0
    for j, (rot, o, e, d) in enumerate(sorted(conf), start=5):
        cs.cell(j, 1, rot)
        cs.cell(j, 2, o).number_format = MONEY
        cs.cell(j, 3, e).number_format = MONEY
        dc = cs.cell(j, 4, d); dc.number_format = MONEY
        dc.fill = OK if abs(d) <= 0.01 else BAD
        falhas += abs(d) > 0.01
    fim = 5 + len(conf) + 1
    cs.cell(fim, 1, "RESULTADO").font = Font(bold=True)
    rc = cs.cell(fim, 2, "IDÊNTICO ✅ (Δ=0)" if falhas == 0 else f"{falhas} divergência(s) ❌")
    rc.fill = OK if falhas == 0 else BAD
    for col, w in {"A": 40, "B": 18, "C": 18, "D": 12}.items():
        cs.column_dimensions[col].width = w

    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)
    return f"{saida} | {len(conf)} células escritas | divergências: {falhas}"


def main() -> int:
    origem = sys.argv[1] if len(sys.argv) > 1 else \
        "/root/projetos/Mut/backend/tests/fixtures/FECHAMENTO_referencia.xlsx"
    saida = sys.argv[2] if len(sys.argv) > 2 else \
        "/root/projetos/Mut/simulacoes/FECHAMENTO_AutoTruck_MOTOR.xlsx"
    print("OK:", gerar(origem, saida))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
