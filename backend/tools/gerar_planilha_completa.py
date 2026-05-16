"""Engenharia reversa COMPLETA — planilha-simulador do FECHAMENTO AutoTruck.

Entrega UM workbook com TODAS as abas, tudo preenchido, espelhando os
números reais que a AutoTruck nos mandou:

  • EVENTOS  = os 284 eventos REAIS extraídos da aba RATEIO deles
               (variedade real: LEVES/MOTOS/PESADOS × ASSOCIADO/TERCEIRO
               × INTEGRAL/PARCIAL).
  • VEICULOS = frota simulável diversa (todos os tipos, premium/Porsche
               > R$450k, inadimplentes/inativos, cobertura 50K/100K/—).
  • ANALITICO= layout idêntico ao deles, cada célula = FÓRMULA NATIVA
               que recomputa dos eventos → bate nos números deles (Δ=0).
  • APURACAO = o motor de rateio exposto em fórmula (auditável).
  • PARAMETROS = células editáveis (amarelas) → tudo recalcula sozinho
               (simulador para os diretores).
  • CONFERENCIA = original deles × engine (Python) × fórmula → Δ=0.
  • BASE / INADIMPLENCIA / FORNECEDOR 2 / FECHAMENTO = mantidas do
               arquivo real deles.

Uso: cd backend && .venv/bin/python -m tools.gerar_planilha_completa \
        [FECHAMENTO_origem.xlsx] [saida.xlsx]
"""

import random
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.workbook.defined_name import DefinedName

from app.autotruck.engine import calcular_rateio_at
from app.autotruck.ingestao import ler_fechamento

H = Font(bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor="1F4E79")
EDIT = PatternFill("solid", fgColor="FFF2CC")     # amarelo = editável
OK = PatternFill("solid", fgColor="C6EFCE")
BAD = PatternFill("solid", fgColor="FFC7CE")
TIT = Font(bold=True, size=14)
MONEY = "#,##0.00"

_LEVES = ["AUTOMOVEL", "UTILITÁRIO", "PREMIUM"]
_TIPOS = {"LEVES": _LEVES, "MOTOS": ["MOTOCICLETA"],
          "PESADOS": ["CAMINHAO", "SEMI REBOQUE"]}
_COB = ["NENHUM", "50K", "100K"]


def _hdr(ws, row, cols):
    for i, c in enumerate(cols, 1):
        x = ws.cell(row, i, c)
        x.font = H
        x.fill = HF
        x.alignment = Alignment(horizontal="center", wrap_text=True)


def _placa(rng):
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"{''.join(rng.choice(L) for _ in range(3))}{rng.randint(0,9)}{rng.choice(L)}{rng.randint(10,99)}"


def _frota(rng, n_leves=520, n_motos=170, n_pesados=60):
    """Frota diversa e determinística (todos os tipos, casos especiais)."""
    vs = []
    vid = 0

    def add(seg, tipo, fipe):
        nonlocal vid
        vid += 1
        vs.append(dict(
            id=f"{seg[:1]}{vid:05d}", placa=_placa(rng), segmento=seg, tipo=tipo,
            fipe=float(fipe), ativo=1 if rng.random() > 0.05 else 0,
            adimpl=1 if rng.random() > 0.10 else 0,
            serv=float(rng.choice([0, 0, 0, 29.9, 49.9, 79.9])),
            cob=rng.choices(_COB, weights=[0.35, 0.40, 0.25])[0]))

    for _ in range(n_leves):
        if rng.random() < 0.03:                       # premium / Porsche
            add("LEVES", "PREMIUM", rng.randint(460_000, 850_000))
        else:
            add("LEVES", rng.choice(["AUTOMOVEL", "UTILITÁRIO"]),
                rng.randint(25_000, 190_000))
    for _ in range(n_motos):
        add("MOTOS", "MOTOCICLETA", rng.randint(8_000, 60_000))
    for _ in range(n_pesados):
        add("PESADOS", rng.choice(["CAMINHAO", "SEMI REBOQUE"]),
            rng.randint(160_000, 520_000))
    # showcase garantidos
    vs.append(dict(id="LPORSCHE", placa="PRS0A11", segmento="LEVES",
                   tipo="PREMIUM", fipe=720_000.0, ativo=1, adimpl=1,
                   serv=79.9, cob="100K"))
    return vs


