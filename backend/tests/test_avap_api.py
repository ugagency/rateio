"""API /avap com os arquivos reais de 09/2026 (AVAP/ é gitignored: sem eles, os testes são pulados)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

RAIZ = Path(__file__).resolve().parents[2] / "AVAP"
VEIC, FILA = RAIZ / "Cotas_ativasAVAP_09_26.xlsx", RAIZ / "foto28-09.xlsx"
pytestmark = pytest.mark.skipif(not (VEIC.exists() and FILA.exists()), reason="dados reais da AVAP ausentes")

client = TestClient(app)


def _upload(mes="10/2026"):
    with open(VEIC, "rb") as v, open(FILA, "rb") as e:
        return client.post("/avap/selecionar", data={"mes_ano_ref": mes},
                           files={"veiculos": ("v.xlsx", v), "eventos": ("e.xlsx", e)})


def test_inspecionar_arquivo_valida_e_rejeita():
    with open(VEIC, "rb") as f:
        ok = client.post("/avap/inspecionar-arquivo", data={"slot": "VEICULOS"}, files={"arquivo": ("v.xlsx", f)})
    assert ok.json()["valido"] and ok.json()["resumo"]["veiculos"] == 39242
    with open(VEIC, "rb") as f:  # slot trocado: veículos enviado como eventos
        ruim = client.post("/avap/inspecionar-arquivo", data={"slot": "EVENTOS"}, files={"arquivo": ("v.xlsx", f)})
    assert ruim.json()["valido"] is False and ruim.json()["erro"]


def test_calculo_bloqueado_com_pendencias_e_liberado_apos_decidir():
    r = _upload()
    assert r.status_code == 200
    sel = r.json()
    assert sel["pendencias"] and not sel["homologavel"]
    assert client.post("/avap/10-2026/calcular", json={"criterio": "VEICULO"}).status_code == 409

    decisoes = [{"protocolo": p, "decisao": "INCLUIR", "justificativa": "revisado pelo operador"}
                for p in sel["pendencias"]]
    assert client.post("/avap/10-2026/decidir", json={"decisoes": decisoes}).json()["homologavel"]
    client.post("/avap/10-2026/lancamentos", json={"lancamentos": [
        {"descricao": "RASTREAMENTO", "valor": 118173.45}, {"descricao": "RECEBIDOS AGO 2026", "valor": -45521.49}]})
    res = client.post("/avap/10-2026/calcular", json={"criterio": "VEICULO"})
    assert res.status_code == 200
    d = res.json()
    assert d["aprovado"] and d["valor_cota_estimado"] and set(d["comparativo_criterios"]) == {"TODOS", "VEICULO", "ASSOCIADO", "AMBOS"}
    assert d["somas"] == 118173.45 and d["deducoes"] == 45521.49


def test_demo_setembro_reproduz_fechamento_real():
    assert client.post("/avap/demo-setembro").json()["selecionados"] == 103
    d = client.post("/avap/09-2026/calcular", json={"criterio": "VEICULO"}).json()
    assert d["numerador"] == 1802067.92 and d["custo_eventos"] == 1733393.65
    page = client.get("/avap/09-2026/boletos", params={"page_size": 5}).json()
    assert page["total"] == d["total_boletos"] and len(page["items"]) == 5
    assert "placa;matricula" in client.get("/avap/09-2026/boletos.csv").text


def test_criterio_invalido_e_competencia_inexistente():
    assert client.post("/avap/01-2020/calcular", json={}).status_code == 404
    client.post("/avap/demo-setembro")
    assert client.post("/avap/09-2026/calcular", json={"criterio": "XYZ"}).status_code == 400
