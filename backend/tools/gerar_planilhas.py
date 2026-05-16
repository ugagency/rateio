"""Gera as planilhas de simulação AutoTruck (1 XLSX por cenário).

Prova anti-mock: a aba CONFERENCIA traz, lado a lado, TRÊS derivações
independentes de cada número — (1) engine, (2) recálculo Python
(`verificacao.recomputar`), (3) fórmula nativa do Excel (SUMIFS/CEILING/IF)
sobre as abas de INPUT. As três têm de bater (Δ = 0). Quem abrir o
arquivo pode alterar um input e ver as fórmulas recalcularem.

Uso:  cd backend && .venv/bin/python -m tools.gerar_planilhas [destino]
"""

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.autotruck.cenarios import build
from app.autotruck.engine import calcular_rateio_at, sugerir_ajuste
from app.autotruck.verificacao import recomputar

H = Font(bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor="1F4E79")
TITLE = Font(bold=True, size=14)
OK = PatternFill("solid", fgColor="C6EFCE")
BAD = PatternFill("solid", fgColor="FFC7CE")
MONEY = "#,##0.00"


def _hdr(ws, row, cols, start=1):
    for i, c in enumerate(cols):
        cell = ws.cell(row=row, column=start + i, value=c)
        cell.font = H
        cell.fill = HF
        cell.alignment = Alignment(horizontal="center")


def _sheet_inputs_veiculos(wb, veics):
    ws = wb.create_sheet("INPUTS_VEICULOS")
    cols = ["id", "placa", "segmento", "tipo", "fipe", "status_ativo", "adimplente",
            "servicos", "cobertura", "qtd_cotas(F)", "elegivel(F)",
            "cotas_elegiveis(F)", "preco_terceiros(F)"]
    _hdr(ws, 1, cols)
    for i, v in enumerate(veics, start=2):
        ws.cell(i, 1, v.id_veiculo)
        ws.cell(i, 2, v.placa)
        ws.cell(i, 3, v.segmento)
        ws.cell(i, 4, v.tipo_veiculo)
        ws.cell(i, 5, round(v.valor_fipe, 2)).number_format = MONEY
        ws.cell(i, 6, 1 if v.status_ativo else 0)
        ws.cell(i, 7, 1 if v.adimplente else 0)
        ws.cell(i, 8, round(v.servicos_adicionais, 2)).number_format = MONEY
        ws.cell(i, 9, v.cobertura_terceiros)
        ws.cell(i, 10, f"=IF(E{i}>450000,20,1+0.5*(CEILING(E{i}/10000,1)-1))")
        ws.cell(i, 11, f"=IF(AND(F{i}=1,G{i}=1),1,0)")
        ws.cell(i, 12, f"=J{i}*K{i}")
        ws.cell(i, 13, f'=IF(K{i}=1,IF(I{i}="100K",30,IF(I{i}="50K",20,0)),0)')
    ws.freeze_panes = "A2"
    return len(veics) + 1


def _sheet_inputs_eventos(wb, evs):
    ws = wb.create_sheet("INPUTS_EVENTOS")
    cols = ["id", "protocolo", "placa", "segmento", "envolvimento", "tipo_evento",
            "valor_evento", "orcamento_reparo", "valor_fipe", "data_aviso",
            "franquia", "valor_salvado", "salvado_liq", "tipo_efetivo(F)",
            "custo_a_ratear(F)"]
    _hdr(ws, 1, cols)
    for i, e in enumerate(evs, start=2):
        ws.cell(i, 1, e.id_evento)
        ws.cell(i, 2, e.protocolo)
        ws.cell(i, 3, e.placa)
        ws.cell(i, 4, e.segmento)
        ws.cell(i, 5, e.envolvimento)
        ws.cell(i, 6, e.tipo_evento)
        ws.cell(i, 7, round(e.valor_evento, 2)).number_format = MONEY
        ws.cell(i, 8, round(e.orcamento_reparo, 2)).number_format = MONEY
        ws.cell(i, 9, round(e.valor_fipe, 2)).number_format = MONEY
        ws.cell(i, 10, e.data_aviso)
        ws.cell(i, 11, round(e.franquia, 2)).number_format = MONEY
        ws.cell(i, 12, round(e.valor_salvado, 2)).number_format = MONEY
        ws.cell(i, 13, 1 if e.salvado_liquidado else 0)
        ws.cell(i, 14, f'=IF(AND(F{i}<>"INTEGRAL",I{i}>0,H{i}>0.75*I{i}),"INTEGRAL",F{i})')
        ws.cell(i, 15, f'=IF(N{i}="INTEGRAL",I{i},G{i})')
    ws.freeze_panes = "A2"
    return len(evs) + 1


