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
    # N3 (transcrição): terceiro NÃO abate a cota — custo a ratear = bruto
    # (salvados/franquias = 0 no dataset). Recuperação fica só no pote.
    assert c.custo_a_ratear_leves == pytest.approx(ALVO_BRUTO_LEVES, abs=0.01)
    assert c.recuperacao_terceiros_leves == pytest.approx(ALVO_TERC_LEVES, abs=0.01)


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


# --- N3: terceiro é produto à parte, NÃO abate a cota variável ---

def test_n3_terceiro_nao_abate_cota_variavel() -> None:
    veic = [VeiculoAT("V1", "X", "LEVES", "AUTOMOVEL", 9_000, True, True)]  # 1 cota
    evs = [
        EventoAT("E1", "P1", "X", "LEVES", "ASSOCIADO", "PARCIAL", 100, 1, 9_000, "2025-03-01"),
        EventoAT("E2", "P2", "Y", "LEVES", "TERCEIRO", "PARCIAL", 50, 1, 9_000, "2025-03-02"),
    ]
    s = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs).segmentos[0]
    assert s.custo_a_ratear == pytest.approx(100, abs=0.01)        # terceiro NÃO abate
    assert s.recuperacao_terceiros == pytest.approx(50, abs=0.01)  # mas segue rastreado
    assert s.valor_cota == pytest.approx(100, abs=0.01)            # 100 / 1 cota


# --- N1: estabilização pela média dos últimos 3 meses (± var_trimestral_max) ---

def _cota30():
    """1 veículo (1 cota) + 1 evento parcial R$30 → cota = R$30,00."""
    veic = [VeiculoAT("V1", "X", "LEVES", "AUTOMOVEL", 9_000, True, True)]
    evs = [EventoAT("E1", "P1", "X", "LEVES", "ASSOCIADO", "PARCIAL", 30, 1, 9_000, "2025-03-01")]
    return veic, evs


def test_n1_sem_historico_nao_alerta() -> None:
    veic, evs = _cota30()
    s = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs).segmentos[0]
    assert s.valor_cota == pytest.approx(30.0)
    assert s.media_cota_3m == 0.0 and s.alerta_variacao_trimestral is False


def test_n1_dentro_de_5pct_nao_alerta() -> None:
    veic, evs = _cota30()
    s = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs,
                           historico_cotas={"LEVES": [29, 30, 31]}).segmentos[0]
    assert s.media_cota_3m == pytest.approx(30.0)
    assert s.variacao_vs_media == pytest.approx(0.0)
    assert s.alerta_variacao_trimestral is False


def test_n1_acima_de_5pct_alerta() -> None:
    veic, evs = _cota30()
    r = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs,
                           historico_cotas={"LEVES": [20, 20, 20]})
    s = r.segmentos[0]
    assert s.media_cota_3m == pytest.approx(20.0)
    assert s.variacao_vs_media == pytest.approx(0.5)  # (30-20)/20
    assert s.alerta_variacao_trimestral is True
    assert "Variação trimestral" in s.sugestao
    assert r.consolidado.alerta_variacao_trimestral is True


def test_n1_usa_apenas_ultimos_3_meses() -> None:
    veic, evs = _cota30()
    # mês antigo (1000) deve ser ignorado; só [30,30,30] conta → sem alerta
    s = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs,
                           historico_cotas={"LEVES": [1000, 30, 30, 30]}).segmentos[0]
    assert s.media_cota_3m == pytest.approx(30.0)
    assert s.alerta_variacao_trimestral is False


def test_n1_service_monta_historico_dos_meses_anteriores() -> None:
    svc = AutoTruckService(AutoTruckRepo(""))
    svc.calcular_e_persistir("10/2025", force=True)
    svc.calcular_e_persistir("11/2025", force=True)
    r = svc.calcular_e_persistir("12/2025", force=True)
    leves = next(s for s in r.segmentos if s.segmento == "LEVES")
    # dataset fixo → cota constante; média 3M ≈ cota atual, variação ~0, sem alerta
    assert leves.media_cota_3m == pytest.approx(leves.valor_cota, abs=0.01)
    assert leves.alerta_variacao_trimestral is False


# --- N2: assistente de ajuste inteligente (mínimo de eventos, integral recente) ---

from app.autotruck.engine import sugerir_ajuste  # noqa: E402


def _cenario_ajuste():
    """1 veículo (1 cota) → cota = soma dos custos. Integrais de valores
    distintos + 1 parcial, para testar seleção mínima e preferência."""
    veic = [VeiculoAT("V1", "X", "LEVES", "AUTOMOVEL", 9_000, True, True)]
    evs = [
        EventoAT("I1", "P1", "X", "LEVES", "ASSOCIADO", "INTEGRAL", 0, 0, 50, "2025-01-10"),
        EventoAT("I2", "P2", "X", "LEVES", "ASSOCIADO", "INTEGRAL", 0, 0, 30, "2025-03-20"),
        EventoAT("I3", "P3", "X", "LEVES", "ASSOCIADO", "INTEGRAL", 0, 0, 30, "2025-02-05"),
        EventoAT("PA", "P4", "X", "LEVES", "ASSOCIADO", "PARCIAL", 20, 1, 9_000, "2025-03-25"),
    ]
    return calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs)


