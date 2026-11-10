"""Assistente de ajuste da cota no pote único, adaptado do assistente da AutoTruck.

O gestor informa a cota que quer atingir; o assistente sugere quais eventos postergar para a próxima
competência para chegar lá. A conta é a do pote único:

    valor da cota = (eventos + somas - deduções) / cotas
    redução necessária = (cota atual - alvo) x cotas

Regra de escolha (mesma ideia da AutoTruck, "estabilização > FIFO"): o menor número de eventos possível.
A cada passo, se algum evento sozinho já cobre o que falta, entra o menor deles (para não passar muito
do alvo); senão, entra o de maior custo. Empate de custo: o mais recente primeiro. Diferença em relação
à AutoTruck: lá entra sempre o maior; aqui o último passo escolhe o menor que cobre, o que dá o mesmo
número de eventos e uma cota final mais perto do alvo.

Nada aqui altera a sessão: a função só sugere. Aplicar é uma decisão EXCLUIR com justificativa, que vai
para a trilha de auditoria como qualquer outra decisão do operador.
"""

from dataclasses import dataclass, field
from datetime import date

from app.avap.domain import EventoAVAP

TOLERANCIA = 0.005  # meio centavo, a mesma folga da AutoTruck


@dataclass(frozen=True)
class EventoSugerido:
    protocolo: int
    motivo: str
    placa: str | None
    data_finalizacao: date | None
    custo_evento: float


@dataclass(frozen=True)
class SugestaoAjuste:
    cota_atual: float
    alvo_cota: float
    precisa_ajuste: bool
    reducao_necessaria: float
    reducao_obtida: float
    cota_resultante: float
    atingiu_alvo: bool
    mensagem: str
    eventos_sugeridos: list[EventoSugerido] = field(default_factory=list)


def brl(v: float) -> str:
    """R$ no formato brasileiro, para as mensagens: 1.234,56."""
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cota(numerador: float, total_cotas: float) -> float:
    if total_cotas <= 0:
        raise ValueError("Sem cotas no denominador.")
    return numerador / total_cotas


def _recencia(e: EventoAVAP) -> int:
    return e.data_finalizacao.toordinal() if e.data_finalizacao else 0


def sugerir_ajuste(
    eventos: list[EventoAVAP], numerador: float, total_cotas: float, alvo_cota: float
) -> SugestaoAjuste:
    """Sugere o menor conjunto de eventos a postergar para a cota ficar no alvo ou abaixo dele."""
    if alvo_cota <= 0:
        raise ValueError("O alvo da cota precisa ser maior que zero.")
    atual = round(cota(numerador, total_cotas), 4)
    alvo = round(alvo_cota, 2)
    if atual <= alvo + TOLERANCIA:
        return SugestaoAjuste(
            cota_atual=atual, alvo_cota=alvo, precisa_ajuste=False, reducao_necessaria=0.0,
            reducao_obtida=0.0, cota_resultante=atual, atingiu_alvo=True,
            mensagem=f"A cota de R$ {brl(atual)} já está dentro do alvo de R$ {brl(alvo)}.")

    reducao = round((atual - alvo) * total_cotas, 2)
    # ordem base: custo desc, empate pelo mais recente
    restantes = sorted((e for e in eventos if e.custo_evento > 0),
                       key=lambda e: (-e.custo_evento, -_recencia(e)))
    escolhidos: list[EventoAVAP] = []
    acumulado = 0.0
    while restantes and acumulado < reducao - TOLERANCIA:
        falta = reducao - acumulado
        cobrem = [e for e in restantes if e.custo_evento >= falta - TOLERANCIA]
        e = min(cobrem, key=lambda x: (x.custo_evento, -_recencia(x))) if cobrem else restantes[0]
        escolhidos.append(e)
        restantes.remove(e)
        acumulado = round(acumulado + e.custo_evento, 2)

    resultante = round(cota(numerador - acumulado, total_cotas), 4)
    atingiu = resultante <= alvo + TOLERANCIA
    if not escolhidos:
        msg = f"A cota de R$ {brl(atual)} está acima do alvo, mas não há eventos com custo para postergar."
    elif atingiu:
        msg = (f"Postergue {len(escolhidos)} evento(s), somando R$ {brl(acumulado)}: a cota vai de "
               f"R$ {brl(atual)} para R$ {brl(resultante)} (alvo R$ {brl(alvo)}).")
    else:
        msg = (f"Mesmo postergando todos os {len(escolhidos)} eventos, a cota fica em R$ {brl(resultante)}, "
               f"acima do alvo de R$ {brl(alvo)}.")
    return SugestaoAjuste(
        cota_atual=atual, alvo_cota=alvo, precisa_ajuste=True, reducao_necessaria=reducao,
        reducao_obtida=acumulado, cota_resultante=resultante, atingiu_alvo=atingiu, mensagem=msg,
        eventos_sugeridos=[EventoSugerido(e.protocolo, e.motivo, e.placa, e.data_finalizacao, e.custo_evento)
                           for e in escolhidos])
