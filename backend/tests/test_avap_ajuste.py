"""Assistente de ajuste da cota no pote único (app/avap/ajuste.py e rotas /avap/{mes}/...-ajuste)."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.avap.ajuste import sugerir_ajuste
from app.avap.domain import EstadoRateio, EventoAVAP
from app.main import app


def _ev(protocolo: int, custo: float, dia: int = 1) -> EventoAVAP:
    return EventoAVAP(
        protocolo=protocolo, situacao="FINALIZADO", data_finalizacao=date(2026, 9, dia), valor_reparo=custo,
        valor_participacao=0.0, custo_evento=custo, previsao_reparo=0.0, motivo="COLISAO",
        estado_rateio=EstadoRateio.NA_FILA, valor_rateado=None, data_cadastro=None, rotulo_cota=None,
        peso_cota=None, sufixo_cota=None, categoria=None, modelo=None, tipo_veiculo=None,
        tipo_evento="Evento Associado", placa=None)


def test_dentro_do_alvo_nao_sugere_nada():
    s = sugerir_ajuste([_ev(1, 100)], numerador=1000, total_cotas=100, alvo_cota=10)
    assert not s.precisa_ajuste and s.eventos_sugeridos == [] and s.cota_resultante == 10


def test_ultimo_passo_escolhe_o_menor_evento_que_cobre():
    # cota 20, alvo 15: precisa reduzir 500. O de 600 cobre sozinho e passa menos do alvo que o de 900.
    evs = [_ev(1, 900), _ev(2, 600), _ev(3, 300), _ev(4, 100)]
    s = sugerir_ajuste(evs, numerador=2000, total_cotas=100, alvo_cota=15)
    assert [e.protocolo for e in s.eventos_sugeridos] == [2]
    assert s.atingiu_alvo and s.cota_resultante == 14 and s.reducao_necessaria == 500


def test_sem_evento_que_cubra_sozinho_comeca_pelo_maior():
    evs = [_ev(1, 300), _ev(2, 250), _ev(3, 100)]
    s = sugerir_ajuste(evs, numerador=2000, total_cotas=100, alvo_cota=15)  # precisa de 500
    assert [e.protocolo for e in s.eventos_sugeridos] == [1, 2] and s.atingiu_alvo


def test_empate_de_custo_prefere_o_mais_recente():
    evs = [_ev(1, 500, dia=3), _ev(2, 500, dia=20)]
    s = sugerir_ajuste(evs, numerador=2000, total_cotas=100, alvo_cota=15)
    assert [e.protocolo for e in s.eventos_sugeridos] == [2]


def test_alvo_inalcancavel_avisa():
    s = sugerir_ajuste([_ev(1, 100)], numerador=2000, total_cotas=100, alvo_cota=1)
    assert s.precisa_ajuste and not s.atingiu_alvo and "acima do alvo" in s.mensagem


def test_alvo_invalido():
    with pytest.raises(ValueError):
        sugerir_ajuste([], numerador=1, total_cotas=1, alvo_cota=0)


client = TestClient(app)


def test_demo_postergar_e_devolver_com_auditoria():
    client.post("/avap/demo-fenauto")
    sug = client.post("/avap/09-2026/sugerir-ajuste", json={"alvo_cota": 7.0}).json()
    assert sug["precisa_ajuste"] and sug["atingiu_alvo"] and sug["cota_atual"] == 7.78
    prot = [e["protocolo"] for e in sug["eventos_sugeridos"]]

    r = client.post("/avap/09-2026/aplicar-ajuste",
                    json={"protocolos": prot, "justificativa": "estabilizar a cota", "alvo_cota": 7.0}).json()
    assert r["cota_atual"] <= 7.0 and r["cota_atual"] == pytest.approx(sug["cota_resultante"], abs=1e-4)
    assert {e["protocolo"] for e in r["postergados"]} == set(prot)
    reg = r["ajustes"][0]
    assert reg["acao"] == "postergar" and reg["cota_antes"] == 7.78 and reg["cota_depois"] == r["cota_atual"]
    assert any("Postergado no ajuste da cota: estabilizar a cota" in a for a in r["auditoria"])
    calc = client.get("/avap/09-2026/resultado").json()
    assert calc["aprovado"] and calc["valor_cota"] == r["cota_atual"]

    d = client.post("/avap/09-2026/devolver-ajuste",
                    json={"protocolos": prot, "justificativa": "voltar ao fechamento"}).json()
    assert d["cota_atual"] == 7.78 and d["postergados"] == [] and len(d["ajustes"]) == 2
    assert d["ajustes"][0]["acao"] == "devolver"


def test_demo_rejeita_protocolo_fora_do_rateio():
    client.post("/avap/demo-fenauto")
    r = client.post("/avap/09-2026/aplicar-ajuste", json={"protocolos": [1], "justificativa": "teste"})
    assert r.status_code == 400
    r = client.post("/avap/09-2026/devolver-ajuste", json={"protocolos": [1], "justificativa": "teste"})
    assert r.status_code == 400
