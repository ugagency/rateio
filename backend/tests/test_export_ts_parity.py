"""Paridade do exportador TypeScript (P2).

Gera BASE e RATEIO pelo escritor TS do app e confirma que o motor aprovado os
aceita (detectar_tipo, roundtrip de cotas, invariante zero), com a mesma
fixture do harness Python. Pula quando Node ou esbuild não estão disponíveis
(ambiente mínimo de CI sem o app instalado).
"""

import sys
from pathlib import Path

import pytest

REF_TS = Path(__file__).resolve().parents[2] / "admissao-verificada" / "reference" / "ts_parity"
pytestmark = pytest.mark.skipif(not (REF_TS / "check.py").exists(), reason="check de paridade TS ausente")
sys.path.insert(0, str(REF_TS))


def test_exportador_ts_tem_paridade_com_o_motor():
    import check

    ok, motivo = check.disponivel()
    if not ok:
        pytest.skip(motivo)

    r = check.rodar()
    assert r["tipo_base"] == "BASE"
    assert r["tipo_rateio"] == "RATEIO"
    assert r["roundtrip_ok"], r
    assert r["eventos_lidos"] == 6
    assert r["invariante_ok"], f"Δ={r['dif']}"
    assert abs(r["dif"]) < 0.01
