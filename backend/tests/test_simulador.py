"""Simulador da Fenaprove: registro do lead em CSV fora do repositório."""

import csv

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BASE = {"nome": "Visitante Teste", "whatsapp": "31999990000", "consentimento": True}


def _lead(id_, **extra):
    return {**BASE, "id": id_, **extra}


def _linhas(tmp_path):
    texto = (tmp_path / "leads_fenaprove.csv").read_text(encoding="utf-8-sig")
    return list(csv.DictReader(texto.splitlines(), delimiter=";"))


def test_lead_classifica_e_grava(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    quente = client.post("/avap/simulador/lead", json=_lead("lead-0001", quer_versao=True, sistema_gestao="SGA (Hinova)"))
    morno = client.post("/avap/simulador/lead", json=_lead("lead-0002", quer_versao=True, sistema_gestao="Outro sistema"))
    frio = client.post("/avap/simulador/lead", json=_lead("lead-0003", quer_versao=False, sistema_gestao="SGA (Hinova)"))
    assert [r.json()["classificacao"] for r in (quente, morno, frio)] == ["quente", "morno", "frio"]
    r = client.get("/avap/simulador/leads").json()
    assert (r["total"], r["quente"], r["morno"], r["frio"], r["com_simulacao"]) == (3, 1, 1, 1, 0)
    texto = client.get("/avap/simulador/leads.csv").content.decode("utf-8-sig")
    assert len(texto.splitlines()) == 4 and "Visitante Teste" in texto


def test_mesmo_id_atualiza_a_linha_e_guarda_a_simulacao(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    contato = _lead("lead-0001", quer_versao=True, sistema_gestao="SGA (Hinova)", modelo_rateio="Pote único",
                    rateio_hoje="Equipe interna em planilha")
    assert client.post("/avap/simulador/lead", json=contato).json()["etapa"] == "contato"
    resultado = {**contato, "etapa": "resultado", "simulacao": {
        "faixa_veiculos": "10.001 a 20.000", "valor_cota": "8.3333", "eventos_qtd": 75}}
    assert client.post("/avap/simulador/lead", json=resultado).json()["etapa"] == "resultado"
    # reenvio atrasado do passo 1 (fila offline): não desfaz a etapa nem apaga a simulação
    assert client.post("/avap/simulador/lead", json=contato).json()["etapa"] == "resultado"
    linhas = _linhas(tmp_path)
    assert len(linhas) == 1
    assert linhas[0]["faixa_veiculos"] == "10.001 a 20.000" and linhas[0]["valor_cota"] == "8.3333"
    assert linhas[0]["modelo_rateio"] == "Pote único" and linhas[0]["rateio_hoje"] == "Equipe interna em planilha"
    assert client.get("/avap/simulador/leads").json()["com_simulacao"] == 1


def test_arquivo_com_cabecalho_antigo_e_preservado(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    (tmp_path / "leads_fenaprove.csv").write_text("nome;whatsapp\nAntigo;3188887777\n", encoding="utf-8-sig")
    assert client.post("/avap/simulador/lead", json=_lead("lead-0001", quer_versao=True)).status_code == 200
    copias = list(tmp_path.glob("leads_fenaprove_anterior_*.csv"))
    assert len(copias) == 1 and "Antigo" in copias[0].read_text(encoding="utf-8-sig")
    assert len(_linhas(tmp_path)) == 1


def test_lead_sem_consentimento_nao_grava(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    assert client.post("/avap/simulador/lead", json=_lead("lead-0001", consentimento=False)).status_code == 422
    assert client.get("/avap/simulador/leads").json()["total"] == 0


def test_rotas_avap_continuam_respondendo():
    assert client.post("/avap/demo-fenauto").status_code == 200
