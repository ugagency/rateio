"""Motor de Rateio — núcleo puro.

Porta a lógica de `rodar_motor_rateio.py` para um módulo testável e injetável.
Sem I/O, sem dependência de framework. Recebe coleções, devolve `ResultadoRateio`.
"""

from collections import defaultdict
from typing import Iterable

from .domain import (
    Boleto,
    Consolidado,
    Evento,
    EventoRateado,
    PotinhoResultado,
    ResultadoRateio,
    ServicoFixo,
    Veiculo,
)
from .rules import DEGRAUS_DEFAULT, Degrau, tabela_cota_por_categoria


def calcular_rateio(
    *,
    mes_ano_ref: str,
    veiculos: Iterable[Veiculo],
    eventos: Iterable[Evento],
    servicos: Iterable[ServicoFixo],
    degraus: tuple[Degrau, ...] = DEGRAUS_DEFAULT,
) -> ResultadoRateio:
    """Roda o motor sobre as coleções de entrada e devolve o resultado completo.

    Regras invariantes (não alterar):
      - Funcionários e veículos inativos não entram na matemática nem geram boleto.
      - Plano ANUAL entra como peso, mas não gera boleto mensal.
      - Eventos são alocados por (data ASC, valor DESC, id) com rateio parcial.
      - Saldo restante volta como Valor_Saldo_Pendente do evento original.
    """
    veiculos_list = list(veiculos)
    eventos_list = list(eventos)
    servicos_idx = {s.id_veiculo: s for s in servicos}
    tabela_cota = tabela_cota_por_categoria(degraus)

    # 1) Elegíveis para a matemática (status ativo + não-funcionário)
    elegiveis = [v for v in veiculos_list if v.status_ativo and not v.is_funcionario]

    # 2) Cotas por categoria
    cotas_por_tipo: dict[str, float] = defaultdict(float)
    for v in elegiveis:
        cotas_por_tipo[v.tipo_categoria_risco] += v.qtd_cotas

    # 3) Calcula os 4 potinhos cumulativos
    potinhos: list[PotinhoResultado] = []
    alvo_total = 0.0
    for d in degraus:
        base = sum(cotas_por_tipo.get(c, 0.0) for c in d.categorias_que_pagam)
        valor = round(base * d.valor_por_cota, 2)
        alvo_total += valor
        potinhos.append(
            PotinhoResultado(
                potinho=d.nome,
                degrau=d.valor_por_cota,
                base_cotas=round(base, 2),
                valor=valor,
            )
        )
    alvo_total = round(alvo_total, 2)

    # 4) Aloca eventos: data ASC → valor DESC → id, com rateio parcial
    eventos_ordenados = sorted(
        eventos_list,
        key=lambda e: (e.data_ocorrencia, -e.valor_saldo_pendente, e.id_evento),
    )
    restante = alvo_total
    eventos_rateados: list[EventoRateado] = []
    for e in eventos_ordenados:
        if restante <= 0.005:
            break
        if e.valor_saldo_pendente <= 0:
            continue
        usar = round(min(e.valor_saldo_pendente, restante), 2)
        parcial = usar < e.valor_saldo_pendente - 0.005
        eventos_rateados.append(
            EventoRateado(
                mes_ano_ref=mes_ano_ref,
                id_evento=e.id_evento,
                data_ocorrencia=e.data_ocorrencia,
                valor_total_evento=e.valor_total,
                valor_saldo_antes=e.valor_saldo_pendente,
                valor_rateado_neste_mes=usar,
                valor_saldo_apos=round(e.valor_saldo_pendente - usar, 2),
                status_evento="SALDO_RESTANTE" if parcial else "LIQUIDADO",
            )
        )
        restante = round(restante - usar, 2)

    # 5) Gera boletos (todos os veículos, mas Gera_Boleto=False para isentos)
    boletos: list[Boleto] = []
    for v in veiculos_list:
        rateio_v = (
            v.qtd_cotas * tabela_cota[v.tipo_categoria_risco]
            if (not v.is_funcionario)
            else 0.0
        )
        sv = servicos_idx.get(v.id_veiculo)
        fixos = (
            (sv.taxa_administrativa + sv.valor_assistencia_24h + sv.valor_outros_produtos)
            if sv
            else 0.0
        )
        total = rateio_v + fixos
        gera = (not v.is_funcionario) and v.tipo_pagamento != "ANUAL" and v.status_ativo
        boletos.append(
            Boleto(
                id_veiculo=v.id_veiculo,
                mes_ano_ref=mes_ano_ref,
                tipo_categoria_risco=v.tipo_categoria_risco,
                qtd_cotas=v.qtd_cotas,
                custo_rateio_calculado=round(rateio_v, 2),
                custo_produtos_fixos=round(fixos, 2),
                valor_total_boleto=round(total, 2),
                tipo_pagamento=v.tipo_pagamento,
                is_funcionario=v.is_funcionario,
                gera_boleto=gera,
            )
        )

    # 6) Consolidado
    soma_alocada = round(sum(er.valor_rateado_neste_mes for er in eventos_rateados), 2)
    consolidado = Consolidado(
        mes_ano_ref=mes_ano_ref,
        total_cotas_apuradas=round(sum(cotas_por_tipo.values()), 1),
        total_veiculos_elegiveis=len(elegiveis),
        valor_alvo_total=alvo_total,
        valor_p1_roubo_furto=potinhos[0].valor,
        valor_p2_moto_fip=potinhos[1].valor,
        valor_p3_venture_1=potinhos[2].valor,
        valor_p4_venture_2=potinhos[3].valor,
        eventos_alocados=len(eventos_rateados),
        eventos_liquidados=sum(1 for x in eventos_rateados if x.status_evento == "LIQUIDADO"),
        eventos_parciais=sum(1 for x in eventos_rateados if x.status_evento == "SALDO_RESTANTE"),
        saldo_para_proximo_mes=round(sum(er.valor_saldo_apos for er in eventos_rateados), 2),
        diferenca_alvo_vs_alocado=round(alvo_total - soma_alocada, 2),
    )

    return ResultadoRateio(
        mes_ano_ref=mes_ano_ref,
        consolidado=consolidado,
        potinhos=potinhos,
        eventos_rateados=eventos_rateados,
        boletos=boletos,
    )
