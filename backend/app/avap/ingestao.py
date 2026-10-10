"""Leitores dos exports do SGA (Hinova) da AVAP: veículos e eventos.

Fase 0 do PRD_AVAP: parser de cota + conferência com o rodapé. Os leitores
aceitam caminho de arquivo ou file-like e falham (ConferenciaRodapeError) se a
contagem/soma lida divergir do rodapé, a menos que `estrito=False`.
"""

import re
from datetime import date, datetime

import openpyxl

from .domain import (
    Conferencia,
    Divergencia,
    EstadoRateio,
    EventoAVAP,
    LeituraEventos,
    LeituraVeiculos,
    VeiculoAVAP,
)

TOL = 0.01

# Peso = número entre parênteses no FIM do rótulo (PRD 4.1.1); nunca recalcula pela FIPE.
_RX_PESO = re.compile(r"\(\s*(\d+(?:[.,]\d+)?)\s*\)\s*$")
_RX_SUFIXO = re.compile(r"-\s*(VP|DP|CP|TP)\s*\(\s*\d+(?:[.,]\d+)?\s*\)\s*$")


class ConferenciaRodapeError(ValueError):
    def __init__(self, conferencia: Conferencia):
        self.conferencia = conferencia
        det = "; ".join(f"{d.campo}: lido {d.lido:,.2f} x rodapé {d.rodape:,.2f}" for d in conferencia.divergencias)
        super().__init__(f"Leitura não confere com o rodapé do SGA ({det})")


class LayoutDesconhecidoError(ValueError):
    pass


def parse_cota(rotulo) -> tuple[float, str | None]:
    """Devolve (peso, sufixo) de um rótulo de cota do SGA."""
    if not isinstance(rotulo, str):
        raise ValueError(f"Rótulo de cota inválido: {rotulo!r}")
    m = _RX_PESO.search(rotulo)
    if not m:
        raise ValueError(f"Rótulo de cota sem peso no fim: {rotulo!r}")
    peso = float(m.group(1).replace(",", "."))
    s = _RX_SUFIXO.search(rotulo)
    return peso, (s.group(1) if s else None)


def _num(v, padrao: float = 0.0) -> float:
    """Número do SGA: float, int, '25200.00' ou '361,530.00' (milhar com vírgula)."""
    if v is None or v == "":
        return padrao
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v).strip().replace(",", ""))


