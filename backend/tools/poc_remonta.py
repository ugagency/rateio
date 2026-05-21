"""PoC Remonta — roda o motor AutoTruck sobre BASE + RATEIO da reunião 19/05.

Lê as planilhas que o Rodrigo entregou (Remonta/BASE_Reconstruida.xlsx e
Remonta/Rateio_POC_Completo.xlsx) e demonstra o rateio acontecendo:

- BASE  → denominador (cotas ativas e adimplentes por segmento) +
          fotografia da inadimplência por produto
- RATEIO → numerador (eventos do mês abr/26, com Tipo/Envolvimento/Valor
           Rateado/Participação por bloco)

Saídas:

- simulacoes/POC_REMONTA_abr26.xlsx — 4 abas:
    INPUT_BASE        snapshot do que foi lido da BASE
    INPUT_EVENTOS     eventos extraídos do Rateio POC
    MEMORIA_CALCULO   fórmulas Excel nativas reproduzindo o motor por segmento
    ANALITICO_SAIDA   layout familiar (cotas/inadimplência/rateio/cota final)
- docs/evidencias/POC_REMONTA_abr26.txt — trilha textual reproduzível.

Uso: cd backend && .venv/bin/python -m tools.poc_remonta
        [BASE.xlsx] [Rateio.xlsx] [saida_xlsx] [saida_txt]
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from app.autotruck.domain import EventoAT, VeiculoAT
from app.autotruck.engine import calcular_rateio_at
from app.autotruck.rules import PARAMS_DEFAULT, ParametrosAT

# ------------------------------------------------------------------
# Parsing utilitário
# ------------------------------------------------------------------

_BR_NUM = re.compile(r"-?\d[\d\.]*,?\d*")


def _to_float(v) -> float:
    """Aceita número, 'R$ 1.234,56', '7706.1', 'R$ -', None — devolve float."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s in {"R$ -", "-", "R$ ###"}:
        return 0.0
    m = _BR_NUM.search(s.replace("R$", ""))
    if not m:
        return 0.0
    txt = m.group(0)
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return 0.0


