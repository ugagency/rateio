"""Golden test de ACEITE — o FECHAMENTO real da AutoTruck.

Garante permanentemente que: ingerimos o arquivo *deles* (layout do SGA),
o engine roda sobre os eventos *deles* e reproduz o ANALITICO *deles*
centavo a centavo (|Δ| ≤ R$ 0,01). Fixture: tests/fixtures/FECHAMENTO_referencia.xlsx
"""

from pathlib import Path

import pytest

from app.autotruck.ingestao import ler_fechamento, reconciliar

FIX = Path(__file__).parent / "fixtures" / "FECHAMENTO_referencia.xlsx"
pytestmark = pytest.mark.skipif(not FIX.exists(), reason="fixture do FECHAMENTO ausente")


def test_ingestao_le_eventos_e_analitico_reais() -> None:
    f = ler_fechamento(str(FIX))
    assert len(f.eventos) >= 250                       # ~284 eventos reais
    a = f.analitico
    assert a.rateio_leves == pytest.approx(2_616_217.12, abs=0.01)
    assert a.rateio_motos == pytest.approx(500_182.55, abs=0.01)
    assert a.integral_leves == pytest.approx(1_834_103.63, abs=0.01)
    assert a.parcial_leves == pytest.approx(782_113.49, abs=0.01)
    assert a.terceiros_leves_total == pytest.approx(756_464.11, abs=0.01)
    assert a.terceiros_motos_total == pytest.approx(32_982.25, abs=0.01)
    assert a.pesados_terceiros_total == pytest.approx(14_000.00, abs=0.01)


def test_reconciliacao_aprovada_centavo_a_centavo() -> None:
    rec = reconciliar(str(FIX))
    # nenhuma linha pode estar em FALHA
    falhas = [ln for ln in rec.linhas if ln.status == "FALHA"]
    assert not falhas, f"linhas em FALHA: {[(l.item, l.delta) for l in falhas]}"
    assert rec.aprovado is True
    # todas as linhas reconciliam dentro de R$ 0,01
    assert all(abs(ln.delta) <= 0.01 for ln in rec.linhas)


def test_engine_sobre_eventos_deles_reproduz_o_rateio_deles() -> None:
    rec = reconciliar(str(FIX))
    by = {ln.item: ln for ln in rec.linhas}
    for item in ("LEVES RATEIO (bruto)", "MOTOS RATEIO (bruto)",
                 "LEVES integral", "MOTOS parcial", "PESADOS terceiros"):
        assert by[item].status == "OK"
        assert abs(by[item].delta) <= 0.01
