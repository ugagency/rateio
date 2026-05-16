"""N5 — conector + fluxo D+0..D+5 com lock (Foto de Fechamento)."""

from pathlib import Path

import pytest

from app.autotruck.cenarios import _frota
from app.autotruck.domain import EventoAT
from app.autotruck.fechamento import FechamentoError, FechamentoService
from app.autotruck.fontes import (
    FonteFechamentoXlsx,
    FonteMemoria,
    FonteRateio,
    FonteSGAHttp,
)

FIX = Path(__file__).parent / "fixtures" / "FECHAMENTO_referencia.xlsx"
pytestmark = pytest.mark.skipif(not FIX.exists(), reason="fixture ausente")

import random  # noqa: E402

_FROTA = _frota(random.Random(7), 200, 60, 20)


def _abrir(svc, mes="12/2025"):
    return svc.abrir(FonteFechamentoXlsx(str(FIX), mes_ano_ref=mes),
                     veiculos_base=_FROTA, base_cotas_leves=81_757,
                     base_cotas_motos=16_135)


def test_d0_foto_lacrada_reproduz_analitico_real() -> None:
    f = _abrir(FechamentoService())
    assert f.status == "ABERTO"
    assert len(f.hash_insumos) == 64                 # sha-256
    assert f.n_eventos >= 250
    assert f.resultado.consolidado.bruto_leves == pytest.approx(2_616_217.12, abs=0.01)
    assert f.resultado.consolidado.bruto_motos == pytest.approx(500_182.55, abs=0.01)
    assert f.resultado.consolidado.invariante_ok is True


def test_lacre_detecta_violacao_da_fonte() -> None:
    svc = FechamentoService()
    f = _abrir(svc)
    fonte = FonteFechamentoXlsx(str(FIX), mes_ano_ref="12/2025")
    assert svc.verificar_integridade(f.id, fonte)["intacto"] is True
    _, evs, _ = fonte.carregar()
    adulterada = FonteMemoria([], evs[:-3], "12/2025")
    chk = svc.verificar_integridade(f.id, adulterada)
    assert chk["intacto"] is False and "VIOLA" in chk["mensagem"].upper()


def test_maquina_de_estados_e_emissao() -> None:
    svc = FechamentoService()
    f = _abrir(svc)
    with pytest.raises(FechamentoError):       # não emite sem homologar
        svc.emitir(f.id)
    with pytest.raises(FechamentoError):       # homologação exige justificativa
        svc.homologar(f.id, "  ")
    svc.homologar(f.id, "Conferência diretoria — LC 213")
    assert svc.buscar(f.id).status == "HOMOLOGADO"
    svc.emitir(f.id)
    foto = svc.buscar(f.id)
    assert foto.status == "EMITIDO"
    assert len(svc.lote_boletos(f.id)) > 0
    acoes = [a.acao for a in foto.auditoria_fechamento]
    assert acoes == ["FOTO_FECHAMENTO_D0", "HOMOLOGACAO_D3", "EMISSAO_D5"]


def test_cota_usa_base_informada() -> None:
    svc = FechamentoService()
    f = _abrir(svc)
    c = svc.cota(f.id)
    assert c["LEVES"]["cotas_base"] == pytest.approx(81_757, abs=1)
    assert c["LEVES"]["valor_cota"] == pytest.approx(
        round(c["LEVES"]["custo_a_ratear"] / 81_757, 2), abs=0.01)


def test_idempotencia_abrir() -> None:
    svc = FechamentoService()
    _abrir(svc)
    with pytest.raises(FechamentoError):
        _abrir(svc)                            # já aberto
    f = svc.abrir(FonteFechamentoXlsx(str(FIX), mes_ano_ref="12/2025"),
                  veiculos_base=_FROTA, force=True)
    assert f.status == "ABERTO"


def test_conector_abstrato_funciona_com_qualquer_fonte() -> None:
    """O motor não muda de fonte: FonteMemoria implementa o mesmo Protocol."""
    veic = _FROTA
    evs = [EventoAT("E1", "P1", "X", "LEVES", "ASSOCIADO", "PARCIAL",
                    10_000, 1, 50_000, "2025-03-01")]
    fonte = FonteMemoria(veic, evs, "03/2025")
    assert isinstance(fonte, FonteRateio)
    f = FechamentoService().abrir(fonte, base_cotas_leves=1000)
    assert f.status == "ABERTO" and f.n_eventos == 1


def test_sga_http_contrato_presente_mas_pendente_de_endpoint() -> None:
    with pytest.raises(NotImplementedError):
        FonteSGAHttp("https://sga.exemplo", "tok", "12/2025").carregar()