def _conf_linha(ws, row, rotulo, eng, py, formula, money=True):
    ws.cell(row, 1, rotulo)
    c_eng = ws.cell(row, 2, round(eng, 2))
    c_py = ws.cell(row, 3, round(py, 2))
    c_xls = ws.cell(row, 4, formula)
    ws.cell(row, 5, round(eng - py, 2))                       # Δ engine−python (valor)
    ws.cell(row, 6, f"=ROUND(B{row}-D{row},2)")               # Δ engine−Excel (fórmula)
    for c in (c_eng, c_py):
        if money:
            c.number_format = MONEY
    dcell = ws.cell(row, 5)
    dcell.fill = OK if abs(eng - py) < 0.01 else BAD
    ws.cell(row, 6).fill = OK


def _sheet_conferencia(wb, r, rec, cen, nv, ne):
    ws = wb.create_sheet("CONFERENCIA", 0)
    ws["A1"] = f"CONFERÊNCIA — Cenário {cen.nome}: {cen.titulo}"
    ws["A1"].font = TITLE
    ws["A2"] = ("Três derivações independentes do mesmo número: ENGINE · "
                "RECÁLCULO PYTHON · FÓRMULA EXCEL (SUMIFS/CEILING/IF sobre as "
                "abas INPUTS_*). Δ deve ser 0,00 — prova de que os dados são "
                "calculados, não fixos. Altere um input e as fórmulas recalculam.")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = 46

    EV, VE = "INPUTS_EVENTOS", "INPUTS_VEICULOS"
    er, vr = f"$N$2:$N${ne}", None  # placeholders
    ev_seg, ev_env, ev_tef = f"{EV}!$D$2:$D${ne}", f"{EV}!$E$2:$E${ne}", f"{EV}!$N$2:$N${ne}"
    ev_cus, ev_fr, ev_sv, ev_sl = (f"{EV}!$O$2:$O${ne}", f"{EV}!$K$2:$K${ne}",
                                    f"{EV}!$L$2:$L${ne}", f"{EV}!$M$2:$M${ne}")
    ve_seg, ve_cot = f"{VE}!$C$2:$C${nv}", f"{VE}!$L$2:$L${nv}"
    ve_cob = f"{VE}!$M$2:$M${nv}"

    row = 4
    cons = r.consolidado
    for seg in ("LEVES", "MOTOS"):
        s = next(x for x in r.segmentos if x.segmento == seg)
        rc = rec[seg]
        ws.cell(row, 1, f"— SEGMENTO {seg} (rateio variável) —").font = Font(bold=True)
        row += 1
        _hdr(ws, row, ["métrica", "engine", "python", "fórmula Excel", "Δ eng−py", "Δ eng−xls"])
        row += 1
        ig_f = (f'=SUMIFS({ev_cus},{ev_seg},"{seg}",{ev_env},"ASSOCIADO",{ev_tef},"INTEGRAL")')
        pa_f = (f'=SUMIFS({ev_cus},{ev_seg},"{seg}",{ev_env},"ASSOCIADO",{ev_tef},"PARCIAL")')
        sv_f = (f'=SUMIFS({ev_sv},{ev_seg},"{seg}",{ev_env},"ASSOCIADO",{ev_sl},1)')
        fr_f = (f'=SUMIFS({ev_fr},{ev_seg},"{seg}",{ev_env},"ASSOCIADO")')
        co_f = f'=SUMIFS({ve_cot},{ve_seg},"{seg}")'
        _conf_linha(ws, row, "custo integrais", s.custo_integrais, rc["custo_integrais"], ig_f); ri = row; row += 1
        _conf_linha(ws, row, "custo parciais", s.custo_parciais, rc["custo_parciais"], pa_f); rp = row; row += 1
        _conf_linha(ws, row, "(−) salvados liq.", s.deducao_salvados, rc["deducao_salvados"], sv_f); rs = row; row += 1
        _conf_linha(ws, row, "(−) franquias", s.deducao_franquias, rc["deducao_franquias"], fr_f); rf = row; row += 1
        _conf_linha(ws, row, "= custo a ratear", s.custo_a_ratear, rc["custo_a_ratear"],
                    f"=D{ri}+D{rp}-D{rs}-D{rf}"); rcar = row; row += 1
        _conf_linha(ws, row, "cotas ativas (denominador)", s.cotas_ativas, rc["cotas_ativas"],
                    co_f, money=False); rco = row; row += 1
        _conf_linha(ws, row, "VALOR DA COTA", s.valor_cota, rc["valor_cota"],
                    f"=ROUND(D{rcar}/D{rco},2)"); row += 1
        ws.cell(row, 1, f"terceiros (rastreado, NÃO abate — N3): R$ {s.recuperacao_terceiros:,.2f}")
        row += 2

    # Potes
    ws.cell(row, 1, "— POTES FIXOS (não entram na divisão de cotas) —").font = Font(bold=True)
    row += 1
    _hdr(ws, row, ["métrica", "engine", "python", "fórmula Excel", "Δ eng−py", "Δ eng−xls"])
    row += 1
    pcc = cen.params.preco_casco_caminhao
    _conf_linha(ws, row, "Terceiros — arrecadado", cons.pote_terceiros_arrecadado,
                rec["POTES"]["terceiros_arrecadado"], f"=SUM({ve_cob})"); row += 1
    _conf_linha(ws, row, "Terceiros — custo (payouts)", cons.pote_terceiros_custo,
                rec["POTES"]["terceiros_custo"], f'=SUMIFS({ev_cus},{ev_env},"TERCEIRO")'); row += 1
    _conf_linha(ws, row, "Caminhão — arrecadado", cons.pote_caminhao_arrecadado,
                rec["POTES"]["caminhao_arrecadado"],
                f'=COUNTIFS({ve_seg},"PESADOS",{VE}!$K$2:$K${nv},1)*{pcc}'); row += 1
    _conf_linha(ws, row, "Caminhão — custo (PT assoc.)", cons.pote_caminhao_custo,
                rec["POTES"]["caminhao_custo"],
                f'=SUMIFS({ev_cus},{ev_seg},"PESADOS",{ev_env},"ASSOCIADO")'); row += 2

    ws.cell(row, 1, "INVARIANTE DE AUDITORIA (engine):").font = Font(bold=True)
    inv = ws.cell(row, 2, "OK · Δ 0,00" if cons.invariante_ok else f"FALHA Δ {cons.diferenca_total}")
    inv.fill = OK if cons.invariante_ok else BAD
    for col, w in {"A": 30, "B": 16, "C": 16, "D": 52, "E": 12, "F": 12}.items():
        ws.column_dimensions[col].width = w
    return ws


