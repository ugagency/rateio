"""Motor puro do rateio AVAP: numerador, denominador, valor da cota, boletos e invariantes (PRD 6 a 10)."""

from collections import Counter
from collections.abc import Iterable

from .domain import BoletoAVAP, EventoAVAP, Lancamento, ResultadoAVAP, TipoLancamento, VeiculoAVAP
from .rules import REGRAS_PADRAO, RegrasAVAP


def _motivo_fora(v: VeiculoAVAP, regras: RegrasAVAP) -> str | None:
    """Motivo de ficar fora do denominador, ou None se elegível (D2 e D4)."""
    if v.peso_cota <= 0:
        return "PESO_ZERO"
    if v.situacao_associado.upper() in regras.situacoes_pendentes:
        return "ASSOCIADO_PENDENTE"
    if not v.placa and not v.valor_fipe:
        return "SEM_PLACA_SEM_FIPE"
    crit = regras.criterio_elegibilidade
    if crit in ("VEICULO", "AMBOS") and v.situacao_veiculo.upper() != "ATIVO":
        return "VEICULO_INADIMPLENTE"
    if crit in ("ASSOCIADO", "AMBOS") and v.situacao_associado.upper() != "ATIVO":
        return "ASSOCIADO_INADIMPLENTE"
    return None


def calcular_rateio(
    eventos: Iterable[EventoAVAP],
    lancamentos: Iterable[Lancamento],
    veiculos: Iterable[VeiculoAVAP],
    regras: RegrasAVAP = REGRAS_PADRAO,
) -> ResultadoAVAP:
    eventos = list(eventos)
    lancamentos = list(lancamentos)
    custo = round(sum(e.custo_evento for e in eventos), 2)
    somas = round(sum(x.valor for x in lancamentos if x.tipo == TipoLancamento.SOMA), 2)
    deducoes = round(sum(x.valor for x in lancamentos if x.tipo == TipoLancamento.DEDUCAO), 2)
    numerador = round(custo + somas - deducoes, 2)

    elegiveis: list[VeiculoAVAP] = []
    fora: Counter[str] = Counter()
    for v in veiculos:
        m = _motivo_fora(v, regras)
        if m:
            fora[m] += 1
        else:
            elegiveis.append(v)
    total_cotas = sum(v.peso_cota for v in elegiveis)
    if total_cotas <= 0:
        raise ValueError("Denominador zerado: nenhum veículo elegível")
    valor_cota = numerador / total_cotas

    boletos = [
        BoletoAVAP(
            placa=v.placa,
            matricula=v.matricula,
            peso_cota=v.peso_cota,
            contribuicao_rateio=round(v.peso_cota * valor_cota, 2),
            contribuicao_estabilizacao=round(v.peso_cota * regras.contribuicao_estabilizacao_por_cota, 2),
            taxa_administracao=round(v.peso_cota * regras.taxa_administracao_por_cota, 2),
            produtos_beneficios=round(v.peso_cota * regras.produtos_beneficios_por_cota, 2),
        )
        for v in elegiveis
    ]
    diferenca = round(sum(b.contribuicao_rateio for b in boletos) - numerador, 2)
    protocolos = [e.protocolo for e in eventos]
    invariantes = {
        "arredondamento": abs(diferenca) < 0.01 * len(boletos),
        "numerador_positivo": numerador > 0,
        "protocolos_unicos": len(protocolos) == len(set(protocolos)),
    }
    return ResultadoAVAP(
        custo_eventos=custo, somas=somas, deducoes=deducoes, numerador=numerador,
        total_cotas=total_cotas, valor_cota=valor_cota, veiculos_elegiveis=len(elegiveis),
        veiculos_fora=dict(fora), boletos=boletos, diferenca_arredondamento=diferenca,
        invariantes=invariantes, eventos_por_motivo=dict(Counter(e.motivo for e in eventos)),
    )
