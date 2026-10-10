"""Seleção dos eventos do fechamento (PRD 5): fila do SGA + alertas + decisões do operador.

Achado de 10/10/2026: no fechamento real de 09/2026 a seleção foi a fila do SGA (Valor Rateado
"0.00", 79 de 80 eventos) mais 24 inclusões manuais de eventos com Valor Rateado vazio, menos 1
exclusão. Por isso só NA_FILA é candidato por regra; o vazio exige decisão INCLUIR.
"""

from collections.abc import Iterable, Mapping
from datetime import date

from .domain import (
    Alerta,
    Decisao,
    DecisaoEvento,
    EventoAVAP,
    EventoNaoSelecionado,
    EventoSelecionado,
    ResultadoSelecao,
)
from .ingestao import TOL
from .rules import REGRAS_PADRAO, RegrasAVAP


def _alertas(e: EventoAVAP, base_numerador: float, regras: RegrasAVAP,
             data_anterior: date | None) -> list[Alerta]:
    out: list[Alerta] = []
    s = str(e.protocolo)
    if len(s) < 10 or int(s[:4]) < regras.ano_minimo_protocolo:
        out.append(Alerta("A1", e.protocolo, f"Protocolo atípico ({s})"))
    if e.custo_evento <= 0:
        out.append(Alerta("A2", e.protocolo, f"Custo do evento <= 0 ({e.custo_evento:,.2f})"))
    if e.valor_participacao == 0 and e.custo_evento < regras.custo_minimo_sem_participacao:
        out.append(Alerta("A3", e.protocolo, "Sem participação e custo baixo"))
    if base_numerador > 0 and e.custo_evento > regras.pct_concentracao * base_numerador:
        out.append(Alerta("A4", e.protocolo, f"Evento acima de {regras.pct_concentracao:.0%} do numerador"))
    if e.motivo in regras.motivos_integrais:
        out.append(Alerta("A5", e.protocolo, f"Indenização integral ({e.motivo})"))
    if data_anterior is not None and e.data_finalizacao != data_anterior:
        out.append(Alerta("A6", e.protocolo, f"Data de finalização mudou (era {data_anterior})"))
    if abs(e.custo_evento - (e.valor_reparo - e.valor_participacao)) > TOL:
        out.append(Alerta("A7", e.protocolo, "Custo diferente de reparo menos participação"))
    return out


def selecionar(
    eventos: Iterable[EventoAVAP],
    regras: RegrasAVAP = REGRAS_PADRAO,
    decisoes: Iterable[DecisaoEvento] = (),
    data_fechamento: date | None = None,
    ja_rateados: frozenset[int] = frozenset(),
    datas_anteriores: Mapping[int, date] | None = None,
) -> ResultadoSelecao:
    """Monta a seleção do fechamento. `ja_rateados` vem do histórico de fechamentos anteriores."""
    datas_anteriores = datas_anteriores or {}
    audit: list[str] = []
    bloqueios: list[int] = []

    dec: dict[int, DecisaoEvento] = {}
    for d in decisoes:
        if not d.justificativa.strip():
            raise ValueError(f"Decisão sobre {d.protocolo} sem justificativa")
        if d.protocolo in dec:
            raise ValueError(f"Duas decisões para o protocolo {d.protocolo}")
        dec[d.protocolo] = d

    # Duplicidade (5.3): idêntica deduplica; divergente bloqueia.
    grupos: dict[int, list[EventoAVAP]] = {}
    for e in eventos:
        grupos.setdefault(e.protocolo, []).append(e)
    unicos: list[EventoAVAP] = []
    divergentes: list[EventoAVAP] = []
    for prot, lista in grupos.items():
        if all(x == lista[0] for x in lista):
            unicos.append(lista[0])
            if len(lista) > 1:
                audit.append(f"{prot}: {len(lista)} linhas idênticas deduplicadas")
        else:
            divergentes.append(lista[0])
            bloqueios.append(prot)
            audit.append(f"{prot}: duplicata com valores diferentes, bloqueia a homologação")

    for p in dec:
        if p not in grupos:
            bloqueios.append(p)
            audit.append(f"{p}: decisão para protocolo inexistente na foto")

    def passa_regra(e: EventoAVAP) -> bool:
        return (
            e.situacao == "FINALIZADO"
            and e.tipo_evento == "Evento Associado"
            and e.estado_rateio in regras.estados_candidatos
            and (data_fechamento is None or (e.data_finalizacao is not None and e.data_finalizacao < data_fechamento))
            and e.protocolo not in ja_rateados
        )

    em_jogo = [
        e for e in unicos
        if (dec[e.protocolo].decisao == Decisao.INCLUIR if e.protocolo in dec else passa_regra(e))
    ]
    base = sum(e.custo_evento for e in em_jogo)

    selecionados: list[EventoSelecionado] = []
    nao: list[EventoNaoSelecionado] = []
    alertas: list[Alerta] = []
    pendencias: list[int] = []

    for e in divergentes:
        nao.append(EventoNaoSelecionado(e, "Duplicata com valores diferentes (bloqueada)"))

    for e in unicos:
        d = dec.get(e.protocolo)
        if d and d.decisao == Decisao.EXCLUIR:
            nao.append(EventoNaoSelecionado(e, f"Excluído pelo operador: {d.justificativa}"))
            audit.append(f"{e.protocolo}: EXCLUIR ({d.justificativa})")
            continue
        if d and e.protocolo in ja_rateados:
            bloqueios.append(e.protocolo)
            audit.append(f"{e.protocolo}: INCLUIR de protocolo já rateado em outra competência")
            nao.append(EventoNaoSelecionado(e, "Já rateado em fechamento anterior (bloqueado)"))
            continue
        if not d and not passa_regra(e):
            nao.append(EventoNaoSelecionado(e, _motivo_fora(e, regras, data_fechamento, ja_rateados)))
            continue
        al = _alertas(e, base, regras, datas_anteriores.get(e.protocolo))
        alertas.extend(al)
        cods = tuple(a.codigo for a in al)
        if d:
            selecionados.append(EventoSelecionado(e, "DECISAO", cods))
            audit.append(f"{e.protocolo}: INCLUIR ({d.justificativa})")
        elif al:
            pendencias.append(e.protocolo)
            nao.append(EventoNaoSelecionado(e, f"Pendente de decisão ({', '.join(cods)})"))
        else:
            selecionados.append(EventoSelecionado(e, "REGRA", ()))

    return ResultadoSelecao(selecionados, nao, alertas, pendencias, sorted(set(bloqueios)), audit)


def _motivo_fora(e: EventoAVAP, regras: RegrasAVAP, data_fechamento: date | None,
                 ja_rateados: frozenset[int]) -> str:
    if e.protocolo in ja_rateados:
        return "Já rateado em fechamento anterior"
    if e.tipo_evento != "Evento Associado":
        return "Evento de terceiro"
    if e.situacao != "FINALIZADO":
        return f"Situação {e.situacao}"
    if e.estado_rateio not in regras.estados_candidatos:
        return f"Fora da fila do SGA ({e.estado_rateio.value})"
    return "Finalizado após a data de corte"
