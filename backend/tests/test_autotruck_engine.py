"""Testes do motor AutoTruck (isolado do ELLO).

Hermético: AutoTruckRepo("") cai no dataset calibrado determinístico
(build_dataset, seed fixo) que reproduz os agregados da aba ANALITICO.
"""

import pytest

from app.autotruck.domain import EventoAT, VeiculoAT
from app.autotruck.engine import calcular_rateio_at
from app.autotruck.repo import AutoTruckRepo
from app.autotruck.rules import cotas_por_fipe
from app.autotruck.service import AutoTruckJaExisteError, AutoTruckService

# Alvos da aba ANALITICO do FECHAMENTO.
ALVO_BRUTO_LEVES = 2_616_217.12
ALVO_BRUTO_MOTOS = 500_182.55
ALVO_TERC_LEVES = 756_464.11
ALVO_TERC_MOTOS = 32_982.25


@pytest.fixture
def service() -> AutoTruckService:
    return AutoTruckService(AutoTruckRepo(""))  # fallback determinístico


def test_reproduz_agregados_analitico(service: AutoTruckService) -> None:
    c = service.replay("12/2025").consolidado
    assert c.bruto_leves == pytest.approx(ALVO_BRUTO_LEVES, abs=0.01)
    assert c.bruto_motos == pytest.approx(ALVO_BRUTO_MOTOS, abs=0.01)
    assert c.recuperacao_terceiros_leves == pytest.approx(ALVO_TERC_LEVES, abs=0.01)
    assert c.recuperacao_terceiros_motos == pytest.approx(ALVO_TERC_MOTOS, abs=0.01)


def test_invariante_auditoria_zero(service: AutoTruckService) -> None:
    c = service.replay("12/2025").consolidado
    assert c.diferenca_total == pytest.approx(0.0, abs=0.01)
    assert c.invariante_ok is True
    # custo a ratear = bruto - recuperação de terceiros (por segmento)
    assert c.custo_a_ratear_leves == pytest.approx(ALVO_BRUTO_LEVES - ALVO_TERC_LEVES, abs=0.01)


def test_segmentacao_bases_separadas(service: AutoTruckService) -> None:
    r = service.replay("12/2025")
    modos = {s.segmento: s.modo for s in r.segmentos}
    assert modos["LEVES"] == "RATEIO_VARIAVEL"
    assert modos["MOTOS"] == "RATEIO_VARIAVEL"
    assert modos["PESADOS"] == "POTE_FIXO"  # casco caminhão não entra na divisão de cotas


@pytest.mark.parametrize(
    "fipe,esperado,especial",
    [
        (10_000, 1.0, False),
        (10_001, 1.5, False),
        (20_000, 1.5, False),
        (20_001, 2.0, False),
        (450_000, 23.0, False),
        (450_001, 20.0, True),    # cota especial high-end (multiplicador)
        (900_000, 20.0, True),
    ],
)
def test_cotas_por_fipe(fipe, esperado, especial) -> None:
    qc, esp = cotas_por_fipe(float(fipe))
    assert qc == pytest.approx(esperado)
    assert esp is especial


def test_regra_75_reclassifica_para_integral() -> None:
    veic = [VeiculoAT("V1", "AAA1A11", "LEVES", "AUTOMOVEL", 50_000, True, True)]
    ev = EventoAT(
        id_evento="E1", protocolo="P1", placa="AAA1A11", segmento="LEVES",
        envolvimento="ASSOCIADO", tipo_evento="PARCIAL", valor_evento=10_000,
        orcamento_reparo=40_000,  # > 75% de 50.000 → vira INTEGRAL
        valor_fipe=50_000, data_aviso="2025-03-01",
    )
    r = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=[ev])
    assert r.consolidado.eventos_reclassificados_75pct == 1
    er = r.eventos_rateados[0]
    assert er.tipo_evento == "INTEGRAL" and er.reclassificado_75pct is True
    # INTEGRAL entra pelo FIPE (50k), não pelo valor de oficina (10k)
    assert r.segmentos[0].custo_integrais == pytest.approx(50_000, abs=0.01)