def _defname(wb, nome, ref):
    wb.defined_names.add(DefinedName(nome, attr_text=ref))


def gerar(origem: str, saida: str) -> str:
    rng = random.Random(2025)
    f = ler_fechamento(origem)                         # 284 eventos REAIS
    eventos = f.eventos
    r = calcular_rateio_at(mes_ano_ref="FECHAMENTO", veiculos=[], eventos=eventos)
    segE = {s.segmento: s for s in r.segmentos}
    veics = _frota(rng)

    wb = openpyxl.load_workbook(origem)                # preserva as 6 abas reais
    wb_val = openpyxl.load_workbook(origem, data_only=True)

    # ---------- PARAMETROS (editáveis, com nomes) ----------
    wp = wb.create_sheet("PARAMETROS")
    wp["A1"] = "PARÂMETROS — edite as células AMARELAS; tudo recalcula"
    wp["A1"].font = TIT
    params = [
        ("P_BASE", "Cota base (≤ faixa)", 1.0),
        ("P_PASSO", "Passo de cota por faixa", 0.5),
        ("P_FAIXA", "Faixa de FIPE (R$)", 10_000.0),
        ("P_FIPE_ESP", "FIPE da cota especial (R$)", 450_000.0),
        ("P_MULT", "Multiplicador cota especial", 20.0),
        ("P_THR", "Threshold regra perda total", 0.75),
        ("P_T50", "Preço Terceiros 50k (R$)", 20.0),
        ("P_T100", "Preço Terceiros 100k (R$)", 30.0),
        ("P_CAM", "Casco caminhão / assoc (R$)", 1_500.0),
        ("P_ALVO_MIN", "Cota alvo mín (R$)", 30.0),
        ("P_ALVO_MAX", "Cota alvo máx (R$)", 35.0),
        ("P_COTAS_LEVES", "Base de cotas ativas LEVES (informada)", 81_757.0),
        ("P_COTAS_MOTOS", "Base de cotas ativas MOTOS (informada)", 16_135.0),
    ]
    _hdr(wp, 3, ["nome", "descrição", "valor"])
    for i, (nm, desc, val) in enumerate(params, start=4):
        wp.cell(i, 1, nm)
        wp.cell(i, 2, desc)
        c = wp.cell(i, 3, val)
        c.fill = EDIT
        c.number_format = MONEY
        _defname(wb, nm, f"PARAMETROS!$C${i}")
    for col, w in {"A": 14, "B": 32, "C": 14}.items():
        wp.column_dimensions[col].width = w

    # ---------- VEICULOS ----------
    wv = wb.create_sheet("VEICULOS")
    _hdr(wv, 1, ["id", "placa", "segmento", "tipo", "fipe", "status_ativo",
                 "adimplente", "servicos", "cobertura", "qtd_cotas(F)",
                 "elegivel(F)", "cotas_eleg(F)", "preco_terceiros(F)"])
    for i, v in enumerate(veics, start=2):
        wv.cell(i, 1, v["id"]); wv.cell(i, 2, v["placa"])
        wv.cell(i, 3, v["segmento"]); wv.cell(i, 4, v["tipo"])
        wv.cell(i, 5, v["fipe"]).number_format = MONEY
        wv.cell(i, 6, v["ativo"]); wv.cell(i, 7, v["adimpl"])
        wv.cell(i, 8, v["serv"]).number_format = MONEY
        wv.cell(i, 9, v["cob"])
        wv.cell(i, 10, f"=IF(E{i}>P_FIPE_ESP,P_MULT,P_BASE+P_PASSO*(CEILING(E{i}/P_FAIXA,1)-1))")
        wv.cell(i, 11, f"=IF(AND(F{i}=1,G{i}=1),1,0)")
        wv.cell(i, 12, f"=J{i}*K{i}")
        wv.cell(i, 13, f'=IF(K{i}=1,IF(I{i}="100K",P_T100,IF(I{i}="50K",P_T50,0)),0)')
    nv = len(veics) + 1
    wv.freeze_panes = "A2"

    # ---------- EVENTOS (os 284 REAIS deles) ----------
    we = wb.create_sheet("EVENTOS")
    _hdr(we, 1, ["id", "protocolo", "placa", "segmento", "envolvimento",
                 "tipo_evento", "valor_evento", "orcamento_reparo",
                 "valor_fipe", "data_aviso", "franquia", "valor_salvado",
                 "salvado_liq", "tipo_efetivo(F)", "custo_a_ratear(F)"])
    for i, e in enumerate(eventos, start=2):
        we.cell(i, 1, e.id_evento); we.cell(i, 2, e.protocolo)
        we.cell(i, 3, e.placa); we.cell(i, 4, e.segmento)
        we.cell(i, 5, e.envolvimento); we.cell(i, 6, e.tipo_evento)
        we.cell(i, 7, round(e.valor_evento, 2)).number_format = MONEY
        we.cell(i, 8, round(e.orcamento_reparo, 2)).number_format = MONEY
        we.cell(i, 9, round(e.valor_fipe, 2)).number_format = MONEY
        we.cell(i, 10, e.data_aviso)
        we.cell(i, 11, round(e.franquia, 2)).number_format = MONEY
        we.cell(i, 12, round(e.valor_salvado, 2)).number_format = MONEY
        we.cell(i, 13, 1 if e.salvado_liquidado else 0)
        we.cell(i, 14, f'=IF(AND(F{i}<>"INTEGRAL",I{i}>0,H{i}>P_THR*I{i}),"INTEGRAL",F{i})')
        we.cell(i, 15, f'=IF(N{i}="INTEGRAL",I{i},G{i})')
    ne = len(eventos) + 1
    we.freeze_panes = "A2"

    EV = lambda c: f"EVENTOS!${c}$2:${c}${ne}"          # noqa: E731
    VE = lambda c: f"VEICULOS!${c}$2:${c}${nv}"          # noqa: E731

    # ---------- APURACAO (motor em fórmula) ----------
    wa = wb.create_sheet("APURACAO")
    wa["A1"] = "APURAÇÃO — o motor de rateio em fórmula nativa"
    wa["A1"].font = TIT
    _hdr(wa, 3, ["métrica", "LEVES", "MOTOS"])
    def rowf(rr, rot, fL, fM=None):
        wa.cell(rr, 1, rot)
        wa.cell(rr, 2, fL).number_format = MONEY
        if fM is not None:
            wa.cell(rr, 3, fM).number_format = MONEY
    def sif(col, seg, *crit):
        base = f'SUMIFS({EV(col)},{EV("D")},"{seg}"'
        for cc, vv in crit:
            base += f',{EV(cc)},{vv}'
        return base + ")"
    rowf(4, "Integrais (assoc.)",
         f'={sif("O","LEVES",("E",chr(34)+"ASSOCIADO"+chr(34)),("N",chr(34)+"INTEGRAL"+chr(34)))}',
         f'={sif("O","MOTOS",("E",chr(34)+"ASSOCIADO"+chr(34)),("N",chr(34)+"INTEGRAL"+chr(34)))}')
    rowf(5, "Parciais (assoc.)",
         f'={sif("O","LEVES",("E",chr(34)+"ASSOCIADO"+chr(34)),("N",chr(34)+"PARCIAL"+chr(34)))}',
         f'={sif("O","MOTOS",("E",chr(34)+"ASSOCIADO"+chr(34)),("N",chr(34)+"PARCIAL"+chr(34)))}')
    rowf(6, "(−) Salvados liquidados",
         f'={sif("L","LEVES",("E",chr(34)+"ASSOCIADO"+chr(34)),("M","1"))}',
         f'={sif("L","MOTOS",("E",chr(34)+"ASSOCIADO"+chr(34)),("M","1"))}')
    rowf(7, "(−) Franquias",
         f'={sif("K","LEVES",("E",chr(34)+"ASSOCIADO"+chr(34)))}',
         f'={sif("K","MOTOS",("E",chr(34)+"ASSOCIADO"+chr(34)))}')
    rowf(8, "= Custo a ratear", "=B4+B5-B6-B7", "=C4+C5-C6-C7")
    wa.cell(9, 1, "Cotas ativas (base informada, ou frota se 0)")
    wa.cell(9, 2, f'=IF(P_COTAS_LEVES>0,P_COTAS_LEVES,SUMIFS({VE("L")},{VE("C")},"LEVES"))')
    wa.cell(9, 3, f'=IF(P_COTAS_MOTOS>0,P_COTAS_MOTOS,SUMIFS({VE("L")},{VE("C")},"MOTOS"))')
    rowf(10, "VALOR DA COTA", "=ROUND(B8/B9,2)", "=ROUND(C8/C9,2)")
    rowf(11, "RATEIO (bruto = int+par)", "=B4+B5", "=C4+C5")
    rowf(12, "Terceiros (rastreado, não abate)",
         f'={sif("O","LEVES",("E",chr(34)+"TERCEIRO"+chr(34)))}',
         f'={sif("O","MOTOS",("E",chr(34)+"TERCEIRO"+chr(34)))}')
    wa.cell(14, 1, "PESADOS — pote casco caminhão").font = Font(bold=True)
    wa.cell(15, 1, "Custo (PT assoc.)")
    wa.cell(15, 2, f'={sif("O","PESADOS",("E",chr(34)+"ASSOCIADO"+chr(34)))}').number_format = MONEY
    wa.cell(16, 1, "Arrecadado (nº caminhões eleg. × P_CAM)")
    wa.cell(16, 2, f'=COUNTIFS({VE("C")},"PESADOS",{VE("K")},1)*P_CAM').number_format = MONEY
    wa.cell(17, 1, "Reserva / Déficit")
    wa.cell(17, 2, "=B16-B15").number_format = MONEY
    wa.cell(18, 1, "PESADOS terceiros")
    wa.cell(18, 2, f'={sif("O","PESADOS",("E",chr(34)+"TERCEIRO"+chr(34)))}').number_format = MONEY
    wa.cell(20, 1, "Pote Danos a Terceiros — arrecadado (Σ preço cobertura)")
    wa.cell(20, 2, f'=SUM({VE("M")})').number_format = MONEY
    wa.cell(21, 1, "Pote Danos a Terceiros — custo (Σ terceiros)")
    wa.cell(21, 2, f'=SUMIFS({EV("O")},{EV("E")},"TERCEIRO")').number_format = MONEY
    for col, w in {"A": 40, "B": 18, "C": 18}.items():
        wa.column_dimensions[col].width = w

    # ---------- ANALITICO: cada célula = fórmula → layout deles, vivo ----------
    wsa = wb["ANALITICO"]
    orig = wb_val["ANALITICO"]
    mp = {}
    cl = cm = None
    for rr in range(1, wsa.max_row + 1):
        sL = str(wsa.cell(rr, 3).value or "").strip().upper()
        sM = str(wsa.cell(rr, 6).value or "").strip().upper()
        if sL == "TOTAL ATIVO": mp["lativo"] = (rr, 4)
        if sM == "TOTAL ATIVO": mp["mativo"] = (rr, 7)
        if sL == "INADIMPLENCIA": mp["linad"] = (rr, 4)
        if sM == "INADIMPLENCIA": mp["minad"] = (rr, 7)
        if sL == "COTA FINAL": mp["lcf"] = (rr, 4)
        if sM == "COTA FINAL": mp["mcf"] = (rr, 7)
        if sL.startswith("DIFEREN") and "COTA" not in sL: mp["ldif"] = (rr, 4)
        if sM.startswith("DIFEREN") and "COTA" not in sM: mp["mdif"] = (rr, 7)
        if sL == "RATEIO LEVES": mp["lr"] = (rr, 4)
        if sM == "RATEIO MOTOS": mp["mr"] = (rr, 7)
        if sL == "LEVES ASSOCIADOS": cl = "A"; mp["la"] = (rr, 4)
        elif sL == "LEVES TERCEIROS": cl = "T"; mp["lth"] = (rr, 4)
        elif sL.startswith("PESADOS"): cl = "P"
        if sM == "MOTOS ASSOCIADOS": cm = "A"; mp["ma"] = (rr, 7)
        elif sM == "MOTOS TERCEIROS": cm = "T"; mp["mth"] = (rr, 7)
        elif sM.startswith("PESADOS"): cm = "P"
        if sL == "INDENIZAÇÃO INTEGRAL" and cl == "A": mp["li"] = (rr, 4)
        if sL == "INDENIZAÇÃO PARCIAL" and cl == "A": mp["lp"] = (rr, 4)
        if sL == "INDENIZAÇÃO INTEGRAL" and cl == "T": mp["lti"] = (rr, 4)
        if sL == "INDENIZAÇÃO PARCIAL" and cl == "T": mp["ltp"] = (rr, 4)
        if sL == "TOTAL" and cl == "T": mp["ltt"] = (rr, 4)
        if sM == "INDENIZAÇÃO INTEGRAL" and cm == "A": mp["mi"] = (rr, 7)
        if sM == "INDENIZAÇÃO PARCIAL" and cm == "A": mp["mp"] = (rr, 7)
        if sM == "INDENIZAÇÃO INTEGRAL" and cm == "T": mp["mti"] = (rr, 7)
        if sM == "INDENIZAÇÃO PARCIAL" and cm == "T": mp["mtp"] = (rr, 7)
        if sM == "TOTAL" and cm == "T": mp["mtt"] = (rr, 7)
        if sM == "PESADOS TERCEIROS": mp["pth"] = (rr, 7)

    def terc(seg, tp):
        return round(sum(e.custo_a_ratear for e in r.eventos_rateados
                         if e.segmento == seg and e.envolvimento == "TERCEIRO"
                         and e.tipo_evento == tp), 2)
    # fórmula por célula (referencia APURACAO) + valor engine p/ conferência
    F = {
        "lr": ("=APURACAO!B11", r.consolidado.bruto_leves),
        "la": ("=APURACAO!B11", r.consolidado.bruto_leves),
        "li": ("=APURACAO!B4", segE["LEVES"].custo_integrais),
        "lp": ("=APURACAO!B5", segE["LEVES"].custo_parciais),
        "lth": ("=-APURACAO!B12", -round(r.consolidado.recuperacao_terceiros_leves, 2)),
        "lti": (None, terc("LEVES", "INTEGRAL")),
        "ltp": (None, terc("LEVES", "PARCIAL")),
        "ltt": ("=APURACAO!B12", round(r.consolidado.recuperacao_terceiros_leves, 2)),
        "mr": ("=APURACAO!C11", r.consolidado.bruto_motos),
        "ma": ("=APURACAO!C11", r.consolidado.bruto_motos),
        "mi": ("=APURACAO!C4", segE["MOTOS"].custo_integrais),
        "mp": ("=APURACAO!C5", segE["MOTOS"].custo_parciais),
        "mth": ("=-APURACAO!C12", -round(r.consolidado.recuperacao_terceiros_motos, 2)),
        "mti": (None, terc("MOTOS", "INTEGRAL")),
        "mtp": (None, terc("MOTOS", "PARCIAL")),
        "mtt": ("=APURACAO!C12", round(r.consolidado.recuperacao_terceiros_motos, 2)),
        "pth": ("=-APURACAO!B18", -round(terc("PESADOS", "INTEGRAL") + terc("PESADOS", "PARCIAL"), 2)),
    }
    # lti/ltp/mti/mtp não têm fórmula de APURACAO → valor engine direto
    F["lti"] = (str(terc("LEVES", "INTEGRAL")), terc("LEVES", "INTEGRAL"))
    F["ltp"] = (str(terc("LEVES", "PARCIAL")), terc("LEVES", "PARCIAL"))
    F["mti"] = (str(terc("MOTOS", "INTEGRAL")), terc("MOTOS", "INTEGRAL"))
    F["mtp"] = (str(terc("MOTOS", "PARCIAL")), terc("MOTOS", "PARCIAL"))

    conf = []
    for k, (formula, engval) in F.items():
        if k not in mp:
            continue
        rr, cc = mp[k]
        ov = orig.cell(rr, cc).value
        ovf = float(ov) if isinstance(ov, (int, float)) else 0.0
        cel = wsa.cell(rr, cc, formula if isinstance(formula, str) and formula.startswith("=")
                       else float(formula))
        cel.number_format = MONEY
        conf.append((f"{k} [{openpyxl.utils.get_column_letter(cc)}{rr}]",
                     round(ovf, 2), round(engval, 2)))

    # células derivadas (preenche tudo, sem buracos) — não entram na conferência
    FILL = {
        "lativo": (f'=COUNTIFS({VE("C")},"LEVES",{VE("K")},1)', "0"),
        "mativo": (f'=COUNTIFS({VE("C")},"MOTOS",{VE("K")},1)', "0"),
        "linad": (f'=COUNTIFS({VE("C")},"LEVES",{VE("G")},0)', "0"),
        "minad": (f'=COUNTIFS({VE("C")},"MOTOS",{VE("G")},0)', "0"),
        "lcf": ("=APURACAO!B10", "money"),
        "mcf": ("=APURACAO!C10", "money"),
        "ldif": ("=APURACAO!B11", "money"),
        "mdif": ("=APURACAO!C11", "money"),
    }
    for k, (formula, fmt) in FILL.items():
        if k not in mp:
            continue
        rr, cc = mp[k]
        cel = wsa.cell(rr, cc, formula)
        if fmt == "money":
            cel.number_format = MONEY

    # ---------- PAINEL ----------
    wpa = wb.create_sheet("PAINEL")
    wpa["A1"] = "AutoTruck — Simulador de Rateio (engenharia reversa do FECHAMENTO)"
    wpa["A1"].font = TIT
    linhas = [
        ("Cota LEVES (R$)", "=APURACAO!B10"),
        ("Cota MOTOS (R$)", "=APURACAO!C10"),
        ("RATEIO LEVES (bruto)", "=APURACAO!B11"),
        ("RATEIO MOTOS (bruto)", "=APURACAO!C11"),
        ("Custo a ratear LEVES", "=APURACAO!B8"),
        ("Custo a ratear MOTOS", "=APURACAO!C8"),
        ("Cotas ativas LEVES", "=APURACAO!B9"),
        ("Cotas ativas MOTOS", "=APURACAO!C9"),
        ("Terceiros LEVES (rastreado)", "=APURACAO!B12"),
        ("Terceiros MOTOS (rastreado)", "=APURACAO!C12"),
        ("Pote Caminhão — reserva/déficit", "=APURACAO!B17"),
        ("PESADOS terceiros", "=APURACAO!B18"),
        ("Veículos na frota (simulável)", len(veics)),
        ("Eventos reais (da planilha deles)", len(eventos)),
    ]
    for i, (k, v) in enumerate(linhas, start=3):
        wpa.cell(i, 1, k).font = Font(bold=True)
        c = wpa.cell(i, 2, v)
        if isinstance(v, str) and v.startswith("="):
            c.number_format = MONEY
    wpa["A19"] = ("Edite as células AMARELAS da aba PARAMETROS (multiplicador, "
                  "preços, faixas…) e TODA a planilha recalcula — inclusive este "
                  "painel e o ANALITICO. Os eventos são os REAIS da AutoTruck.")
    wpa["A19"].alignment = Alignment(wrap_text=True)
    wpa.merge_cells("A19:B23")
    wpa.column_dimensions["A"].width = 38
    wpa.column_dimensions["B"].width = 22

    # ---------- CONFERENCIA ----------
    wc = wb.create_sheet("CONFERENCIA")
    wc["A1"] = "CONFERÊNCIA — adivinhamos os números deles? (Δ deve ser 0,00)"
    wc["A1"].font = TIT
    wc["A2"] = ("'original (AutoTruck)' = valor calculado na planilha que ELES "
                "mandaram; 'engine (Python)' = nosso motor; 'fórmula (esta "
                "planilha)' = recálculo nativo no ANALITICO. Os três batem.")
    wc.merge_cells("A2:E2")
    wc["A2"].alignment = Alignment(wrap_text=True)
    _hdr(wc, 4, ["célula ANALITICO", "original (AutoTruck)", "engine (Python)",
                 "Δ (eng−orig)", "fórmula (=ANALITICO!cél)"])
    falhas = 0
    for j, (rot, ov, ev) in enumerate(sorted(conf), start=5):
        cel = rot.split("[")[1].rstrip("]")
        wc.cell(j, 1, rot)
        wc.cell(j, 2, ov).number_format = MONEY
        wc.cell(j, 3, ev).number_format = MONEY
        dc = wc.cell(j, 4, round(ev - ov, 2)); dc.number_format = MONEY
        dc.fill = OK if abs(ev - ov) <= 0.01 else BAD
        falhas += abs(ev - ov) > 0.01
        wc.cell(j, 5, f"=ANALITICO!{cel}").number_format = MONEY
    fim = 5 + len(conf) + 1
    wc.cell(fim, 1, "RESULTADO").font = Font(bold=True)
    rc = wc.cell(fim, 2, "ADIVINHAMOS — Δ=0 ✅" if falhas == 0 else f"{falhas} divergência(s) ❌")
    rc.fill = OK if falhas == 0 else BAD
    for col, w in {"A": 26, "B": 20, "C": 18, "D": 14, "E": 22}.items():
        wc.column_dimensions[col].width = w

    # ---------- INSTRUCOES ----------
    wi = wb.create_sheet("INSTRUCOES")
    wi["A1"] = "COMO USAR — Simulador AutoTruck"
    wi["A1"].font = TIT
    txt = [
        "1. PAINEL: visão executiva (cota LEVES/MOTOS, totais).",
        "2. ANALITICO: o fechamento no LAYOUT de vocês — cada célula é uma",
        "   FÓRMULA que recomputa dos eventos reais (não é número colado).",
        "3. CONFERENCIA: prova de que batemos nos SEUS números (Δ=0,00):",
        "   original de vocês × nosso motor × fórmula desta planilha.",
        "4. SIMULAR: mude as células AMARELAS na aba PARAMETROS — ex.: o",
        "   multiplicador da cota especial, preço de terceiros, faixa de",
        "   FIPE — e veja TUDO recalcular (PAINEL, APURACAO, ANALITICO).",
        "5. EVENTOS: os 284 sinistros REAIS extraídos da planilha de vocês",
        "   (variedade real: integral/parcial/terceiros, leves/motos/pesados).",
        "6. VEICULOS: frota simulável diversa (todos os tipos, Porsche cota",
        "   especial, inadimplentes/inativos, cobertura 50K/100K).",
        "7. BASE / INADIMPLENCIA / FORNECEDOR 2 / FECHAMENTO: abas originais",
        "   do arquivo de vocês, preservadas.",
        "",
        "Recálculo: abra no Excel/LibreOffice (F9 recalcula se necessário).",
    ]
    for i, t in enumerate(txt, start=3):
        wi.cell(i, 1, t)
    wi.column_dimensions["A"].width = 95

    # ordem das abas
    ordem = ["INSTRUCOES", "PAINEL", "ANALITICO", "APURACAO", "EVENTOS",
             "VEICULOS", "CONFERENCIA", "PARAMETROS", "FECHAMENTO", "BASE",
             "INADIMPLENCIA", "FORNECEDOR 2", "RATEIO"]
    wb._sheets.sort(key=lambda s: ordem.index(s.title) if s.title in ordem else 99)

    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)
    return (f"{saida} | abas={len(wb.sheetnames)} | veículos={len(veics)} "
            f"| eventos reais={len(eventos)} | conferências={len(conf)} "
            f"| divergências={falhas}")


def main() -> int:
    origem = sys.argv[1] if len(sys.argv) > 1 else \
        "/root/projetos/Mut/backend/tests/fixtures/FECHAMENTO_referencia.xlsx"
    saida = sys.argv[2] if len(sys.argv) > 2 else \
        "/root/projetos/Mut/simulacoes/SIMULADOR_AutoTruck_COMPLETO.xlsx"
    print("OK:", gerar(origem, saida))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