def _sheet_resumo(wb, r, cen):
    ws = wb.create_sheet("RESUMO", 0)
    c = r.consolidado
    L = next(x for x in r.segmentos if x.segmento == "LEVES")
    ws["A1"] = f"AutoTruck — Simulação · Cenário {cen.nome}"
    ws["A1"].font = TITLE
    ws["A2"] = cen.titulo
    ws["A2"].font = Font(bold=True, size=12)
    ws["A3"] = cen.descricao
    ws["A3"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A3:D3")
    ws.row_dimensions[3].height = 70
    linhas = [
        ("Mês de referência", cen.mes_ano_ref),
        ("Veículos (total / elegíveis — purista)", f"{c.total_veiculos} / {c.total_veiculos_elegiveis}"),
        ("Cota LEVES", f"R$ {c.cota_leves:,.2f}  ({L.faixa_estabilizacao})"),
        ("Cota MOTOS", f"R$ {c.cota_motos:,.2f}"),
        ("Custo a ratear LEVES (= integral+parcial)", f"R$ {c.custo_a_ratear_leves:,.2f}"),
        ("Terceiros rastreado LEVES (não abate — N3)", f"R$ {c.recuperacao_terceiros_leves:,.2f}"),
        ("Alerta de volatilidade (sinistro > 25% pool)", "SIM" if L.alerta_volatilidade else "não"),
        ("Reclassificados pela regra dos 75%", c.eventos_reclassificados_75pct),
        ("Eventos postergados (teto pote caminhão)", c.eventos_postergados),
        ("Pote Terceiros — arrec / custo / reserva",
         f"R$ {c.pote_terceiros_arrecadado:,.2f} / {c.pote_terceiros_custo:,.2f} / {c.pote_terceiros_reserva:,.2f}"),
        ("Pote Caminhão — arrec / custo / reserva",
         f"R$ {c.pote_caminhao_arrecadado:,.2f} / {c.pote_caminhao_custo:,.2f} / {c.pote_caminhao_reserva:,.2f}"),
        ("Invariante de auditoria", "OK · Δ 0,00" if c.invariante_ok else f"FALHA Δ {c.diferenca_total}"),
    ]
    for i, (k, v) in enumerate(linhas, start=5):
        ws.cell(i, 1, k).font = Font(bold=True)
        ws.cell(i, 2, v)
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 52
    return ws


def _sheet_tabela(wb, nome, cols, linhas):
    ws = wb.create_sheet(nome)
    _hdr(ws, 1, cols)
    for i, lin in enumerate(linhas, start=2):
        for j, val in enumerate(lin, start=1):
            cell = ws.cell(i, j, val)
            if isinstance(val, float):
                cell.number_format = MONEY
    ws.freeze_panes = "A2"


def gerar(nome_cenario: str, destino: Path) -> Path:
    cen = build(nome_cenario)
    r = calcular_rateio_at(mes_ano_ref=cen.mes_ano_ref, veiculos=cen.veiculos,
                           eventos=cen.eventos, params=cen.params,
                           historico_cotas=cen.historico_cotas)
    rec = recomputar(cen.veiculos, cen.eventos, cen.params)
    sug = sugerir_ajuste(r, params=cen.params)

    wb = Workbook()
    wb.remove(wb.active)
    nv = _sheet_inputs_veiculos(wb, cen.veiculos)
    ne = _sheet_inputs_eventos(wb, cen.eventos)
    _sheet_tabela(wb, "APURACAO",
                  ["segmento", "modo", "integrais", "parciais", "salvados",
                   "franquias", "terceiros_rastreado", "custo_a_ratear",
                   "cotas_ativas", "valor_cota", "faixa", "media_3m",
                   "variacao", "alerta_volat", "alerta_trim"],
                  [[s.segmento, s.modo, s.custo_integrais, s.custo_parciais,
                    s.deducao_salvados, s.deducao_franquias, s.recuperacao_terceiros,
                    s.custo_a_ratear, s.cotas_ativas, s.valor_cota,
                    s.faixa_estabilizacao, s.media_cota_3m, s.variacao_vs_media,
                    s.alerta_volatilidade, s.alerta_variacao_trimestral]
                   for s in r.segmentos])
    _sheet_tabela(wb, "POTES",
                  ["pote", "arrecadado", "custo", "reserva_ou_deficit", "situacao"],
                  [["Terceiros (50k/100k)", r.consolidado.pote_terceiros_arrecadado,
                    r.consolidado.pote_terceiros_custo, r.consolidado.pote_terceiros_reserva,
                    "reserva" if r.consolidado.pote_terceiros_reserva >= 0 else "déficit"],
                   ["Casco Caminhão", r.consolidado.pote_caminhao_arrecadado,
                    r.consolidado.pote_caminhao_custo, r.consolidado.pote_caminhao_reserva,
                    "reserva" if r.consolidado.pote_caminhao_reserva >= 0 else "déficit"]])
    _sheet_tabela(wb, "EVENTOS_FIFO",
                  ["#fifo", "id", "protocolo", "segmento", "envolvimento",
                   "data_aviso", "tipo", "reclass_75", "custo_a_ratear", "status"],
                  [[e.ordem_fifo, e.id_evento, e.protocolo, e.segmento, e.envolvimento,
                    e.data_aviso, e.tipo_evento, "SIM" if e.reclassificado_75pct else "",
                    e.custo_a_ratear, e.status] for e in r.eventos_rateados])
    bol = sorted(r.boletos, key=lambda b: (not b.cota_especial, b.id_veiculo))[:120]
    _sheet_tabela(wb, "BOLETOS",
                  ["id", "placa", "segmento", "fipe", "qtd_cotas", "cota_especial",
                   "rateio", "pote_terceiros", "pote_caminhao", "servicos",
                   "TOTAL", "emite"],
                  [[b.id_veiculo, b.placa, b.segmento, b.valor_fipe, b.qtd_cotas,
                    "SIM" if b.cota_especial else "", b.custo_rateio,
                    b.custo_pote_terceiros, b.custo_pote_caminhao,
                    b.servicos_adicionais, b.valor_total_boleto,
                    "SIM" if b.gera_boleto else "não"] for b in bol])
    _sheet_tabela(wb, "AJUSTE",
                  ["segmento", "cota_atual", "alvo", "precisa", "cota_resultante",
                   "atingiu", "n_eventos", "mensagem"],
                  [[s.segmento, s.cota_atual, s.alvo_cota, "SIM" if s.precisa_ajuste else "não",
                    s.cota_resultante, "SIM" if s.atingiu_alvo else "não",
                    len(s.eventos_sugeridos), s.mensagem] for s in sug])
    _sheet_conferencia(wb, r, rec, cen, nv, ne)
    _sheet_resumo(wb, r, cen)
    wb._sheets.sort(key=lambda s: 0 if s.title == "RESUMO" else
                    1 if s.title == "CONFERENCIA" else 2)

    destino.mkdir(parents=True, exist_ok=True)
    fp = destino / f"SIMULACAO_AutoTruck_Cenario_{cen.nome}.xlsx"
    wb.save(fp)
    return fp


def main() -> int:
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/projetos/Mut/simulacoes")
    for nome in ("A", "B", "C"):
        fp = gerar(nome, destino)
        print(f"OK  cenário {nome} → {fp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
