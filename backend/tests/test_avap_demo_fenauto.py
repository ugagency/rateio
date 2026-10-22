"""Demo Fenauto: roda com os arquivos fictícios versionados em demo_fenauto/, sem depender de AVAP/."""

import pytest
from fastapi.testclient import TestClient

from app.api.avap import DEMO
from app.main import app

client = TestClient(app)


def test_demo_fenauto_fecha_em_778_sem_diferenca():
    sel = client.post("/avap/demo-fenauto").json()
    assert sel["selecionados"] == 103 and sel["homologavel"] and "Fenauto" in sel["origem"]
    d = client.post("/avap/09-2026/calcular", json={"criterio": "VEICULO"}).json()
    assert d["aprovado"] and d["numerador"] == 1801505.68 and d["total_cotas"] == 231556
    assert round(d["valor_cota"], 6) == 7.78 and d["diferenca_arredondamento"] == 0
    assert d["total_rateio"] == d["numerador"]
    assert all(lanc["codigo"] != "NAO_CLASSIFICADO" for lanc in d["lancamentos"])
    assert "boletos_fenauto" in client.get("/avap/09-2026/boletos.csv").headers["content-disposition"]


@pytest.mark.skipif(not DEMO["veiculos"].exists(), reason="dados reais da AVAP ausentes")
def test_demo_fenauto_nao_repete_protocolo_nem_placa_reais():
    client.post("/avap/demo-setembro")
    reais = client.get("/avap/09-2026/eventos", params={"page_size": 500}).json()["items"]
    client.post("/avap/demo-fenauto")
    fict = client.get("/avap/09-2026/eventos", params={"page_size": 500}).json()["items"]
    assert not {e["protocolo"] for e in reais} & {e["protocolo"] for e in fict}
    assert not {e["placa"] for e in reais if e["placa"]} & {e["placa"] for e in fict if e["placa"]}