def _data(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return None


def _texto(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _linhas(origem) -> list[tuple]:
    wb = openpyxl.load_workbook(origem, data_only=True, read_only=True)
    try:
        return list(wb.active.iter_rows(values_only=True))
    finally:
        wb.close()


def _cabecalho(linhas: list[tuple], primeira_coluna: str) -> int:
    for i, r in enumerate(linhas[:10]):
        if r and r[0] == primeira_coluna:
            return i
    raise LayoutDesconhecidoError(f"Cabeçalho iniciado em '{primeira_coluna}' não encontrado")


def _colunas(cab: tuple) -> dict[str, int]:
    """Nome -> índice da PRIMEIRA ocorrência (o layout de 30/09 repete um bloco vazio)."""
    idx: dict[str, int] = {}
    for i, nome in enumerate(cab):
        if nome and str(nome).strip() not in idx:
            idx[str(nome).strip()] = i
    return idx


def _exigir(idx: dict[str, int], nomes: list[str]) -> None:
    faltam = [n for n in nomes if n not in idx]
    if faltam:
        raise LayoutDesconhecidoError(f"Colunas ausentes: {', '.join(faltam)}")


def _comparar(campo: str, lido: float, rodape: float | None, conf: Conferencia) -> None:
    if rodape is not None and abs(lido - rodape) > TOL:
        conf.divergencias.append(Divergencia(campo, lido, rodape))


# ───────────────────────── veículos ─────────────────────────

_COLS_VEICULO = [
    "Placa", "Cota", "Categoria", "Tipo Veículo", "Valor FIPE Veiculo",
    "Situação Veículo", "Situação Associado", "Matrícula Associado",
]


def ler_veiculos(origem, estrito: bool = True) -> LeituraVeiculos:
    linhas = _linhas(origem)
    h = _cabecalho(linhas, "Placa")
    idx = _colunas(linhas[h])
    _exigir(idx, _COLS_VEICULO)

    veiculos: list[VeiculoAVAP] = []
    fim = len(linhas)
    for i in range(h + 1, len(linhas)):
        r = linhas[i]
        if not any(c is not None for c in r) or r[0] == "Resumo":
            fim = i
            break
        peso, suf = parse_cota(r[idx["Cota"]])
        fipe = _num(r[idx["Valor FIPE Veiculo"]], 0.0)
        mat = r[idx["Matrícula Associado"]]
        veiculos.append(VeiculoAVAP(
            placa=_texto(r[idx["Placa"]]),
            rotulo_cota=str(r[idx["Cota"]]).strip(),
            peso_cota=peso,
            sufixo_cota=suf,
            categoria=_texto(r[idx["Categoria"]]) or "",
            tipo_veiculo=_texto(r[idx["Tipo Veículo"]]) or "",
            valor_fipe=fipe if fipe > 0 else None,
            situacao_veiculo=_texto(r[idx["Situação Veículo"]]) or "",
            situacao_associado=_texto(r[idx["Situação Associado"]]) or "",
            matricula=int(mat) if isinstance(mat, (int, float)) else None,
        ))

    rodape: dict[str, float] = {}
    for r in linhas[fim:]:
        rot = str(r[0]) if r and r[0] else ""
        if rot.startswith("Total de veículos"):
            rodape["veiculos"] = _num(r[1])
        elif rot.startswith("Total de cotas"):
            rodape["cotas"] = _num(r[1])

    conf = Conferencia()
    _comparar("veiculos", float(len(veiculos)), rodape.get("veiculos"), conf)
    _comparar("cotas", sum(v.peso_cota for v in veiculos), rodape.get("cotas"), conf)
    if not rodape:
        raise LayoutDesconhecidoError("Rodapé 'Resumo' não encontrado")
    if estrito and not conf.aprovada:
        raise ConferenciaRodapeError(conf)
    return LeituraVeiculos(veiculos, rodape, conf)


# ───────────────────────── eventos ─────────────────────────

_COLS_EVENTO = [
    "Protocolo", "Situacao", "Data Finalizacao", "Valor Reparo", "Valor Participacao",
    "Valor CustoEvento", "Previsao Valor Reparo", "Motivo", "Valor Rateado",
    "Data Cadastro Evento", "Cota", "Categoria", "Modelo", "Tipo Evento",
]

_ROTULOS_RODAPE = {
    "Valor Total Reparo": "reparo",
    "Valor Total Participacao": "participacao",
    "Valor Total Custo Evento": "custo",
    "Valor a Ratear": "a_ratear",
    "Valor Rateado": "rateado",
}


def estado_rateio(valor, custo: float) -> tuple[EstadoRateio, float | None]:
    """Classifica o campo Valor Rateado (PRD 4.2.1)."""
    if valor is None or str(valor).strip() == "":
        return EstadoRateio.NAO_RATEADO, None
    v = _num(valor)
    if abs(v) <= TOL:
        return EstadoRateio.NA_FILA, 0.0
    if abs(v - custo) <= TOL:
        return EstadoRateio.RATEADO, v
    return EstadoRateio.RATEADO_DIVERGENTE, v


def ler_eventos(origem, estrito: bool = True) -> LeituraEventos:
    linhas = _linhas(origem)
    h = _cabecalho(linhas, "Protocolo")
    idx = _colunas(linhas[h])
    _exigir(idx, _COLS_EVENTO)
    layout = "28/09" if "Placa" in idx else "30/09" if "Tipo Veiculo" in idx else None
    if layout is None:
        raise LayoutDesconhecidoError("Layout sem 'Placa' nem 'Tipo Veiculo'")

    eventos: list[EventoAVAP] = []
    fim = len(linhas)
    for i in range(h + 1, len(linhas)):
        r = linhas[i]
        if not isinstance(r[0], int):
            fim = i
            break
        custo = _num(r[idx["Valor CustoEvento"]])
        est, vr = estado_rateio(r[idx["Valor Rateado"]], custo)
        rot = _texto(r[idx["Cota"]])
        peso, suf = parse_cota(rot) if rot else (None, None)
        eventos.append(EventoAVAP(
            protocolo=r[0],
            situacao=_texto(r[idx["Situacao"]]) or "",
            data_finalizacao=_data(r[idx["Data Finalizacao"]]),
            valor_reparo=_num(r[idx["Valor Reparo"]]),
            valor_participacao=_num(r[idx["Valor Participacao"]]),
            custo_evento=custo,
            previsao_reparo=_num(r[idx["Previsao Valor Reparo"]]),
            motivo=_texto(r[idx["Motivo"]]) or "",
            estado_rateio=est,
            valor_rateado=vr,
            data_cadastro=_data(r[idx["Data Cadastro Evento"]]),
            rotulo_cota=rot,
            peso_cota=peso,
            sufixo_cota=suf,
            categoria=_texto(r[idx["Categoria"]]),
            modelo=_texto(r[idx["Modelo"]]),
            tipo_veiculo=_texto(r[idx["Tipo Veiculo"]]) if "Tipo Veiculo" in idx else None,
            tipo_evento=_texto(r[idx["Tipo Evento"]]),
            placa=_texto(r[idx["Placa"]]) if "Placa" in idx else None,
        ))

    rodape: dict[str, float] = {}
    for r in linhas[fim:]:
        rot = str(r[0]).strip() if r and r[0] else ""
        m = re.match(r"Total de eventos encontrados:\s*(\d+)", rot)
        if m:
            rodape["eventos"] = float(m.group(1))
        elif rot in _ROTULOS_RODAPE and isinstance(r[1], (int, float)):
            # "Valor a Ratear" e "Valor Rateado" aparecem 2x: eventos, depois relacionados
            chave = _ROTULOS_RODAPE[rot]
            if chave in rodape:
                chave += "_relacionados"
            rodape[chave] = float(r[1])
        elif rot == "Valor Reparo Evento Relacionados":
            rodape["relacionados_reparo"] = _num(r[1])
    if "eventos" not in rodape:
        raise LayoutDesconhecidoError("Rodapé 'Resumo' não encontrado")

    conf = Conferencia()
    _comparar("eventos", float(len(eventos)), rodape.get("eventos"), conf)
    _comparar("reparo", sum(e.valor_reparo for e in eventos), rodape.get("reparo"), conf)
    _comparar("participacao", sum(e.valor_participacao for e in eventos), rodape.get("participacao"), conf)
    _comparar("custo", sum(e.custo_evento for e in eventos), rodape.get("custo"), conf)

    cont: dict[int, int] = {}
    for e in eventos:
        cont[e.protocolo] = cont.get(e.protocolo, 0) + 1
    dups = sorted(p for p, n in cont.items() if n > 1)

    if estrito and not conf.aprovada:
        raise ConferenciaRodapeError(conf)
    return LeituraEventos(eventos, rodape, conf, layout, dups)
