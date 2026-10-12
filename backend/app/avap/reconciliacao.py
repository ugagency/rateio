"""Reconciliação de aceite da AVAP (PRD 11): confronta o fechamento real (planilha de rateio)
com o que o motor calcula a partir das exportações do SGA.

Status: OK (|Δ| <= R$ 0,01), FALHA, INFO (informativo, não reprova) e PENDENTE (falta insumo).
"""

from dataclasses import dataclass, field

from .domain import Decisao, DecisaoEvento, EventoAVAP, VeiculoAVAP
from .engine import calcular_rateio
from .historico import FechamentoHistorico
from .rules import RegrasAVAP
from .selecao import selecionar

TOL = 0.01
CRITERIOS = ("TODOS", "VEICULO", "ASSOCIADO", "AMBOS")


@dataclass(frozen=True)
class Linha:
    grupo: str
    item: str
    declarado: float | None
    calculado: float | None
    status: str
    obs: str = ""

    @property
    def delta(self) -> float | None:
        if self.declarado is None or self.calculado is None:
            return None
        return round(self.calculado - self.declarado, 2)


@dataclass
class Reconciliacao:
    aba: str
    linhas: list[Linha] = field(default_factory=list)

    @property
    def aprovado(self) -> bool:
        return not any(ln.status == "FALHA" for ln in self.linhas)

    def add(self, grupo: str, item: str, declarado: float | None, calculado: float | None,
            obs: str = "", informativo: bool = False) -> None:
        if declarado is None or calculado is None:
            st = "PENDENTE"
        elif informativo:
            st = "INFO"
        else:
            st = "OK" if abs(calculado - declarado) <= TOL else "FALHA"
        self.linhas.append(Linha(grupo, item, declarado, calculado, st, obs))


def reconciliar(
    hist: FechamentoHistorico,
    eventos_sga: list[EventoAVAP],
    veiculos: list[VeiculoAVAP],
    fila_pre_fechamento: list[EventoAVAP] | None = None,
    valor_cota_declarado: float | None = None,
    regras: RegrasAVAP | None = None,
) -> Reconciliacao:
    regras = regras or RegrasAVAP()
    rec = Reconciliacao(hist.aba)
    sga = {e.protocolo: e for e in eventos_sga}

    # 1. Eventos do histórico presentes na exportação do SGA, com o mesmo valor
    ausentes = sorted(hist.protocolos - sga.keys())
    divergentes = sorted(e.protocolo for e in hist.eventos
                         if e.protocolo in sga and abs(sga[e.protocolo].custo_evento - e.valor_rateado) > TOL)
    rec.add("Eventos", "protocolos do rateio ausentes no SGA", 0, float(len(ausentes)),
            obs=", ".join(map(str, ausentes)))
    rec.add("Eventos", "valores divergentes do SGA", 0, float(len(divergentes)),
            obs=", ".join(map(str, divergentes)))

    usados = [sga[e.protocolo] for e in hist.eventos if e.protocolo in sga]

    # 2. Seleção: fila pré-fechamento + decisões derivadas do histórico
    if fila_pre_fechamento is not None:
        decisoes = [DecisaoEvento(p, Decisao.INCLUIR, "consta no rateio real") for p in sorted(hist.protocolos)]
        na_fila = {e.protocolo for e in fila_pre_fechamento if e.estado_rateio in regras.estados_candidatos}
        decisoes += [DecisaoEvento(p, Decisao.EXCLUIR, "na fila e fora do rateio real") for p in sorted(na_fila - hist.protocolos)]
        sel = selecionar(fila_pre_fechamento, regras, decisoes)
        rec.add("Seleção", "eventos selecionados", float(len(hist.eventos)), float(len(sel.selecionados)),
                obs=f"{len(na_fila & hist.protocolos)} da fila, {len(hist.protocolos - na_fila)} manuais, "
                    f"{len(na_fila - hist.protocolos)} da fila excluídos")
        rec.add("Seleção", "custo dos eventos selecionados", hist.total_eventos, sel.total_custo)
        rec.add("Seleção", "pendências de homologação", 0, float(len(sel.pendencias) + len(sel.bloqueios)))
    else:
        rec.add("Seleção", "eventos selecionados (sem foto da fila pré-fechamento)", None, None)

    # 3. Totais do histórico contra o motor
    rec.add("Totais", "custo dos eventos", hist.total_eventos, round(sum(e.custo_evento for e in usados), 2),
            obs="só eventos achados no SGA" if ausentes else "")
    rec.add("Totais", "quantidade de eventos", float(len(hist.eventos)), float(len(usados)))
    for n in hist.nao_classificadas:
        rec.add("Linhas", f"linha sem classificação: {n}", 0, 1.0, informativo=True)

    # 4. Numerador e valor da cota, por critério de elegibilidade (D2)
    if usados and len(usados) == len(hist.eventos):
        for crit in CRITERIOS:
            r = calcular_rateio(usados, hist.lancamentos, veiculos, _com_criterio(regras, crit))
            rec.add("Numerador", f"numerador ({crit})", hist.total, r.numerador)
            if valor_cota_declarado is None:
                rec.add("Valor da cota", f"valor por cota ({crit}), {r.total_cotas:,.0f} cotas",
                        None, round(r.valor_cota, 4),
                        obs="critério vigente (D2)" if crit == regras.criterio_elegibilidade else "só comparação")
            else:
                rec.add("Valor da cota", f"valor por cota ({crit}), {r.total_cotas:,.0f} cotas",
                        valor_cota_declarado, round(r.valor_cota, 2))
    else:
        rec.add("Numerador", "numerador (eventos ausentes no SGA, não calculado)", None, None)
    return rec


def _com_criterio(regras: RegrasAVAP, criterio: str) -> RegrasAVAP:
    from dataclasses import replace

    return replace(regras, criterio_elegibilidade=criterio)
