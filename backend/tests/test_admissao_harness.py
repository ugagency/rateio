"""Teste de aceite do contrato de exportação do MVP Admissão Verificada
(SPEC-008). Roda o exportador de referência sobre uma competência conhecida e
exige que o motor aprovado reconheça os arquivos e feche o invariante. Trava a
regressão do contrato: qualquer mudança que quebre a paridade falha o build.
"""

import sys
from pathlib import Path

import pytest

# o exportador/harness de referência vive fora do backend
REF = Path(__file__).resolve().parents[2] / "admissao-verificada" / "reference"
pytestmark = pytest.mark.skipif(
    not (REF / "harness.py").exists(), reason="harness de referência ausente"
)
sys.path.insert(0, str(REF))


def test_contrato_exportacao_reconciliacao_invariante_zero():
    from harness import rodar_harness

    r = rodar_harness()
    assert r["tipo_base"] == "BASE"
    assert r["tipo_rateio"] == "RATEIO"
    assert r["roundtrip_ok"], r["roundtrip"]
    assert r["eventos_lidos"] == r["eventos_exportados"]
    assert r["invariante_ok"], f"Δ={r['dif']}"
    assert abs(r["dif"]) < 0.01
    assert not r["alertas"], r["alertas"]