def _data_iso(s: str) -> str:
    """'25/11/2025' → '2025-11-25'. Aceita já-ISO."""
    if not s:
        return "2026-04-01"
    s = str(s).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    try:
        return datetime.strptime(s, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return "2026-04-01"


# ------------------------------------------------------------------
# Leitura da BASE
# ------------------------------------------------------------------

# Layout (BASE_Reconstruida.xlsx, aba BASE):
#   col A-E   → PESADO (Valor Classif, Valor Produto, Qtd Boletos, Cota Situação)
#   col G-K   → MOTO   (idem)
#   col N-R   → LEVE   (idem)
#
# Cota por Situação (BAIXADO / ABERTO) é a única fonte direta do denominador.
COLS_SEG = {
    "PESADOS": dict(desc=1, ab=2, bx=3, can=4, tot=5),  # A..E
    "MOTOS":   dict(desc=7, ab=8, bx=9, can=10, tot=11),  # G..K
    "LEVES":   dict(desc=14, ab=15, bx=16, can=17, tot=18),  # N..R
}


def _ler_base(path: Path) -> dict:
    """Devolve {segmento: {'cotas_baixadas','cotas_abertas','cotas_canceladas',
    'rateio_baixado','rateio_aberto','inadimplencia_total','valor_classificacao':[(desc,baixado,aberto)]}}.

    Cota por Situação aparece no rodapé de cada coluna ('Cota por Situação de
    Boleto'). Quando ausente (LEVES, na versão do Rodrigo), `cotas_baixadas`
    fica como `None` e o caller decide o fallback.
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active  # aba BASE
    nrow, ncol = ws.max_row, ws.max_column

    saida = {}
    for seg, cols in COLS_SEG.items():
        info = {
            "cotas_baixadas": None, "cotas_abertas": None, "cotas_canceladas": None,
            "rateio_baixado": 0.0, "rateio_aberto": 0.0,
            "valor_classificacao": [],
        }
        # 1) Cota por Situação — busca pelo label
        for r in range(1, nrow + 1):
            v = ws.cell(r, cols["desc"]).value
            if v and "Cota por Situa" in str(v):
                # valores podem estar na própria linha (se label compartilha) ou na seguinte
                for r2 in (r, r + 1):
                    if r2 > nrow:
                        break
                    a, b, c = (ws.cell(r2, cols["ab"]).value,
                                ws.cell(r2, cols["bx"]).value,
                                ws.cell(r2, cols["can"]).value)
                    if any(_to_float(x) > 0 for x in (a, b, c)):
                        # ordem na planilha = (BAIXADO, ABERTO, CANCELADO) ou
                        # (ABERTO, BAIXADO, CANCELADO) — heurística: o maior é BAIXADO.
                        vals = [_to_float(a), _to_float(b), _to_float(c)]
                        bx = max(vals)
                        ab = sorted(vals)[-2]
                        can = min(vals)
                        info["cotas_baixadas"] = bx
                        info["cotas_abertas"] = ab
                        info["cotas_canceladas"] = can
                        break
                if info["cotas_baixadas"] is not None:
                    break
        # 2) Valor de Classificação — primeira tabela com header DESCRIÇÃO
        in_block, header_row = False, None
        for r in range(1, nrow + 1):
            v = ws.cell(r, cols["desc"]).value
            if v and "Valor de Classifica" in str(v):
                in_block = True
                continue
            if in_block and v and str(v).strip().upper() == "DESCRIÇÃO":
                header_row = r
                break
        if header_row:
            for r in range(header_row + 1, nrow + 1):
                desc = ws.cell(r, cols["desc"]).value
                if not desc or "Valor de Produto" in str(desc) or str(desc).strip().upper() == "TOTAL":
                    if str(desc).strip().upper() == "TOTAL":
                        # captura totais
                        info["total_aberto_classif"] = _to_float(ws.cell(r, cols["ab"]).value)
                        info["total_baixado_classif"] = _to_float(ws.cell(r, cols["bx"]).value)
                    break
                info["valor_classificacao"].append((
                    str(desc).strip(),
                    _to_float(ws.cell(r, cols["bx"]).value),
                    _to_float(ws.cell(r, cols["ab"]).value),
                ))
                if str(desc).strip().upper() == "RATEIO":
                    info["rateio_baixado"] = _to_float(ws.cell(r, cols["bx"]).value)
                    info["rateio_aberto"] = _to_float(ws.cell(r, cols["ab"]).value)
        saida[seg] = info
    return saida


# ------------------------------------------------------------------
# Leitura do Rateio POC
# ------------------------------------------------------------------

# Cada bloco começa com um título (e.g. 'LEVES ASSOCIADOS'), seguido de
# subtítulos por Tipo Evento ('INDENIZAÇÃO INTEGRAL' / 'INDENIZAÇÃO PARCIAL')
# e tabelas com header começando em 'Protocolo'.
HEADER_PROTOCOLO = "Protocolo"

# Títulos conhecidos → (segmento, envolvimento). 'PESADOS TERCEIROS' é
# meramente demonstrativo (não rateia), mas é registrado.
TITULOS = {
    "PESADOS TERCEIROS": ("PESADOS", "TERCEIRO"),
    "MOTOS ASSOCIADOS":  ("MOTOS",  "ASSOCIADO"),
    "MOTOS TERCEIROS":   ("MOTOS",  "TERCEIRO"),
    "LEVES ASSOCIADOS":  ("LEVES",  "ASSOCIADO"),
    "LEVES TERCEIROS":   ("LEVES",  "TERCEIRO"),
}


def _ler_rateio(path: Path) -> list[dict]:
    """Lê todos os eventos em formato dict bruto (uma linha por evento)."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    eventos = []
    segmento, envolvimento, tipo_evento = None, None, None
    in_table = False
    for r in range(1, ws.max_row + 1):
        a = ws.cell(r, 1).value
        b = ws.cell(r, 2).value
        if a and str(a).strip().upper() in TITULOS:
            segmento, envolvimento = TITULOS[str(a).strip().upper()]
            tipo_evento = None
            in_table = False
            continue
        # subtítulo (col B) anunciando tipo — só vale quando NÃO estamos
        # numa tabela ativa (o mesmo texto se repete em cada linha de dado).
        if not in_table and a is None and b:
            txt = str(b).upper()
            if "INTEGRAL" in txt:
                tipo_evento = "INTEGRAL"; continue
            if "PARCIAL" in txt:
                tipo_evento = "PARCIAL"; continue
        if a and str(a).strip() == HEADER_PROTOCOLO:
            in_table = True; continue
        if not in_table:
            continue
        # linha de dado
        protocolo = a
        if protocolo is None:
            in_table = False
            continue
        eventos.append({
            "segmento": segmento, "envolvimento": envolvimento,
            "tipo_evento": tipo_evento,
            "protocolo": str(protocolo),
            "motivo": ws.cell(r, 3).value, "situacao": ws.cell(r, 5).value,
            "placa": ws.cell(r, 6).value or f"AUTO-{r}",
            "participacao": _to_float(ws.cell(r, 7).value),
            "data_aviso": _data_iso(ws.cell(r, 8).value),
            "mes_ref": ws.cell(r, 10).value,
            "valor_rateado": _to_float(ws.cell(r, 11).value),
        })
    return eventos


# ------------------------------------------------------------------
# Montagem do input do motor
# ------------------------------------------------------------------

# Fallback de cotas LEVES — a planilha entregue (BASE_Reconstruida) não
# trouxe o quadro de Cota por Situação para LEVES; estimativa baseada na
# faixa típica de cota LEVES R$ 30–35 sobre o total a ratear LEVES do mês.
COTAS_LEVES_FALLBACK = 30_000


def _montar_input(base: dict, eventos: list[dict]) -> tuple[list[VeiculoAT], list[EventoAT], dict]:
    """Cria veículos sintéticos (1 cota cada, FIPE=10k) representando o
    denominador e converte eventos brutos para EventoAT.

    Em INTEGRAL o motor usa `valor_fipe`; em PARCIAL usa `valor_evento`. Em
    ambos descontamos `franquia` (= Participação). Assim:
        custo a ratear no motor = (VR + Part) - Part = VR  ✓
    O `valor_fipe` para PARCIAL fica suficientemente alto para não disparar
    a regra dos 75% (que reclassificaria como INTEGRAL).
    """
    cotas = {
        "LEVES":   int(base["LEVES"].get("cotas_baixadas") or COTAS_LEVES_FALLBACK),
        "MOTOS":   int(base["MOTOS"].get("cotas_baixadas") or 0),
        "PESADOS": int(base["PESADOS"].get("cotas_baixadas") or 0),
    }
    veiculos: list[VeiculoAT] = []
    for seg, n in cotas.items():
        for i in range(1, n + 1):
            veiculos.append(VeiculoAT(
                id_veiculo=f"{seg[:3]}-{i:05d}", placa=f"{seg[:3]}{i:05d}",
                segmento=seg, tipo_veiculo="AUTOMOVEL" if seg == "LEVES" else (
                    "MOTOCICLETA" if seg == "MOTOS" else "CAMINHAO"),
                valor_fipe=10_000.0,   # = 1 cota base
                status_ativo=True, adimplente=True,
                servicos_adicionais=0.0, cobertura_terceiros="NENHUM",
            ))

    eventos_at: list[EventoAT] = []
    for i, e in enumerate(eventos, start=1):
        vr = e["valor_rateado"]; part = e["participacao"]
        bruto = vr + part
        if e["tipo_evento"] == "INTEGRAL":
            valor_fipe = bruto
            valor_evento = bruto
        else:  # PARCIAL
            valor_evento = bruto
            valor_fipe = bruto / 0.5  # garante <0.75 → não reclassifica
        eventos_at.append(EventoAT(
            id_evento=f"EV-{i:04d}",
            protocolo=str(e["protocolo"]),
            placa=str(e["placa"]),
            segmento=e["segmento"],
            envolvimento=e["envolvimento"],
            tipo_evento=e["tipo_evento"],
            valor_evento=valor_evento,
            orcamento_reparo=valor_evento,
            valor_fipe=valor_fipe,
            data_aviso=e["data_aviso"],
            franquia=part,
        ))
    return veiculos, eventos_at, cotas


# ------------------------------------------------------------------
# Saída — planilha Excel
# ------------------------------------------------------------------

HDR_FILL = PatternFill("solid", fgColor="1F4E79")
HDR_FONT = Font(bold=True, color="FFFFFF")
SUB_FILL = PatternFill("solid", fgColor="DDEBF7")
SUB_FONT = Font(bold=True)
THIN = Side(border_style="thin", color="9BC2E6")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CURRENCY = u'_-"R$" * #,##0.00_-;-"R$" * #,##0.00_-;_-"R$" * "-"??_-;_-@_-'


def _hdr(ws, row, cols):
    for c, txt in enumerate(cols, start=1):
        cell = ws.cell(row=row, column=c, value=txt)
        cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.border = BOX
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _sub(ws, row, col_ini, txt, span=1):
    cell = ws.cell(row=row, column=col_ini, value=txt)
    cell.fill = SUB_FILL; cell.font = SUB_FONT
    if span > 1:
        ws.merge_cells(start_row=row, start_column=col_ini,
                       end_row=row, end_column=col_ini + span - 1)


def _gerar_xlsx(saida: Path, base: dict, eventos: list[dict], cotas: dict, resultado, params: ParametrosAT):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ------------------ INPUT_BASE
    ws = wb.create_sheet("INPUT_BASE")
    _hdr(ws, 1, ["Segmento", "Cotas BAIXADAS (denominador)",
                  "Cotas ABERTAS (inadimplentes)", "R$ Rateio BAIXADO",
                  "R$ Rateio ABERTO", "Fonte"])
    for r, seg in enumerate(["LEVES", "MOTOS", "PESADOS"], start=2):
        b = base[seg]
        fonte = "BASE_Reconstruida.xlsx" if b.get("cotas_baixadas") else (
            f"fallback (estimativa = {COTAS_LEVES_FALLBACK} cotas)" if seg == "LEVES" else "ausente")
        ws.cell(r, 1, seg).font = SUB_FONT
        ws.cell(r, 2, cotas[seg])
        ws.cell(r, 3, b.get("cotas_abertas") or 0)
        ws.cell(r, 4, b.get("rateio_baixado") or 0).number_format = CURRENCY
        ws.cell(r, 5, b.get("rateio_aberto") or 0).number_format = CURRENCY
        ws.cell(r, 6, fonte)
        for c in range(1, 7):
            ws.cell(r, c).border = BOX
    for col, w in {"A": 12, "B": 26, "C": 26, "D": 22, "E": 22, "F": 36}.items():
        ws.column_dimensions[col].width = w

    # ------------------ INPUT_EVENTOS
    ws = wb.create_sheet("INPUT_EVENTOS")
    _hdr(ws, 1, ["Segmento", "Envolvimento", "Tipo", "Protocolo", "Placa",
                  "Data Aviso", "Participação", "Valor Rateado", "Motivo"])
    for r, e in enumerate(eventos, start=2):
        ws.cell(r, 1, e["segmento"]); ws.cell(r, 2, e["envolvimento"])
        ws.cell(r, 3, e["tipo_evento"]); ws.cell(r, 4, str(e["protocolo"]))
        ws.cell(r, 5, str(e["placa"])); ws.cell(r, 6, e["data_aviso"])
        ws.cell(r, 7, e["participacao"]).number_format = CURRENCY
        ws.cell(r, 8, e["valor_rateado"]).number_format = CURRENCY
        ws.cell(r, 9, e["motivo"] or "")
        for c in range(1, 10):
            ws.cell(r, c).border = BOX
    ws.freeze_panes = "A2"
    for col, w in {"A": 10, "B": 12, "C": 10, "D": 14, "E": 12, "F": 12,
                    "G": 16, "H": 18, "I": 36}.items():
        ws.column_dimensions[col].width = w

    # ------------------ MEMORIA_CALCULO (fórmulas Excel nativas)
    ws = wb.create_sheet("MEMORIA_CALCULO")
    ws["A1"] = "Memória de cálculo — fórmulas Excel reproduzindo o motor AutoTruck"
    ws["A1"].font = Font(bold=True, size=12)
    ws.merge_cells("A1:H1")
    _sub(ws, 3, 1, "Por segmento (LEVES e MOTOS = rateio variável)", span=8)
    _hdr(ws, 4, [
        "Segmento",
        "Σ Integral ASSOC (a)",
        "Σ Parcial ASSOC (b)",
        "Σ Participação (c=franquia)",
        "Σ Salvado (d)",
        "Custo a Ratear  =a+b-c-d",
        "Cotas (denominador)",
        "Cota mensal = custo / cotas",
    ])
    # Referências à aba INPUT_EVENTOS para somar via SUMIFS
    EV = "INPUT_EVENTOS"
    n = len(eventos) + 1  # última linha
    for r, seg in enumerate(["LEVES", "MOTOS"], start=5):
        # a = SUMIFS(VR, seg=SEG, env=ASSOCIADO, tipo=INTEGRAL)
        ws.cell(r, 1, seg).font = SUB_FONT
        ws.cell(r, 2, f'=SUMIFS({EV}!H2:H{n},{EV}!A2:A{n},"{seg}",'
                       f'{EV}!B2:B{n},"ASSOCIADO",{EV}!C2:C{n},"INTEGRAL")')
        ws.cell(r, 3, f'=SUMIFS({EV}!H2:H{n},{EV}!A2:A{n},"{seg}",'
                       f'{EV}!B2:B{n},"ASSOCIADO",{EV}!C2:C{n},"PARCIAL")')
        ws.cell(r, 4, 0.0)  # Participação já está embutida no VR (= bruto - part)
        ws.cell(r, 5, 0.0)  # sem salvado nessa PoC
        ws.cell(r, 6, f"=B{r}+C{r}-D{r}-E{r}")
        ws.cell(r, 7, cotas[seg])
        ws.cell(r, 8, f"=IF(G{r}=0,0,F{r}/G{r})")
        for c in (2, 3, 4, 5, 6, 8):
            ws.cell(r, c).number_format = CURRENCY
            ws.cell(r, c).border = BOX
        ws.cell(r, 1).border = BOX; ws.cell(r, 7).border = BOX

    _sub(ws, 8, 1, "Recuperação de Terceiros (NÃO abate a cota — produto à parte)", span=8)
    _hdr(ws, 9, ["Segmento", "Σ Terceiros (PARCIAL+INTEGRAL)", "", "", "", "", "", ""])
    for r, seg in enumerate(["LEVES", "MOTOS"], start=10):
        ws.cell(r, 1, seg).font = SUB_FONT
        ws.cell(r, 2, f'=SUMIFS({EV}!H2:H{n},{EV}!A2:A{n},"{seg}",{EV}!B2:B{n},"TERCEIRO")')
        ws.cell(r, 2).number_format = CURRENCY; ws.cell(r, 2).border = BOX
        ws.cell(r, 1).border = BOX

    _sub(ws, 13, 1, "PESADOS — demonstrativo (não entra no rateio variável)", span=8)
    _hdr(ws, 14, ["Segmento", "Σ ASSOCIADO", "Σ TERCEIRO", "", "", "", "", ""])
    ws["A15"] = "PESADOS"; ws["A15"].font = SUB_FONT; ws["A15"].border = BOX
    ws["B15"] = f'=SUMIFS({EV}!H2:H{n},{EV}!A2:A{n},"PESADOS",{EV}!B2:B{n},"ASSOCIADO")'
    ws["C15"] = f'=SUMIFS({EV}!H2:H{n},{EV}!A2:A{n},"PESADOS",{EV}!B2:B{n},"TERCEIRO")'
    ws["B15"].number_format = CURRENCY; ws["C15"].number_format = CURRENCY
    ws["B15"].border = BOX; ws["C15"].border = BOX

    for col, w in {"A": 12, "B": 22, "C": 22, "D": 22, "E": 16, "F": 26,
                    "G": 22, "H": 24}.items():
        ws.column_dimensions[col].width = w

    # ------------------ ANALITICO_SAIDA
    ws = wb.create_sheet("ANALITICO_SAIDA")
    ws["A1"] = f"ANALÍTICO — abril/2026 (PoC Remonta — motor AutoTruck Mut)"
    ws["A1"].font = Font(bold=True, size=14); ws.merge_cells("A1:H1")
    ws["A2"] = f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Invariante motor (Δ alvo vs alocado): R$ {resultado.consolidado.diferenca_total:.2f}"
    ws.merge_cells("A2:H2")

    seg_res = {s.segmento: s for s in resultado.segmentos}
    _hdr(ws, 4, ["", "LEVES", "MOTOS", "", "PESADOS (pote)", "", "", ""])
    rows = [
        ("Cotas ativas adimplentes (denominador)",
            int(seg_res["LEVES"].cotas_ativas), int(seg_res["MOTOS"].cotas_ativas), "—"),
        ("Σ Integral associados",
            seg_res["LEVES"].custo_integrais, seg_res["MOTOS"].custo_integrais,
            seg_res["PESADOS"].custo_integrais),
        ("Σ Parcial associados",
            seg_res["LEVES"].custo_parciais, seg_res["MOTOS"].custo_parciais,
            seg_res["PESADOS"].custo_parciais),
        ("(−) Dedução salvados",
            seg_res["LEVES"].deducao_salvados, seg_res["MOTOS"].deducao_salvados,
            seg_res["PESADOS"].deducao_salvados),
        ("(−) Dedução franquias / participação",
            seg_res["LEVES"].deducao_franquias, seg_res["MOTOS"].deducao_franquias,
            seg_res["PESADOS"].deducao_franquias),
        ("Custo a Ratear (numerador)",
            seg_res["LEVES"].custo_a_ratear, seg_res["MOTOS"].custo_a_ratear,
            seg_res["PESADOS"].custo_a_ratear),
        ("Cota mensal — variável",
            seg_res["LEVES"].valor_cota, seg_res["MOTOS"].valor_cota, "—"),
        ("Recuperação Terceiros (vai p/ pote Terceiros)",
            seg_res["LEVES"].recuperacao_terceiros,
            seg_res["MOTOS"].recuperacao_terceiros,
            seg_res["PESADOS"].recuperacao_terceiros),
        ("Faixa de estabilização (R$30–R$35)",
            seg_res["LEVES"].faixa_estabilizacao,
            seg_res["MOTOS"].faixa_estabilizacao, "—"),
    ]
    for i, (label, l, m, p) in enumerate(rows, start=5):
        ws.cell(i, 1, label).font = SUB_FONT; ws.cell(i, 1).border = BOX
        for col, val in zip((2, 3, 5), (l, m, p)):
            cell = ws.cell(i, col, val); cell.border = BOX
            if isinstance(val, (int, float)) and i != 5:
                cell.number_format = CURRENCY
    ws.merge_cells("E4:F4")
    for col, w in {"A": 44, "B": 18, "C": 18, "D": 4, "E": 22, "F": 8,
                    "G": 4, "H": 4}.items():
        ws.column_dimensions[col].width = w

    saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)