def test_modelo_purista_exclui_inadimplente_e_inativo() -> None:
    veic = [
        VeiculoAT("V1", "P1", "LEVES", "AUTOMOVEL", 50_000, True, True),
        VeiculoAT("V2", "P2", "LEVES", "AUTOMOVEL", 50_000, True, False),   # inadimplente
        VeiculoAT("V3", "P3", "LEVES", "AUTOMOVEL", 50_000, False, True),   # inativo
    ]
    ev = EventoAT("E1", "PR1", "P9", "LEVES", "ASSOCIADO", "PARCIAL",
                  9_000, 1_000, 50_000, "2025-03-01")
    r = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=[ev])
    assert r.consolidado.total_veiculos_elegiveis == 1  # só V1 entra no denominador
    bol = {b.id_veiculo: b for b in r.boletos}
    assert bol["V1"].gera_boleto is True
    assert bol["V2"].gera_boleto is False and bol["V3"].gera_boleto is False


def test_salvado_so_abate_quando_liquidado() -> None:
    base = dict(protocolo="P", placa="X", segmento="LEVES", envolvimento="ASSOCIADO",
                tipo_evento="PARCIAL", valor_evento=10_000, orcamento_reparo=100,
                valor_fipe=80_000, data_aviso="2025-03-01", valor_salvado=3_000)
    veic = [VeiculoAT("V1", "X", "LEVES", "AUTOMOVEL", 50_000, True, True)]
    nao_liq = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic,
                                 eventos=[EventoAT(id_evento="E1", salvado_liquidado=False, **base)])
    liq = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic,
                             eventos=[EventoAT(id_evento="E2", salvado_liquidado=True, **base)])
    assert nao_liq.segmentos[0].deducao_salvados == 0.0
    assert liq.segmentos[0].deducao_salvados == pytest.approx(3_000, abs=0.01)
    assert liq.segmentos[0].custo_a_ratear < nao_liq.segmentos[0].custo_a_ratear


def test_exclusao_manual_exige_justificativa_e_loga() -> None:
    veic = [VeiculoAT("V1", "X", "LEVES", "AUTOMOVEL", 50_000, True, True)]
    evs = [
        EventoAT("E1", "P1", "X", "LEVES", "ASSOCIADO", "PARCIAL", 5_000, 1, 50_000, "2025-03-01"),
        EventoAT("E2", "P2", "X", "LEVES", "ASSOCIADO", "PARCIAL", 7_000, 1, 50_000, "2025-03-02"),
    ]
    base = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs)
    com_excl = calcular_rateio_at(
        mes_ano_ref="03/2025", veiculos=veic, eventos=evs,
        exclusoes={"E2": "Sinistro em análise jurídica — LC 213", "E1": "  "},
    )
    # justificativa vazia ("  ") é ignorada; só E2 sai e é logada
    assert len(com_excl.auditoria) == 1
    assert com_excl.auditoria[0].id_evento == "E2"
    assert com_excl.segmentos[0].custo_a_ratear == pytest.approx(
        base.segmentos[0].custo_a_ratear - 7_000, abs=0.01
    )


def test_idempotencia_service(service: AutoTruckService) -> None:
    service.calcular_e_persistir("12/2025", force=True)
    with pytest.raises(AutoTruckJaExisteError):
        service.calcular_e_persistir("12/2025")
    service.calcular_e_persistir("12/2025", force=True)  # force sobrescreve


def test_boleto_compoe_rateio_mais_potes_mais_servicos(service: AutoTruckService) -> None:
    r = service.replay("12/2025")
    esp = next(b for b in r.boletos if b.cota_especial)
    assert esp.qtd_cotas == 20.0  # multiplicador high-end
    for b in r.boletos:
        assert b.valor_total_boleto == pytest.approx(
            b.custo_rateio + b.custo_pote_terceiros + b.custo_pote_caminhao + b.servicos_adicionais,
            abs=0.01,
        )