def test_n2_minimo_de_eventos_e_atinge_alvo() -> None:
    r = _cenario_ajuste()  # cota = 50+30+30+20 = 130
    s = sugerir_ajuste(r, alvo_cota=70.0)
    leves = next(x for x in s if x.segmento == "LEVES")
    assert leves.cota_atual == pytest.approx(130.0)
    assert leves.precisa_ajuste is True
    # precisa reduzir >= 60 → mínimo de eventos: I1(50) + (I2 ou I3, 30) = 80 ≥ 60
    ids = [e.id_evento for e in leves.eventos_sugeridos]
    assert ids[0] == "I1"                       # maior valor primeiro (mínimo de eventos)
    assert len(leves.eventos_sugeridos) == 2
    assert leves.atingiu_alvo is True
    assert leves.cota_resultante <= 70.0 + 0.01
    assert all(e.tipo_evento == "INTEGRAL" for e in leves.eventos_sugeridos)  # não mexe parcial


def test_n2_desempate_pelo_mais_recente() -> None:
    r = _cenario_ajuste()
    leves = next(x for x in sugerir_ajuste(r, alvo_cota=70.0) if x.segmento == "LEVES")
    # I2 e I3 têm o mesmo custo (30); o mais recente (I2, 2025-03-20) vem antes de I3 (02-05)
    assert leves.eventos_sugeridos[1].id_evento == "I2"


def test_n2_dentro_do_alvo_nao_sugere() -> None:
    r = _cenario_ajuste()
    leves = next(x for x in sugerir_ajuste(r, alvo_cota=200.0) if x.segmento == "LEVES")
    assert leves.precisa_ajuste is False
    assert leves.eventos_sugeridos == []
    assert leves.cota_resultante == pytest.approx(leves.cota_atual)


def test_n2_so_integrais_por_padrao_e_parcial_opcional() -> None:
    veic = [VeiculoAT("V1", "X", "LEVES", "AUTOMOVEL", 9_000, True, True)]
    evs = [EventoAT("PA", "P1", "X", "LEVES", "ASSOCIADO", "PARCIAL", 100, 1, 9_000, "2025-03-01")]
    r = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=evs)  # cota 100
    so_int = next(x for x in sugerir_ajuste(r, alvo_cota=10.0) if x.segmento == "LEVES")
    assert so_int.precisa_ajuste is True and so_int.eventos_sugeridos == []  # nada integral
    assert so_int.atingiu_alvo is False
    com_par = next(x for x in sugerir_ajuste(r, alvo_cota=10.0, incluir_parciais=True)
                   if x.segmento == "LEVES")
    assert [e.id_evento for e in com_par.eventos_sugeridos] == ["PA"]


def test_n2_aplicar_ajuste_loga_auditoria_e_baixa_cota() -> None:
    svc = AutoTruckService(AutoTruckRepo(""))
    base = svc.calcular_e_persistir("12/2025", force=True)
    cota0 = base.consolidado.cota_leves
    sug = next(s for s in svc.sugerir_ajuste("12/2025", alvo_cota=cota0 * 0.8)
               if s.segmento == "LEVES")
    ids = [e.id_evento for e in sug.eventos_sugeridos]
    assert ids
    novo = svc.aplicar_ajuste("12/2025", ids)
    assert novo.consolidado.cota_leves < cota0
    assert len(novo.auditoria) == len(ids)
    assert all(a.acao == "EXCLUSAO_MANUAL" and a.justificativa for a in novo.auditoria)


# --- N4: parametrização real de produtos/potes ---

from app.autotruck.rules import ParametrosAT  # noqa: E402


def test_n4_pote_terceiros_por_faixa_de_cobertura() -> None:
    veic = [
        VeiculoAT("V1", "A", "LEVES", "AUTOMOVEL", 50_000, True, True, cobertura_terceiros="50K"),
        VeiculoAT("V2", "B", "LEVES", "AUTOMOVEL", 50_000, True, True, cobertura_terceiros="100K"),
        VeiculoAT("V3", "C", "LEVES", "AUTOMOVEL", 50_000, True, True, cobertura_terceiros="NENHUM"),
        VeiculoAT("V4", "D", "LEVES", "AUTOMOVEL", 50_000, False, True, cobertura_terceiros="100K"),  # inativo
    ]
    ev = [EventoAT("E1", "P", "Z", "LEVES", "ASSOCIADO", "PARCIAL", 30, 1, 50_000, "2025-03-01")]
    r = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=ev)
    c = r.consolidado
    # arrecadação só dos elegíveis: 20 (50K) + 30 (100K) + 0 (NENHUM) = 50
    assert c.pote_terceiros_arrecadado == pytest.approx(50.0, abs=0.01)
    bol = {b.id_veiculo: b for b in r.boletos}
    assert bol["V1"].custo_pote_terceiros == pytest.approx(20.0)
    assert bol["V2"].custo_pote_terceiros == pytest.approx(30.0)
    assert bol["V3"].custo_pote_terceiros == pytest.approx(0.0)
    assert bol["V4"].custo_pote_terceiros == pytest.approx(0.0)  # inativo não paga