# ------------------------------------------------------------------
# Saída — trilha textual
# ------------------------------------------------------------------

def _gerar_trilha(saida: Path, base, eventos, cotas, resultado, params):
    saida.parent.mkdir(parents=True, exist_ok=True)
    L = []
    P = L.append
    P("=" * 70)
    P("PoC REMONTA — Motor AutoTruck rodando sobre BASE + RATEIO do Rodrigo")
    P(f"Gerado em: {datetime.now().isoformat(timespec='seconds')}")
    P("=" * 70)
    P("")
    P("FONTES")
    P("  - Remonta/BASE_Reconstruida.xlsx  → denominador (cotas baixadas)")
    P("  - Remonta/Rateio_POC_Completo.xlsx → numerador (eventos abr/26)")
    P("")
    P("DENOMINADOR (cotas ativas e adimplentes)")
    for seg in ("LEVES", "MOTOS", "PESADOS"):
        b = base[seg]
        src = "BASE" if b.get("cotas_baixadas") else (
            f"fallback estimado = {COTAS_LEVES_FALLBACK}" if seg == "LEVES" else "ausente")
        P(f"  {seg:8s} cotas={cotas[seg]:>7d}   inadimplentes={b.get('cotas_abertas') or 0:>5}   fonte: {src}")
    P("")
    P("EVENTOS DO MÊS (numerador) — Rateio_POC_Completo.xlsx")
    blocos = {}
    for e in eventos:
        k = (e["segmento"], e["envolvimento"], e["tipo_evento"])
        blocos.setdefault(k, []).append(e)
    for (seg, env, tipo), evs in sorted(blocos.items()):
        soma_vr = sum(e["valor_rateado"] for e in evs)
        soma_part = sum(e["participacao"] for e in evs)
        P(f"  {seg:8s} {env:9s} {tipo:8s}  n={len(evs):3d}  "
          f"Σ VR=R$ {soma_vr:>12,.2f}  Σ Participação=R$ {soma_part:>10,.2f}")
    P("")
    P("FÓRMULA APLICADA (rateio variável LEVES/MOTOS)")
    P("  Custo a Ratear = Σ INTEGRAL ASSOC + Σ PARCIAL ASSOC − Σ salvados − Σ franquias")
    P("  Cota Mensal    = Custo a Ratear  ÷  Cotas ativas adimplentes")
    P("  Terceiros: NÃO abatem a cota (vão para o pote 'Danos a Terceiros').")
    P("  PESADOS: pote fixo (casco caminhão) — não entra no rateio variável.")
    P("")
    P("RESULTADO POR SEGMENTO")
    for s in resultado.segmentos:
        if s.modo == "RATEIO_VARIAVEL":
            P(f"  {s.segmento:8s}  custo=R$ {s.custo_a_ratear:>12,.2f}  "
              f"cotas={s.cotas_ativas:>9,.0f}  cota=R$ {s.valor_cota:>7,.2f}  "
              f"faixa={s.faixa_estabilizacao}")
        else:
            P(f"  {s.segmento:8s}  POTE FIXO casco caminhão  custo=R$ {s.custo_a_ratear:>10,.2f}  "
              f"arrecadado=R$ {s.arrecadado:.2f}  reserva=R$ {s.reserva_ou_deficit:.2f}")
    c = resultado.consolidado
    P("")
    P("INVARIANTE DE AUDITORIA")
    P(f"  Δ (custo apurado − custo alocado) = R$ {c.diferenca_total:.2f}")
    P(f"  invariante_ok = {c.invariante_ok}")
    P(f"  eventos alocados/postergados = {c.eventos_alocados}/{c.eventos_postergados}")
    P("")
    P("PARÂMETROS DO MOTOR")
    P(f"  faixa estabilização R$ {params.cota_alvo_min:.2f}–R$ {params.cota_alvo_max:.2f}")
    P(f"  regra dos 75% (perda total) limiar={params.threshold_perda_total:.0%}")
    P(f"  arrec. terceiros estimada=R$ {params.arrecadacao_terceiros_estimada:.2f}")
    P("")
    P("OBSERVAÇÕES (engenharia reversa)")
    P("  - INTEGRAL: valor_fipe = Valor Rateado + Participação; franquia = Participação.")
    P("  - PARCIAL : valor_evento = VR + Part; valor_fipe inflado p/ não disparar regra 75%.")
    P("  - 1 veículo sintético = 1 cota (FIPE 10k) — denominador escalável diretamente.")
    P("")
    saida.write_text("\n".join(L), encoding="utf-8")


