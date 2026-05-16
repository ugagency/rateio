"""Ingestão do FECHAMENTO real da AutoTruck (layout do SGA/planilha deles).

Lê o workbook *no formato deles* (abas ANALITICO e RATEIO) e reconcilia,
centavo a centavo, contra os números declarados na própria planilha:
  (a) identidades internas do ANALITICO (integral + parcial = rateio);
  (b) reconciliação evento-a-evento: o engine, alimentado com os eventos
      da aba RATEIO, reproduz os agregados do ANALITICO.

Não depende de JSON nosso — consome o artefato do cliente.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

import openpyxl

from .domain import EventoAT

# Colunas da aba RATEIO (1-indexed) conforme cabeçalho real
_C = dict(protocolo=2, campo=3, motivo=4, envolv=5, situacao=6, fornecedor=7,
          placa=8, participacao=9, custo_evento=10, data_com=11, tipo_evento=12,
          mes_ref=13, valor_rateado=14)

_SEG = {"LEVES": "LEVES", "MOTOS": "MOTOS", "PESADOS": "PESADOS"}


def _num(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _data(v) -> str:
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    return str(v)[:10] if v else ""


@dataclass
class AnaliticoFonte:
    rateio_leves: float = 0.0
    integral_leves: float = 0.0
    parcial_leves: float = 0.0
    terceiros_leves_total: float = 0.0
    terceiros_leves_integral: float = 0.0
    terceiros_leves_parcial: float = 0.0
    rateio_motos: float = 0.0
    integral_motos: float = 0.0
    parcial_motos: float = 0.0
    terceiros_motos_total: float = 0.0
    terceiros_motos_integral: float = 0.0
    terceiros_motos_parcial: float = 0.0
    pesados_terceiros_total: float = 0.0


@dataclass
class FechamentoFonte:
    arquivo: str
    analitico: AnaliticoFonte
    eventos: list[EventoAT] = field(default_factory=list)
    secoes_com_dados: list[str] = field(default_factory=list)


def ler_analitico(ws) -> AnaliticoFonte:
    """Lê o ANALITICO por rótulo (robusto a deslocamento de linhas).
    Coluna C/D = LEVES; F/G = MOTOS. Blocos: 'X ASSOCIADOS' → INTEGRAL/PARCIAL;
    'X TERCEIROS' → INTEGRAL/PARCIAL/TOTAL.
    """
    a = AnaliticoFonte()
    ctx_leves = ctx_motos = None  # "ASSOC" | "TERC"
    for r in range(1, ws.max_row + 1):
        cL = (ws.cell(r, 3).value or "")
        cM = (ws.cell(r, 6).value or "")
        sL = str(cL).strip().upper()
        sM = str(cM).strip().upper()
        dL, dM = _num(ws.cell(r, 4).value), _num(ws.cell(r, 7).value)
        if sL == "RATEIO LEVES":
            a.rateio_leves = dL
        if sM == "RATEIO MOTOS":
            a.rateio_motos = dM
        if sL == "LEVES ASSOCIADOS":
            ctx_leves = "ASSOC"
        elif sL == "LEVES TERCEIROS":
            ctx_leves = "TERC"
        elif sL.startswith("PESADOS"):          # bloco PESADOS: encerra LEVES
            ctx_leves = "PESADOS"
        if sM == "MOTOS ASSOCIADOS":
            ctx_motos = "ASSOC"
        elif sM == "MOTOS TERCEIROS":
            ctx_motos = "TERC"
        elif sM.startswith("PESADOS"):          # bloco PESADOS: encerra MOTOS
            ctx_motos = "PESADOS"
        if sL == "INDENIZAÇÃO INTEGRAL":
            if ctx_leves == "ASSOC":
                a.integral_leves = dL
            elif ctx_leves == "TERC":
                a.terceiros_leves_integral = dL
        if sL == "INDENIZAÇÃO PARCIAL":
            if ctx_leves == "ASSOC":
                a.parcial_leves = dL
            elif ctx_leves == "TERC":
                a.terceiros_leves_parcial = dL
        if sL == "TOTAL" and ctx_leves == "TERC":
            a.terceiros_leves_total = dL
        if sM == "INDENIZAÇÃO INTEGRAL":
            if ctx_motos == "ASSOC":
                a.integral_motos = dM
            elif ctx_motos == "TERC":
                a.terceiros_motos_integral = dM
        if sM == "INDENIZAÇÃO PARCIAL":
            if ctx_motos == "ASSOC":
                a.parcial_motos = dM
            elif ctx_motos == "TERC":
                a.terceiros_motos_parcial = dM
        if sM == "TOTAL" and ctx_motos == "TERC":
            a.terceiros_motos_total = dM
        if sM == "PESADOS TERCEIROS":
            a.pesados_terceiros_total = abs(dM)
    a.terceiros_leves_total = a.terceiros_leves_total or abs(
        a.terceiros_leves_integral + a.terceiros_leves_parcial)
    a.terceiros_motos_total = a.terceiros_motos_total or abs(
        a.terceiros_motos_integral + a.terceiros_motos_parcial)
    return a


def ler_eventos_rateio(ws) -> tuple[list[EventoAT], list[str]]:
    """Percorre a aba RATEIO. Marcadores na coluna B definem o contexto
    (segmento, envolvimento, tipo). Linhas-evento têm Custo Evento (J) > 0
    e identificação (Motivo/Fornecedor/Data) — linhas de subtotal são puladas.
    """
    eventos: list[EventoAT] = []
    secoes: set[str] = set()
    seg = env = tipo = None
    eid = 0
    for r in range(1, ws.max_row + 1):
        marca = ws.cell(r, 2).value
        s = str(marca).strip().upper() if marca else ""
        if s.endswith("ASSOCIADOS") or s.endswith("TERCEIROS"):
            for k in _SEG:
                if k in s:
                    seg = k
            env = "ASSOCIADO" if "ASSOCIADOS" in s else "TERCEIRO"
            tipo = None
            continue
        if "INDENIZAÇÃO INTEGRAL" in s:
            tipo = "INTEGRAL"
            continue
        if "INDENIZAÇÃO PARCIAL" in s:
            tipo = "PARCIAL"
            continue
        if s == "PROTOCOLO":
            continue
        if seg is None or env is None or tipo is None:
            continue
        custo = _num(ws.cell(r, _C["custo_evento"]).value)
        motivo = ws.cell(r, _C["motivo"]).value
        fornecedor = ws.cell(r, _C["fornecedor"]).value
        datacom = ws.cell(r, _C["data_com"]).value
        # linha-evento: tem custo > 0 e ao menos uma identificação real
        if custo <= 0 or not (motivo or fornecedor or datacom):
            continue
        eid += 1
        if tipo == "INTEGRAL":
            valor_fipe, valor_evento, orc = custo, custo, 0.0
        else:  # PARCIAL: FIPE alto p/ não disparar regra dos 75%
            valor_fipe, valor_evento, orc = round(custo / 0.5, 2), custo, 0.0
        eventos.append(EventoAT(
            id_evento=f"FZ-{eid:05d}",
            protocolo=str(ws.cell(r, _C["protocolo"]).value or f"PRT{eid:05d}"),
            placa=str(ws.cell(r, _C["placa"]).value or ""),
            segmento=seg, envolvimento=env, tipo_evento=tipo,
            valor_evento=valor_evento, orcamento_reparo=orc, valor_fipe=valor_fipe,
            data_aviso=_data(datacom), franquia=0.0, valor_salvado=0.0,
            salvado_liquidado=False, postergado=False,
        ))
        secoes.add(f"{seg}/{env}/{tipo}")
    return eventos, sorted(secoes)


def ler_fechamento(path: str) -> FechamentoFonte:
    wb = openpyxl.load_workbook(path, data_only=True)
    analitico = ler_analitico(wb["ANALITICO"])
    eventos, secoes = ler_eventos_rateio(wb["RATEIO"])
    return FechamentoFonte(arquivo=path, analitico=analitico,
                           eventos=eventos, secoes_com_dados=secoes)


TOL = 0.01  # critério de aceite: |Δ| ≤ R$ 0,01


@dataclass
class LinhaRecon:
    grupo: str
    item: str
    declarado: float       # número da planilha deles (ANALITICO)
    calculado: float       # identidade interna ou engine
    delta: float
    status: str            # OK | SEM DETALHE NESTA CÓPIA | FALHA


@dataclass
class Reconciliacao:
    arquivo: str
    linhas: list[LinhaRecon]
    secoes_com_dados: list[str]
    n_eventos: int
    aprovado: bool


def reconciliar(path: str) -> Reconciliacao:
    """Roda o ENGINE real sobre os eventos da planilha deles e confronta,
    centavo a centavo, com o ANALITICO declarado por eles."""
    from .engine import calcular_rateio_at  # import tardio (evita ciclo)

    f = ler_fechamento(path)
    a = f.analitico
    r = calcular_rateio_at(mes_ano_ref="FECHAMENTO", veiculos=[], eventos=f.eventos)
    seg = {s.segmento: s for s in r.segmentos}
    eng_int = {"LEVES": seg["LEVES"].custo_integrais, "MOTOS": seg["MOTOS"].custo_integrais}
    eng_par = {"LEVES": seg["LEVES"].custo_parciais, "MOTOS": seg["MOTOS"].custo_parciais}
    eng_bru = {"LEVES": r.consolidado.bruto_leves, "MOTOS": r.consolidado.bruto_motos}
    eng_ter = {"LEVES": r.consolidado.recuperacao_terceiros_leves,
               "MOTOS": r.consolidado.recuperacao_terceiros_motos}
    pes_ter = sum(e.custo_a_ratear for e in r.eventos_rateados
                  if e.segmento == "PESADOS" and e.envolvimento == "TERCEIRO")

    L: list[LinhaRecon] = []

    def add(grupo, item, dec, calc, modo="evento"):
        d = round(calc - dec, 2)
        if abs(d) <= TOL:
            st = "OK"
        elif modo == "evento" and abs(calc) < TOL and abs(dec) > TOL:
            st = "SEM DETALHE NESTA CÓPIA"
        else:
            st = "FALHA"
        L.append(LinhaRecon(grupo, item, round(dec, 2), round(calc, 2), d, st))

    # Grupo 1 — identidades internas do ANALITICO (devem fechar no arquivo deles)
    add("Identidade ANALITICO", "LEVES: integral+parcial = RATEIO LEVES",
        a.rateio_leves, a.integral_leves + a.parcial_leves, "ident")
    add("Identidade ANALITICO", "MOTOS: integral+parcial = RATEIO MOTOS",
        a.rateio_motos, a.integral_motos + a.parcial_motos, "ident")
    add("Identidade ANALITICO", "LEVES terceiros: integral+parcial = TOTAL",
        a.terceiros_leves_total, a.terceiros_leves_integral + a.terceiros_leves_parcial, "ident")
    add("Identidade ANALITICO", "MOTOS terceiros: integral+parcial = TOTAL",
        a.terceiros_motos_total, a.terceiros_motos_integral + a.terceiros_motos_parcial, "ident")

    # Grupo 2 — engine (sobre os eventos da aba RATEIO) × ANALITICO declarado
    add("Engine × ANALITICO", "LEVES integral", a.integral_leves, eng_int["LEVES"])
    add("Engine × ANALITICO", "LEVES parcial", a.parcial_leves, eng_par["LEVES"])
    add("Engine × ANALITICO", "LEVES RATEIO (bruto)", a.rateio_leves, eng_bru["LEVES"])
    add("Engine × ANALITICO", "MOTOS integral", a.integral_motos, eng_int["MOTOS"])
    add("Engine × ANALITICO", "MOTOS parcial", a.parcial_motos, eng_par["MOTOS"])
    add("Engine × ANALITICO", "MOTOS RATEIO (bruto)", a.rateio_motos, eng_bru["MOTOS"])
    add("Engine × ANALITICO", "LEVES terceiros (rastreado)", a.terceiros_leves_total, eng_ter["LEVES"])
    add("Engine × ANALITICO", "MOTOS terceiros (rastreado)", a.terceiros_motos_total, eng_ter["MOTOS"])
    add("Engine × ANALITICO", "PESADOS terceiros", a.pesados_terceiros_total, pes_ter)

    aprovado = all(x.status != "FALHA" for x in L)
    return Reconciliacao(arquivo=path, linhas=L, secoes_com_dados=f.secoes_com_dados,
                         n_eventos=len(f.eventos), aprovado=aprovado)
