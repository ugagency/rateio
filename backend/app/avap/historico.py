"""Leitor da planilha de rateio real da AVAP (histórico/aceite, PRD 4.4).

Cada aba é um fechamento: linhas de evento (com placa) e linhas de soma/dedução (sem placa, valor
com sinal). Serve só para conciliação; não alimenta o cálculo.
"""

from dataclasses import dataclass, field

import openpyxl

from .domain import Lancamento, TipoLancamento
from .ingestao import TOL, LayoutDesconhecidoError, _data
from .rules import REGRAS_PADRAO, RegrasAVAP

_COLS = ["Tipo Veiculo", "Placa", "Protocolo", "Descrição", "Data", "Valor Reparo",
         "Valor Participação", "Valor Rateado"]


@dataclass(frozen=True)
class EventoRateado:
    protocolo: int
    placa: str
    motivo: str
    data: object
    valor_reparo: float
    valor_participacao: float
    valor_rateado: float


@dataclass
class FechamentoHistorico:
    aba: str
    eventos: list[EventoRateado]
    lancamentos: list[Lancamento]
    nao_classificadas: list[str] = field(default_factory=list)

    @property
    def total_eventos(self) -> float:
        return round(sum(e.valor_rateado for e in self.eventos), 2)

    @property
    def total_lancamentos(self) -> float:
        return round(sum(x.valor if x.tipo == TipoLancamento.SOMA else -x.valor for x in self.lancamentos), 2)

    @property
    def total(self) -> float:
        return round(self.total_eventos + self.total_lancamentos, 2)

    @property
    def protocolos(self) -> set[int]:
        return {e.protocolo for e in self.eventos}


def classificar_linha(descricao: str | None, valor: float, regras: RegrasAVAP = REGRAS_PADRAO) -> Lancamento:
    """Linha sem placa -> Lancamento. O sinal define o tipo; a descrição define o código."""
    tipo = TipoLancamento.DEDUCAO if valor < 0 else TipoLancamento.SOMA
    desc = (descricao or "").strip()
    tabela = regras.codigos_deducao if tipo == TipoLancamento.DEDUCAO else regras.codigos_soma
    codigo = next((c for trecho, c in tabela if trecho in desc.upper()), "NAO_CLASSIFICADO")
    return Lancamento(tipo, codigo, desc or "(sem descrição)", round(abs(valor), 2))


def ler_historico(origem, regras: RegrasAVAP = REGRAS_PADRAO) -> dict[str, FechamentoHistorico]:
    """Lê todas as abas do arquivo. Devolve {nome da aba: fechamento}."""
    wb = openpyxl.load_workbook(origem, data_only=True, read_only=True)
    saida: dict[str, FechamentoHistorico] = {}
    try:
        for ws in wb.worksheets:
            linhas = list(ws.iter_rows(values_only=True))
            if not linhas or tuple(linhas[0][: len(_COLS)]) != tuple(_COLS):
                raise LayoutDesconhecidoError(f"Aba '{ws.title}' sem o cabeçalho esperado {_COLS}")
            fech = FechamentoHistorico(ws.title, [], [])
            for r in linhas[1:]:
                if not any(c is not None for c in r):
                    continue
                rateado = float(r[7] or 0)
                rep, part = float(r[5] or 0), float(r[6] or 0)
                if r[1]:  # evento (com placa)
                    if abs(rep - part - rateado) > TOL:
                        raise LayoutDesconhecidoError(
                            f"Aba '{ws.title}', protocolo {r[2]}: rateado != reparo - participação")
                    fech.eventos.append(EventoRateado(int(r[2]), str(r[1]).strip(), str(r[3] or "").strip(),
                                                      _data(r[4]), rep, part, rateado))
                else:
                    lanc = classificar_linha(r[3], rateado, regras)
                    fech.lancamentos.append(lanc)
                    if lanc.codigo == "NAO_CLASSIFICADO":
                        fech.nao_classificadas.append(lanc.descricao)
            saida[ws.title] = fech
    finally:
        wb.close()
    return saida