# ------------------------------------------------------------------
# Saída — Simulador completo (Camada 2)
# ------------------------------------------------------------------

# Posições das colunas na aba EVENTOS do SIMULADOR_AutoTruck_COMPLETO.xlsx
# (ver `gerar_planilha_completa.py`). Os formulários da APURACAO/PAINEL
# já apontam para essas posições, então preservamos o esquema.
EVENTOS_NCOLS = 15
VEICULOS_NCOLS = 13


def _gerar_simulador_remonta(template: Path, saida: Path,
                              eventos: list[dict], cotas: dict) -> None:
    """Abre o SIMULADOR_AutoTruck_COMPLETO.xlsx como template e troca:

        EVENTOS    → 92 eventos do Rateio POC abr/26 (com fórmulas N/O)
        VEICULOS   → frota mínima representativa (296 PESADOS + 1 LEVE
                     simbólico + 1 MOTO simbólico). LEVES/MOTOS usam o
                     override P_COTAS_LEVES/P_COTAS_MOTOS da PARAMETROS.
        PARAMETROS → P_COTAS_LEVES e P_COTAS_MOTOS atualizados.
        PAINEL     → título e contagens atualizadas.

    Mantém as demais abas (ANALITICO, APURACAO, CONFERENCIA, FECHAMENTO,
    BASE, INADIMPLENCIA, FORNECEDOR 2, RATEIO, INSTRUCOES) intactas; suas
    fórmulas referenciam EVENTOS/VEICULOS/PARAMETROS via named ranges e
    recalculam quando o Excel abre.
    """
    wb = openpyxl.load_workbook(template)

    # ---------------- EVENTOS
    ws = wb["EVENTOS"]
    _clear_rows(ws, start=2, n_cols=EVENTOS_NCOLS)
    for i, e in enumerate(eventos, start=2):
        vr = e["valor_rateado"]; part = e["participacao"]
        bruto = vr + part
        valor_fipe = bruto if e["tipo_evento"] == "INTEGRAL" else bruto / 0.5
        ws.cell(i, 1, f"EV-{i - 1:05d}")
        ws.cell(i, 2, str(e["protocolo"]))
        ws.cell(i, 3, str(e["placa"]))
        ws.cell(i, 4, e["segmento"])
        ws.cell(i, 5, e["envolvimento"])
        ws.cell(i, 6, e["tipo_evento"])
        ws.cell(i, 7, bruto)        # valor_evento
        ws.cell(i, 8, bruto)        # orcamento_reparo
        ws.cell(i, 9, valor_fipe)   # valor_fipe
        ws.cell(i, 10, e["data_aviso"])
        ws.cell(i, 11, part)        # franquia
        ws.cell(i, 12, 0)           # valor_salvado
        ws.cell(i, 13, 0)           # salvado_liq
        ws.cell(i, 14, f'=IF(AND(F{i}<>"INTEGRAL",I{i}>0,H{i}>P_THR*I{i}),"INTEGRAL",F{i})')
        ws.cell(i, 15, f'=IF(N{i}="INTEGRAL",I{i},G{i})')

    # ---------------- VEICULOS
    ws = wb["VEICULOS"]
    _clear_rows(ws, start=2, n_cols=VEICULOS_NCOLS)
    r = 2
    for i in range(1, cotas["PESADOS"] + 1):
        _escrever_veiculo(ws, r, f"P{i:05d}", f"PES{i:05d}",
                           "PESADOS", "CAMINHAO", fipe=10_000)
        r += 1
    # Tokens simbólicos LEVES/MOTOS — o denominador vem de P_COTAS_*.
    _escrever_veiculo(ws, r, "L00001", "LEV00001",
                       "LEVES", "AUTOMOVEL", fipe=10_000); r += 1
    _escrever_veiculo(ws, r, "M00001", "MOT00001",
                       "MOTOS", "MOTOCICLETA", fipe=10_000)

    # ---------------- PARAMETROS
    ws = wb["PARAMETROS"]
    ws.cell(15, 3, cotas["LEVES"])   # P_COTAS_LEVES
    ws.cell(16, 3, cotas["MOTOS"])   # P_COTAS_MOTOS

    # ---------------- PAINEL
    ws = wb["PAINEL"]
    ws.cell(1, 1, "AutoTruck — Simulador de Rateio — PoC Remonta (abril/2026)")
    ws.cell(15, 2, cotas["PESADOS"] + 2)         # 296 + 2 (tokens LEVE/MOTO)
    ws.cell(16, 2, len(eventos))
    ws.cell(19, 1,
            "Eventos reais do Rateio_POC_Completo.xlsx (abr/26). Edite a "
            "PARAMETROS (células amarelas P_COTAS_LEVES, P_COTAS_MOTOS, "
            "P_T50, P_T100, P_CAM…) e todo o painel recalcula.")

    saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)