def test_n4_pote_caminhao_valor_fixo_por_associado() -> None:
    veic = [
        VeiculoAT("C1", "A", "PESADOS", "CAMINHAO", 300_000, True, True),
        VeiculoAT("C2", "B", "PESADOS", "CAMINHAO", 300_000, True, True),
        VeiculoAT("C3", "C", "PESADOS", "CAMINHAO", 300_000, False, True),  # inativo
    ]
    # arrecadacao_terceiros_estimada=0 p/ isolar o pote caminhão no boleto
    p = ParametrosAT(preco_casco_caminhao=1_200.0, arrecadacao_terceiros_estimada=0.0)
    r = calcular_rateio_at(mes_ano_ref="03/2025", veiculos=veic, eventos=[], params=p)
    pes = next(s for s in r.segmentos if s.segmento == "PESADOS")
    assert pes.arrecadado == pytest.approx(2 * 1_200.0, abs=0.01)  # 2 elegíveis
    bol = {b.id_veiculo: b for b in r.boletos}
    assert bol["C1"].custo_pote_caminhao == pytest.approx(1_200.0)
    assert bol["C3"].custo_pote_caminhao == pytest.approx(0.0)  # inativo não paga
    assert bol["C1"].valor_total_boleto == pytest.approx(1_200.0, abs=0.01)  # só pote (sem rateio variável)


def test_n4_anchor_analitico_inalterado(service: AutoTruckService) -> None:
    """Sem dados de cobertura e preço caminhão=0 → comportamento do anchor
    (ANALITICO) permanece idêntico: terceiros usa a estimada de R$500k."""
    c = service.replay("12/2025").consolidado
    assert c.pote_terceiros_arrecadado == pytest.approx(500_000.0, abs=0.01)
    assert c.bruto_leves == pytest.approx(ALVO_BRUTO_LEVES, abs=0.01)


# --- Cenários de simulação: prova anti-mock (engine == recálculo independente) ---

from app.autotruck.cenarios import build as _build_cen  # noqa: E402
from app.autotruck.verificacao import recomputar as _recomputar  # noqa: E402


@pytest.mark.parametrize("nome", ["A", "B", "C"])
def test_cenario_engine_igual_recomputo_independente(nome) -> None:
    c = _build_cen(nome)
    r = calcular_rateio_at(mes_ano_ref=c.mes_ano_ref, veiculos=c.veiculos,
                           eventos=c.eventos, params=c.params,
                           historico_cotas=c.historico_cotas)
    rec = _recomputar(c.veiculos, c.eventos, c.params)
    for seg in ("LEVES", "MOTOS"):
        s = next(x for x in r.segmentos if x.segmento == seg)
        assert s.custo_a_ratear == pytest.approx(rec[seg]["custo_a_ratear"], abs=0.02)
        assert s.valor_cota == pytest.approx(rec[seg]["valor_cota"], abs=0.02)
        assert s.recuperacao_terceiros == pytest.approx(rec[seg]["recuperacao_terceiros"], abs=0.02)
    assert r.consolidado.pote_terceiros_arrecadado == pytest.approx(
        rec["POTES"]["terceiros_arrecadado"], abs=0.02)
    assert r.consolidado.pote_caminhao_arrecadado == pytest.approx(
        rec["POTES"]["caminhao_arrecadado"], abs=0.02)
    assert r.consolidado.invariante_ok is True


def test_cenarios_comportamento_distinto() -> None:
    rs = {}
    for nome in ("A", "B", "C"):
        c = _build_cen(nome)
        rs[nome] = calcular_rateio_at(mes_ano_ref=c.mes_ano_ref, veiculos=c.veiculos,
                                      eventos=c.eventos, params=c.params,
                                      historico_cotas=c.historico_cotas)
    A, B, C = rs["A"], rs["B"], rs["C"]
    LA = next(s for s in A.segmentos if s.segmento == "LEVES")
    LB = next(s for s in B.segmentos if s.segmento == "LEVES")
    # A saudável: cota na faixa, sem volatilidade
    assert LA.faixa_estabilizacao == "OK" and LA.alerta_volatilidade is False
    # B estresse: volatilidade, regra 75%, cota especial, postergação, cota ACIMA
    assert LB.alerta_volatilidade is True
    assert B.consolidado.eventos_reclassificados_75pct >= 1
    assert B.consolidado.eventos_postergados >= 1
    assert any(b.cota_especial for b in B.boletos)
    assert LB.faixa_estabilizacao == "ACIMA"
    # C purista: elegíveis bem menores que o total
    assert C.consolidado.total_veiculos_elegiveis < 0.75 * C.consolidado.total_veiculos
    # cotas distintas entre cenários (prova: saída reage aos inputs)
    assert len({A.consolidado.cota_leves, B.consolidado.cota_leves,
                C.consolidado.cota_leves}) == 3
