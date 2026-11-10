"""Simulador da Fenaprove: registro do lead em CSV fora do repositório."""

import csv

import httpx
from fastapi.testclient import TestClient

from app.api import simulador
from app.main import app

client = TestClient(app)

ZAP = "(31) 98888-7777"
BASE = {"nome": "Visitante Teste", "email": "visitante@exemplo.com.br", "consentimento": True}


def _lead(id_, **extra):
    return {**BASE, "id": id_, **extra}


def _linhas(tmp_path):
    texto = (tmp_path / "leads_fenaprove.csv").read_text(encoding="utf-8-sig")
    return list(csv.DictReader(texto.splitlines(), delimiter=";"))


def test_lead_classifica_e_grava(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    zap = {"quer_whatsapp": True, "whatsapp": ZAP}
    quente = client.post("/avap/simulador/lead", json=_lead("lead-0001", sistema_gestao="SGA (Hinova)", **zap))
    morno = client.post("/avap/simulador/lead", json=_lead("lead-0002", sistema_gestao="Outro sistema", **zap))
    frio = client.post("/avap/simulador/lead", json=_lead("lead-0003", sistema_gestao="Outro sistema"))
    morno_sga = client.post("/avap/simulador/lead", json=_lead("lead-0004", sistema_gestao="SGA (Hinova)"))
    assert [r.json()["classificacao"] for r in (quente, morno, frio, morno_sga)] == ["quente", "morno", "frio", "morno"]
    r = client.get("/avap/simulador/leads").json()
    assert (r["total"], r["quente"], r["morno"], r["frio"], r["com_simulacao"]) == (4, 1, 2, 1, 0)
    texto = client.get("/avap/simulador/leads.csv").content.decode("utf-8-sig")
    assert len(texto.splitlines()) == 5 and "Visitante Teste" in texto and "visitante@exemplo.com.br" in texto


def test_email_e_obrigatorio_e_validado(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    sem_email = {k: v for k, v in _lead("lead-0001").items() if k != "email"}
    assert client.post("/avap/simulador/lead", json=sem_email).status_code == 422
    for ruim in ("sdfwdwsf@@@sddf", "sem-arroba.com", "a@b", "a b@exemplo.com"):
        assert client.post("/avap/simulador/lead", json=_lead("lead-0001", email=ruim)).status_code == 422, ruim
    assert client.get("/avap/simulador/leads").json()["total"] == 0


def test_whatsapp_so_e_pedido_e_guardado_quando_o_visitante_quer(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    # só e-mail: não exige WhatsApp, e o que vier digitado não é guardado
    assert client.post("/avap/simulador/lead", json=_lead("lead-0001", whatsapp=ZAP)).status_code == 200
    # quer o WhatsApp: precisa ser válido
    for ruim in ("", "00000000000", "(31) 99999-9999", "(31) 88887-7777", "1234"):
        r = client.post("/avap/simulador/lead", json=_lead("lead-0002", quer_whatsapp=True, whatsapp=ruim))
        assert r.status_code == 422, ruim
    assert client.post("/avap/simulador/lead", json=_lead("lead-0003", quer_whatsapp=True, whatsapp="+55 (31) 98888-7777")).status_code == 200
    linhas = {x["id"]: x for x in _linhas(tmp_path)}
    assert linhas["lead-0001"]["whatsapp"] == "" and linhas["lead-0001"]["quer_whatsapp"] == "não"
    assert linhas["lead-0003"]["whatsapp"] == "+55 (31) 98888-7777" and linhas["lead-0003"]["quer_whatsapp"] == "sim"


def test_mesmo_id_atualiza_a_linha_e_guarda_a_simulacao(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    contato = _lead("lead-0001", sistema_gestao="SGA (Hinova)", modelo_rateio="Pote único",
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
    assert client.post("/avap/simulador/lead", json=_lead("lead-0001")).status_code == 200
    copias = list(tmp_path.glob("leads_fenaprove_anterior_*.csv"))
    assert len(copias) == 1 and "Antigo" in copias[0].read_text(encoding="utf-8-sig")
    assert len(_linhas(tmp_path)) == 1


def test_lead_sem_consentimento_nao_grava(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    assert client.post("/avap/simulador/lead", json=_lead("lead-0001", consentimento=False)).status_code == 422
    assert client.get("/avap/simulador/leads").json()["total"] == 0


def test_rotas_avap_continuam_respondendo():
    assert client.post("/avap/demo-fenauto").status_code == 200


class _N8nFalso:
    """Substitui o httpx.Client: guarda o que seria enviado ao n8n e pode simular queda."""

    enviados: list = []
    fora_do_ar = False

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, json, headers):
        req = httpx.Request("POST", url)
        if _N8nFalso.fora_do_ar:
            raise httpx.ConnectError("sem internet", request=req)
        _N8nFalso.enviados.append((url, json, headers))
        return httpx.Response(200, request=req)


def _n8n(monkeypatch, tmp_path, fora_do_ar=False):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    monkeypatch.setenv("N8N_WEBHOOK_URL", "https://n8n.exemplo/webhook/mut-leads")
    monkeypatch.setenv("N8N_WEBHOOK_SECRET", "segredo-teste")
    monkeypatch.setattr(simulador.httpx, "Client", _N8nFalso)
    _N8nFalso.enviados = []
    _N8nFalso.fora_do_ar = fora_do_ar


def test_sem_webhook_nada_e_enviado(tmp_path, monkeypatch):
    monkeypatch.setenv("MUT_LEADS_DIR", str(tmp_path))
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    assert client.post("/avap/simulador/lead", json=_lead("lead-0001")).status_code == 200
    assert _linhas(tmp_path)[0]["sincronizado"] == "não"
    assert client.post("/avap/simulador/sincronizar").status_code == 409


def test_lead_vai_para_o_n8n_com_segredo(tmp_path, monkeypatch):
    _n8n(monkeypatch, tmp_path)
    client.post("/avap/simulador/lead", json=_lead("lead-0001", quer_whatsapp=True, whatsapp=ZAP))
    url, corpo, cab = _N8nFalso.enviados[0]
    assert url.endswith("/mut-leads") and cab == {"X-Mut-Secret": "segredo-teste"}
    assert corpo["id"] == "lead-0001" and corpo["quer_whatsapp"] == "sim" and corpo["email"] == "visitante@exemplo.com.br"
    assert "sincronizado" not in corpo
    assert _linhas(tmp_path)[0]["sincronizado"] == "sim"
    assert client.get("/avap/simulador/leads").json()["pendentes_n8n"] == 0


def test_queda_deixa_pendente_e_reenvia_depois(tmp_path, monkeypatch):
    _n8n(monkeypatch, tmp_path, fora_do_ar=True)
    client.post("/avap/simulador/lead", json=_lead("lead-0001"))
    client.post("/avap/simulador/lead", json=_lead("lead-0002"))
    assert [x["sincronizado"] for x in _linhas(tmp_path)] == ["não", "não"]
    _N8nFalso.fora_do_ar = False
    assert client.post("/avap/simulador/sincronizar").json() == {"enviados": 2, "pendentes": 0}
    assert [c["id"] for _, c, _ in _N8nFalso.enviados] == ["lead-0001", "lead-0002"]


def test_resultado_reenvia_o_mesmo_lead(tmp_path, monkeypatch):
    _n8n(monkeypatch, tmp_path)
    contato = _lead("lead-0001", quer_whatsapp=True, whatsapp=ZAP)
    client.post("/avap/simulador/lead", json=contato)
    client.post("/avap/simulador/lead", json={**contato, "etapa": "resultado", "simulacao": {"valor_cota": "8.3333"}})
    etapas = [(c["etapa"], c["valor_cota"]) for _, c, _ in _N8nFalso.enviados]
    assert etapas == [("contato", ""), ("resultado", "8.3333")]
    assert _linhas(tmp_path)[0]["sincronizado"] == "sim"