def _clear_rows(ws, start: int, n_cols: int) -> None:
    for r in range(start, ws.max_row + 1):
        for c in range(1, n_cols + 1):
            ws.cell(r, c).value = None


def _escrever_veiculo(ws, row: int, vid: str, placa: str, seg: str,
                       tipo: str, fipe: float) -> None:
    ws.cell(row, 1, vid); ws.cell(row, 2, placa); ws.cell(row, 3, seg)
    ws.cell(row, 4, tipo); ws.cell(row, 5, float(fipe))
    ws.cell(row, 6, 1)              # status_ativo
    ws.cell(row, 7, 1)              # adimplente
    ws.cell(row, 8, 0)              # servicos
    ws.cell(row, 9, "NENHUM")       # cobertura
    ws.cell(row, 10, f"=IF(E{row}>P_FIPE_ESP,P_MULT,"
                       f"P_BASE+P_PASSO*(CEILING(E{row}/P_FAIXA,1)-1))")
    ws.cell(row, 11, f"=IF(AND(F{row}=1,G{row}=1),1,0)")
    ws.cell(row, 12, f"=J{row}*K{row}")
    ws.cell(row, 13, f'=IF(K{row}=1,IF(I{row}="100K",P_T100,'
                       f'IF(I{row}="50K",P_T50,0)),0)')


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent.parent  # backend/tools → projetos/Mut
    base_path = Path(argv[1]) if len(argv) > 1 else root / "Remonta" / "BASE_Reconstruida.xlsx"
    rateio_path = Path(argv[2]) if len(argv) > 2 else root / "Remonta" / "Rateio_POC_Completo.xlsx"
    xlsx_out = Path(argv[3]) if len(argv) > 3 else root / "simulacoes" / "POC_REMONTA_abr26.xlsx"
    txt_out = Path(argv[4]) if len(argv) > 4 else root / "docs" / "evidencias" / "POC_REMONTA_abr26.txt"
    template = root / "simulacoes" / "SIMULADOR_AutoTruck_COMPLETO.xlsx"
    sim_out = root / "simulacoes" / "SIMULADOR_REMONTA_abr26.xlsx"

    print(f"[1/5] Lendo BASE     : {base_path}")
    base = _ler_base(base_path)
    print(f"[2/5] Lendo RATEIO   : {rateio_path}")
    eventos = _ler_rateio(rateio_path)
    print(f"      {len(eventos)} eventos lidos.")

    print("[3/5] Rodando motor AutoTruck…")
    veiculos, eventos_at, cotas = _montar_input(base, eventos)
    resultado = calcular_rateio_at(
        mes_ano_ref="2026-04", veiculos=veiculos, eventos=eventos_at,
        params=PARAMS_DEFAULT,
    )
    for s in resultado.segmentos:
        if s.modo == "RATEIO_VARIAVEL":
            print(f"      {s.segmento:8s}: custo=R$ {s.custo_a_ratear:,.2f}  "
                  f"cotas={s.cotas_ativas:,.0f}  cota=R$ {s.valor_cota:,.2f}  "
                  f"[{s.faixa_estabilizacao}]")
    print(f"      Δ invariante: R$ {resultado.consolidado.diferenca_total:.2f}  "
          f"(ok={resultado.consolidado.invariante_ok})")

    print(f"[4/5] Gerando evidência (Camada 1)")
    _gerar_xlsx(xlsx_out, base, eventos, cotas, resultado, PARAMS_DEFAULT)
    _gerar_trilha(txt_out, base, eventos, cotas, resultado, PARAMS_DEFAULT)
    print(f"      → {xlsx_out}")
    print(f"      → {txt_out}")

    print(f"[5/5] Gerando simulador completo (Camada 2)")
    if template.exists():
        _gerar_simulador_remonta(template, sim_out, eventos, cotas)
        print(f"      → {sim_out}")
    else:
        print(f"      AVISO: template não encontrado em {template} — pulando")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
