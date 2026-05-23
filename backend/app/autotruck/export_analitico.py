"""Export da aba ANALITICO preenchida com os números do motor AutoTruck.

Estratégia *template*: parte de `templates/analitico_template.xlsx` (a própria
aba ANALITICO do FECHAMENTO, só ela, preservando tema/cores/formatação
condicional/merges/formatos R$) e:

  • injeta VALOR LITERAL nas células folha cuja fórmula original era cross-sheet
    (`RATEIO!`) e o motor calcula — cotas, indenizações integral/parcial,
    terceiros, por segmento;
  • mantém as fórmulas *intra*-ANALITICO (SUM, COTA FINAL = D8/D9, …) — elas
    recalculam sozinhas no Excel a partir das folhas preenchidas;
  • deixa EM BRANCO as células de faturamento/financeiro (`FECHAMENTO!`,
    `INADIMPLENCIA!`) que o motor de rateio não calcula — VALOR RECEBIDO,
    RESUMO, FORNECEDOR —, anexando em cada uma uma NOTA `Origem: …` para o
    usuário reconhecer de onde viria o número.

Nada de reconstruir célula a célula (erraria cor/posição); só `cell.value`,
preservando o estilo herdado do template.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from io import BytesIO
from pathlib import Path

import openpyxl
from openpyxl.comments import Comment

from .domain import ResultadoRateioAT, SegmentoResultado

_TEMPLATE = Path(__file__).resolve().parent / "templates" / "analitico_template.xlsx"
_AUTOR = "Motor de Rateio"

# Células de faturamento/financeiro: o motor de rateio NÃO as calcula.
# Ficam em branco + nota com a origem (aba do arquivo do Rodrigo).
#   coord -> (origem_ref, descricao)
_FATURAMENTO: dict[str, tuple[str, str]] = {
    # --- VALOR RECEBIDO (recuperação financeira de terceiros) ---
    "D22": ("FECHAMENTO!$D$16", "VALOR RECEBIDO — recuperação financeira de terceiros (LEVES)"),
    "G22": ("FECHAMENTO!$K$12", "VALOR RECEBIDO — recuperação financeira de terceiros (MOTOS)"),
    "D30": ("FECHAMENTO!$S$9", "VALOR RECEBIDO — recuperação financeira de terceiros (PESADOS associados)"),
    "G30": ("FECHAMENTO!$S$14", "VALOR RECEBIDO — recuperação financeira de terceiros (PESADOS terceiros)"),
    # --- líquidos (dependem do VALOR RECEBIDO acima) ---
    "D20": ("=D22-D26", "Líquido terceiros LEVES = VALOR RECEBIDO − total rateado (depende do faturamento)"),
    "G20": ("=G22-G26", "Líquido terceiros MOTOS = VALOR RECEBIDO − total rateado (depende do faturamento)"),
    "D28": ("=D30-D34", "Líquido PESADOS associados (depende do VALOR RECEBIDO)"),
    "G28": ("=G30-G34", "Líquido PESADOS terceiros (depende do VALOR RECEBIDO)"),
    # --- boxes de validação OK/! (cross-sheet p/ FECHAMENTO) ---
    "B20": ("FECHAMENTO!$D$16", "Validação OK/! — compara rateio terceiros LEVES com o recebido (faturamento)"),
    "H20": ("FECHAMENTO!$K$12", "Validação OK/! — compara rateio terceiros MOTOS com o recebido (faturamento)"),
    "B28": ("FECHAMENTO!$S$9", "Validação OK/! — PESADOS associados (faturamento)"),
    "H28": ("FECHAMENTO!$S$14", "Validação OK/! — PESADOS terceiros (faturamento)"),
    # --- RESUMO (boletos / valor / cotas EM ABERTO) — faturamento ---
    "D39": ("FECHAMENTO!C23", "RESUMO·BOLETOS em aberto (LEVE) — faturamento"),
    "E39": ("FECHAMENTO!J23", "RESUMO·BOLETOS em aberto (MOTO) — faturamento"),
    "F39": ("FECHAMENTO!R23", "RESUMO·BOLETOS em aberto (PESADO) — faturamento"),
    "G39": ("=SUM(D39:F39)", "RESUMO·BOLETOS total — soma de faturamento"),
    "D40": ("FECHAMENTO!F23", "RESUMO·VALOR em aberto (LEVE) — faturamento"),
    "E40": ("FECHAMENTO!M23", "RESUMO·VALOR em aberto (MOTO) — faturamento"),
    "F40": ("FECHAMENTO!U23", "RESUMO·VALOR em aberto (PESADO) — faturamento"),
    "G40": ("=SUM(D40:F40)", "RESUMO·VALOR total — soma de faturamento"),
    "D41": ("FECHAMENTO!D23", "RESUMO·COTAS em aberto (LEVE) — faturamento"),
    "E41": ("FECHAMENTO!S23", "RESUMO·COTAS em aberto (MOTO) — faturamento"),
    "F41": ("FECHAMENTO!K23", "RESUMO·COTAS em aberto (PESADO) — faturamento"),
    "G41": ("=SUM(D41:F41)", "RESUMO·COTAS total — soma de faturamento"),
}
# --- FORNECEDOR (produtos/serviços: assist 24h, carro reserva, vidros, combos)
# Vem de INADIMPLENCIA!$I$38:$M$43 (VLOOKUP). Linhas 43..47, colunas D..G.
_FORNECEDOR_LABEL = {
    43: "ASSISTÊNCIA 24 HORAS", 44: "CARRO RESERVA", 45: "VIDROS",
    46: "COMBOS", 47: "ASSISTÊNCIA CARRO",
}
for _r, _lab in _FORNECEDOR_LABEL.items():
    for _c in ("D", "E", "F", "G"):
        _FATURAMENTO[f"{_c}{_r}"] = (
            "INADIMPLENCIA!$I$38:$M$43",
            f"FORNECEDOR·{_lab} — produto/serviço (não calculado pelo motor)",
        )


def _seg(res: ResultadoRateioAT, nome: str) -> SegmentoResultado | None:
    return next((s for s in res.segmentos if s.segmento == nome), None)


def _agg_terceiros(res: ResultadoRateioAT) -> dict[tuple[str, str, str], float]:
    """Soma custo_a_ratear por (segmento, envolvimento, tipo) — só ALOCADO."""
    agg: dict[tuple[str, str, str], float] = defaultdict(float)
    for e in res.eventos_rateados:
        if e.status != "ALOCADO":
            continue
        agg[(e.segmento, e.envolvimento, e.tipo_evento)] += e.custo_a_ratear
    return agg


def _mes_para_data(mes_ano_ref: str) -> date | None:
    """'MM/AAAA' -> date(AAAA, MM, 1) para o título B1 (formato mmm-yy)."""
    try:
        mm, aaaa = mes_ano_ref.split("/")
        return date(int(aaaa), int(mm), 1)
    except (ValueError, AttributeError):
        return None


def gerar_analitico_xlsx(res: ResultadoRateioAT) -> bytes:
    """Devolve os bytes do .xlsx ANALITICO preenchido com o mês de `res`."""
    if not _TEMPLATE.exists():
        raise FileNotFoundError(f"Template ANALITICO ausente: {_TEMPLATE}")
    wb = openpyxl.load_workbook(_TEMPLATE)
    ws = wb["ANALITICO"]

    leves = _seg(res, "LEVES")
    motos = _seg(res, "MOTOS")
    pesados = _seg(res, "PESADOS")
    agg = _agg_terceiros(res)
    c = res.consolidado

    def w(coord: str, value) -> None:
        ws[coord] = value  # só o valor; estilo/formatação herdados do template

    # ---- Título (B1): mês de referência ----
    d = _mes_para_data(res.mes_ano_ref)
    if d is not None:
        w("B1", d)

    # ---- COTAS LEVES (col D) / MOTOS (col G) ----
    for seg, total_cotas, colD in (
        (leves, c.total_cotas_leves, "D"),
        (motos, c.total_cotas_motos, "G"),
    ):
        if seg is None:
            continue
        w(f"{colD}5", round(total_cotas, 2))                          # TOTAL ATIVO
        w(f"{colD}6", round(total_cotas - seg.cotas_ativas, 2))       # INADIMPLENCIA
        # D8/D9/D10/D16 são fórmulas intra-aba — recalculam de D17/D18 e D5/D6.
        w(f"{colD}17", round(seg.custo_integrais, 2))                 # INDENIZAÇÃO INTEGRAL (assoc)
        w(f"{colD}18", round(seg.custo_parciais, 2))                  # INDENIZAÇÃO PARCIAL (assoc)
        # Terceiros (rows 24/25): split integral/parcial vindo da agregação
        seg_nome = seg.segmento
        w(f"{colD}24", round(agg.get((seg_nome, "TERCEIRO", "INTEGRAL"), 0.0), 2))
        w(f"{colD}25", round(agg.get((seg_nome, "TERCEIRO", "PARCIAL"), 0.0), 2))
        # D26/G26 = SUM(D24:D25) — fórmula intra-aba mantida.

    # ---- PESADOS (rows 32/33): D=ASSOCIADOS, G=TERCEIROS ----
    if pesados is not None:
        w("D32", round(agg.get(("PESADOS", "ASSOCIADO", "INTEGRAL"), 0.0), 2))
        w("D33", round(agg.get(("PESADOS", "ASSOCIADO", "PARCIAL"), 0.0), 2))
        w("G32", round(agg.get(("PESADOS", "TERCEIRO", "INTEGRAL"), 0.0), 2))
        w("G33", round(agg.get(("PESADOS", "TERCEIRO", "PARCIAL"), 0.0), 2))
        # D34/G34 = SUM — fórmula intra-aba mantida.

    # ---- Faturamento/financeiro: branco + nota de origem ----
    for coord, (origem, desc) in _FATURAMENTO.items():
        cell = ws[coord]
        cell.value = None
        cell.comment = Comment(
            f"Origem: {origem}\n{desc}\n— não calculado pelo motor de rateio.",
            _AUTOR,
        )

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
