"""Testes da reconciliação de aceite da AVAP (fase 2, CLI e módulo)."""

from pathlib import Path

import pytest

from app.avap.domain import EstadoRateio
from app.avap.historico import EventoRateado, FechamentoHistorico
from app.avap.reconciliacao import reconciliar
from tests.test_avap_fase1 import ev, vei
from tools.reconciliar_avap import main

AVAP = Path(__file__).resolve().parents[2] / "AVAP"


def _hist(protocolos_valores, lancs=()):
    evs = [EventoRateado(p, "AAA1A11", "COLISAO", None, v + 100, 100.0, v) for p, v in protocolos_valores]
    return FechamentoHistorico("Rateio_teste", evs, list(lancs))


def test_reconciliacao_aprova_quando_tudo_bate():
    hist = _hist([(2026000001, 1000.0), (2026000002, 2000.0)])
    sga = [ev(1, 1000.0, estado=EstadoRateio.RATEADO), ev(2, 2000.0, estado=EstadoRateio.RATEADO)]
    rec = reconciliar(hist, sga, [vei(f"P{i}", 4.0) for i in range(50)], valor_cota_declarado=None)
    assert rec.aprovado
    assert any(ln.status == "PENDENTE" for ln in rec.linhas)  # valor da cota sem declarado


def test_reconciliacao_reprova_valor_e_ausente_e_valor_da_cota():
    hist = _hist([(2026000001, 1000.0), (2026000002, 2000.0), (2026000003, 500.0)])
    sga = [ev(1, 999.0, estado=EstadoRateio.RATEADO), ev(2, 2000.0, estado=EstadoRateio.RATEADO)]
    rec = reconciliar(hist, sga, [vei("A", 4.0)])
    itens = {ln.item: ln for ln in rec.linhas}
    assert not rec.aprovado
    assert itens["protocolos do rateio ausentes no SGA"].obs == "2026000003"
    assert itens["valores divergentes do SGA"].obs == "2026000001"


def test_reconciliacao_valor_da_cota_declarado_decide_criterio():
    hist = _hist([(2026000001, 1000.0)])
    sga = [ev(1, 1000.0, estado=EstadoRateio.RATEADO)]
    veic = [vei("A", 10.0), vei("B", 10.0, sv="INADIMPLENTE")]  # TODOS=20 cotas, AMBOS=10 cotas
    rec = reconciliar(hist, sga, veic, valor_cota_declarado=50.0)
    por = {ln.item.split(",")[0]: ln.status for ln in rec.linhas if ln.grupo == "Valor da cota"}
    assert por["valor por cota (TODOS)"] == "OK" and por["valor por cota (AMBOS)"] == "FALHA"


real = pytest.mark.skipif(not AVAP.exists(), reason="AVAP/ (dados reais) ausente")


def _cli(aba, *extra):
    return main([str(AVAP / "rateio_agosto.xlsx"), "--aba", aba, "--eventos", str(AVAP / "foto30-09.xlsx"),
                 "--veiculos", str(AVAP / "Cotas_ativasAVAP_09_26.xlsx"), *extra])


@real
def test_cli_setembro_aprova_com_fila(capsys):
    assert _cli("Rateio_setembro", "--fila", str(AVAP / "foto28-09.xlsx")) == 0
    assert "APROVADO" in capsys.readouterr().out


@real
def test_cli_agosto_reprova_pelas_tres_divergencias_conhecidas(capsys):
    assert _cli("Rateio_agosto") == 1
    out = capsys.readouterr().out
    assert "2026779124" in out and "2026782899" in out and "2026795888" in out


@real
def test_cli_aba_inexistente():
    assert _cli("Rateio_xyz") == 2
