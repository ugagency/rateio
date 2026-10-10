"""Testes da fase 1 do motor AVAP: histórico, seleção e motor.

O aceite sobre dados reais (AVAP/, gitignored) é pulado se a pasta não existir.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from app.avap.domain import (
    Decisao,
    DecisaoEvento,
    EstadoRateio,
    EventoAVAP,
    Lancamento,
    TipoLancamento,
    VeiculoAVAP,
)
from app.avap.engine import calcular_rateio
from app.avap.historico import classificar_linha, ler_historico
from app.avap.ingestao import ler_eventos, ler_veiculos
from app.avap.rules import RegrasAVAP
from app.avap.selecao import selecionar

AVAP = Path(__file__).resolve().parents[2] / "AVAP"


def P(n: int) -> int:
    """Protocolo de teste: números pequenos viram protocolos de 10 dígitos (evita o alerta A1)."""
    return 2026000000 + n if n < 10_000_000 else n


def ev(prot=1, custo=1000.0, part=100.0, motivo="COLISAO", estado=EstadoRateio.NA_FILA,
       situacao="FINALIZADO", tipo="Evento Associado", fin=date(2026, 9, 10)) -> EventoAVAP:
    return EventoAVAP(
        protocolo=P(prot), situacao=situacao, data_finalizacao=fin, valor_reparo=custo + part,
        valor_participacao=part, custo_evento=custo, previsao_reparo=0.0, motivo=motivo,
        estado_rateio=estado, valor_rateado=None, data_cadastro=None, rotulo_cota=None, peso_cota=None,
        sufixo_cota=None, categoria=None, modelo=None, tipo_veiculo=None, tipo_evento=tipo, placa=None)


def inc(p, j="ok"):
    return DecisaoEvento(P(p), Decisao.INCLUIR, j)


def exc(p, j="ok"):
    return DecisaoEvento(P(p), Decisao.EXCLUIR, j)


# ───────── classificação das linhas sem placa ─────────


@pytest.mark.parametrize("desc,valor,tipo,codigo", [
    ("RECEITA COM VENDAS DE SALVADOS", -194771.47, TipoLancamento.DEDUCAO, "SALVADOS"),
    ("E-SAUDE", 16310.38, TipoLancamento.SOMA, "E_SAUDE"),
    ("RASTREAMENTO", 119481.22, TipoLancamento.SOMA, "RASTREAMENTO"),
    ("INADIMPLÊNCIA AGO. 2026", 99605.19, TipoLancamento.SOMA, "INADIMPLENCIA"),
    ("RECEITA INAD. JULHO 2026", -42840.2, TipoLancamento.DEDUCAO, "RECUP_INADIMPLENCIA"),
    ("RECEBIDOS AGO 2026", -45521.49, TipoLancamento.DEDUCAO, "RECUP_INADIMPLENCIA"),
    (None, -129253.0, TipoLancamento.DEDUCAO, "NAO_CLASSIFICADO"),
])
def test_classificar_linha(desc, valor, tipo, codigo):
    lan = classificar_linha(desc, valor)
    assert (lan.tipo, lan.codigo, lan.valor) == (tipo, codigo, round(abs(valor), 2))


# ───────── seleção ─────────


def test_fila_sem_alerta_entra_por_regra():
    r = selecionar([ev(1, 1000), ev(2, 2000, estado=EstadoRateio.NAO_RATEADO)] + [ev(10 + i, 1000) for i in range(20)])
    protocolos = {s.evento.protocolo for s in r.selecionados}
    assert P(1) in protocolos and P(2) not in protocolos  # vazio não é candidato por regra
    assert all(s.origem == "REGRA" for s in r.selecionados) and r.homologavel


@pytest.mark.parametrize("kw,codigo", [
    (dict(prot=20260001), "A1"),
    (dict(prot=2020000001), "A1"),
    (dict(custo=0.0, part=0.0), "A2"),
    (dict(custo=300.0, part=0.0), "A3"),
    (dict(motivo="V.F.I"), "A5"),
])
def test_alertas_bloqueiam_ate_haver_decisao(kw, codigo):
    base = [ev(100 + i, 5000) for i in range(30)]
    alvo = ev(**{"prot": 999, **kw})
    r = selecionar(base + [alvo])
    assert codigo in {a.codigo for a in r.alertas if a.protocolo == alvo.protocolo}
    assert alvo.protocolo in r.pendencias and not r.homologavel
    r2 = selecionar(base + [alvo], decisoes=[inc(alvo.protocolo, "conferido")])
    assert r2.homologavel and alvo.protocolo in {s.evento.protocolo for s in r2.selecionados}


def test_a4_concentracao_e_a7_inconsistencia():
    grande = ev(5, 50_000)
    r = selecionar([grande] + [ev(10 + i, 1000) for i in range(10)])
    assert "A4" in {a.codigo for a in r.alertas if a.protocolo == P(5)}
    torto = replace(ev(6, 1000), valor_reparo=5000.0)
    r = selecionar([torto] + [ev(10 + i, 1000) for i in range(30)])
    assert "A7" in {a.codigo for a in r.alertas if a.protocolo == P(6)}


def test_a6_data_alterada():
    base = [ev(10 + i, 1000) for i in range(30)]
    r = selecionar(base + [ev(7, 1000)], datas_anteriores={P(7): date(2026, 9, 1)})
    assert P(7) in r.pendencias


def test_inclusao_manual_do_vazio_e_exclusao():
    base = [ev(1, 1000), ev(2, 1000, estado=EstadoRateio.NAO_RATEADO), ev(3, 1000)]
    base += [ev(50 + i, 1000) for i in range(30)]  # dilui o A4
    r = selecionar(base, decisoes=[inc(2, "acordo fechado"), exc(3, "salvado pendente")])
    sel = {s.evento.protocolo: s.origem for s in r.selecionados}
    assert sel[P(1)] == "REGRA" and sel[P(2)] == "DECISAO" and P(3) not in sel
    assert any("salvado pendente" in n.motivo for n in r.nao_selecionados)
    assert any("INCLUIR" in a for a in r.auditoria)


def test_decisao_exige_justificativa_e_nao_duplica():
    with pytest.raises(ValueError):
        selecionar([ev(1)], decisoes=[inc(1, "  ")])
    with pytest.raises(ValueError):
        selecionar([ev(1)], decisoes=[inc(1), exc(1)])


def test_decisao_para_protocolo_inexistente_bloqueia():
    r = selecionar([ev(1)], decisoes=[inc(999)])
    assert r.bloqueios == [P(999)] and not r.homologavel


def test_fora_por_regra():
    base = [ev(1, situacao="CANCELADO"), ev(2, tipo="Evento Terceiro"), ev(3, fin=date(2026, 9, 30)),
            ev(4), ev(5, estado=EstadoRateio.RATEADO)]
    r = selecionar(base, data_fechamento=date(2026, 9, 28), ja_rateados=frozenset({P(4)}))
    assert not r.selecionados
    motivos = {n.evento.protocolo - 2026000000: n.motivo for n in r.nao_selecionados}
    assert "CANCELADO" in motivos[1] and "terceiro" in motivos[2] and "corte" in motivos[3]
    assert "anterior" in motivos[4] and "RATEADO" in motivos[5]


def test_incluir_protocolo_ja_rateado_bloqueia():
    r = selecionar([ev(4)], decisoes=[inc(4)], ja_rateados=frozenset({P(4)}))
    assert r.bloqueios == [P(4)] and not r.selecionados


def test_duplicata_identica_deduplica_e_divergente_bloqueia():
    lote = [ev(10 + i, 1000) for i in range(30)]
    r = selecionar(lote + [ev(10, 1000)])
    assert len([s for s in r.selecionados if s.evento.protocolo == P(10)]) == 1
    assert r.homologavel and any("deduplicadas" in a for a in r.auditoria)
    r = selecionar(lote + [ev(10, 2000)])
    assert r.bloqueios == [P(10)] and not r.homologavel
    assert P(10) not in {s.evento.protocolo for s in r.selecionados}


# ───────── motor ─────────


def vei(placa="AAA1A11", peso=4.0, sv="ATIVO", sa="ATIVO", fipe=20000.0):
    return VeiculoAVAP(placa, "COTA", peso, None, "PASSEIO", "AUTOMOVEL", fipe, sv, sa, 1)


def test_motor_numerador_e_boletos():
    veic = [vei(f"P{i}", 4.0) for i in range(50)]  # 200 cotas
    r = calcular_rateio(
        [ev(1, 1500.0), ev(2, 500.0)],
        [Lancamento(TipoLancamento.SOMA, "E_SAUDE", "x", 300.0),
         Lancamento(TipoLancamento.DEDUCAO, "SALVADOS", "y", 200.0)],
        veic)
    assert (r.custo_eventos, r.somas, r.deducoes, r.numerador) == (2000.0, 300.0, 200.0, 2100.0)
    assert r.total_cotas == 200 and r.valor_cota == pytest.approx(10.5)
    assert r.boletos[0].contribuicao_rateio == 42.0 and r.boletos[0].total == 42.0
    assert r.aprovado and r.diferenca_arredondamento == 0
    assert r.eventos_por_motivo == {"COLISAO": 2}


def test_motor_elegibilidade_d2_e_d4():
    veic = [vei("A"), vei("B", sv="INADIMPLENTE"), vei("C", sa="INADIMPLENTE"), vei("D", peso=0.0),
            vei("E", sa="PENDENTE ADESÃO"), vei(None, fipe=0.0)]
    base = dict(eventos=[ev(1, 1000.0)], lancamentos=[], veiculos=veic)
    amb = calcular_rateio(**base)
    assert amb.veiculos_elegiveis == 1 and amb.veiculos_fora == {
        "VEICULO_INADIMPLENTE": 1, "ASSOCIADO_INADIMPLENTE": 1, "PESO_ZERO": 1,
        "ASSOCIADO_PENDENTE": 1, "SEM_PLACA_SEM_FIPE": 1}
    assert calcular_rateio(**base, regras=RegrasAVAP(criterio_elegibilidade="VEICULO")).veiculos_elegiveis == 2
    assert calcular_rateio(**base, regras=RegrasAVAP(criterio_elegibilidade="ASSOCIADO")).veiculos_elegiveis == 2
    assert calcular_rateio(**base, regras=RegrasAVAP(criterio_elegibilidade="TODOS")).veiculos_elegiveis == 3


def test_motor_split_e_denominador_zero():
    r = calcular_rateio([ev(1, 100.0)], [], [vei("A", 2.0)], RegrasAVAP(
        taxa_administracao_por_cota=0.5, produtos_beneficios_por_cota=1.0))
    b = r.boletos[0]
    assert (b.contribuicao_rateio, b.taxa_administracao, b.produtos_beneficios, b.total) == (100.0, 1.0, 2.0, 103.0)
    with pytest.raises(ValueError):
        calcular_rateio([ev(1)], [], [vei("A", sv="INADIMPLENTE")])


def test_motor_invariante_de_arredondamento_reportada():
    veic = [vei(f"P{i}", 1.0) for i in range(3)]
    r = calcular_rateio([ev(1, 100.0)], [], veic)  # 33,33 x 3 = 99,99
    assert r.diferenca_arredondamento == pytest.approx(-0.01) and r.invariantes["arredondamento"]


# ───────── aceite sobre dados reais ─────────

real = pytest.mark.skipif(not AVAP.exists(), reason="AVAP/ (dados reais) ausente")


@real
def test_real_historico_totais():
    h = ler_historico(AVAP / "rateio_agosto.xlsx")
    ago, setb = h["Rateio_agosto"], h["Rateio_setembro"]
    assert (len(ago.eventos), ago.total_eventos, ago.total) == (150, 1_775_640.36, 1_806_046.24)
    assert (len(setb.eventos), setb.total_eventos, setb.total) == (103, 1_733_393.65, 1_802_067.92)
    assert ago.nao_classificadas == [] and setb.nao_classificadas == ["(sem descrição)"]


@real
def test_real_selecao_setembro_reproduz_fechamento():
    """Fila do SGA de 28/09 + decisões do operador = exatamente a aba Rateio_setembro."""
    setb = ler_historico(AVAP / "rateio_agosto.xlsx")["Rateio_setembro"]
    eventos = ler_eventos(AVAP / "foto28-09.xlsx").eventos
    fila = {e.protocolo for e in eventos if e.estado_rateio == EstadoRateio.NA_FILA}
    assert len(fila) == 80 and fila - setb.protocolos == {2026819916}
    manuais = setb.protocolos - fila
    assert len(manuais) == 24  # 22 integrais + 1 colisão + 1 continuação, vazios no SGA

    decisoes = [inc(p, "fechamento real 09/2026") for p in setb.protocolos]
    decisoes.append(exc(2026819916, "fora do fechamento real; critério a obter da AVAP"))
    r = selecionar(eventos, decisoes=decisoes)
    assert {s.evento.protocolo for s in r.selecionados} == setb.protocolos
    assert r.total_custo == setb.total_eventos == 1_733_393.65
    assert r.homologavel and not r.bloqueios

    # Sem decisões, só a fila sem alerta entra e o resto fica pendente (a homologação trava).
    sem = selecionar(eventos)
    assert not sem.homologavel and len(sem.pendencias) > 0
    assert {s.evento.protocolo for s in sem.selecionados} <= fila


@real
def test_real_motor_fecha_total_de_setembro():
    h = ler_historico(AVAP / "rateio_agosto.xlsx")["Rateio_setembro"]
    eventos = {e.protocolo: e for e in ler_eventos(AVAP / "foto30-09.xlsx").eventos}
    veiculos = ler_veiculos(AVAP / "Cotas_ativasAVAP_09_26.xlsx").veiculos
    r = calcular_rateio([eventos[p] for p in h.protocolos], h.lancamentos, veiculos)
    assert r.numerador == 1_802_067.92 and r.aprovado
    assert r.valor_cota * r.total_cotas == pytest.approx(r.numerador)
