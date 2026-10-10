"""Testes da fase 0 do motor AVAP (parser de cota e leitores com conferência de rodapé).

Os testes sobre arquivos reais ficam em AVAP/ (gitignored) e são pulados se ausentes.
"""

from datetime import datetime
from pathlib import Path

import openpyxl
import pytest

from app.avap.domain import EstadoRateio
from app.avap.ingestao import (
    ConferenciaRodapeError,
    LayoutDesconhecidoError,
    estado_rateio,
    ler_eventos,
    ler_veiculos,
    parse_cota,
)

AVAP = Path(__file__).resolve().parents[2] / "AVAP"


@pytest.mark.parametrize("rotulo,peso,sufixo", [
    ("COTA 6,0 - (25.000,01 A 30.000,00)(6.00)", 6.0, None),
    ("COTA 6,0 - (25.000,01 A 30.000,00) - VP (6.00)", 6.0, "VP"),
    ("COTA 8,0 (35.000,01 A 40.000,00) - VP (8.00)", 8.0, "VP"),
    ("COTA 34,0 (165.000,01 A 170.000,00) (34.00)", 34.0, None),
    ("COTA 80.00 - (R$ 210.000,00) - TP (80.00)", 80.0, "TP"),
    ("COTA 0.00 (0.00)", 0.0, None),
    ("COTA 0,0 - PRODUTOS AVULSOS (0.00)", 0.0, None),
    ("COTA 5,0 - (20.000,01 A 25.000,00) - DP (5,00)", 5.0, "DP"),
])
def test_parse_cota(rotulo, peso, sufixo):
    assert parse_cota(rotulo) == (peso, sufixo)


@pytest.mark.parametrize("ruim", [None, 12, "COTA 6,0 sem peso", ""])
def test_parse_cota_invalida(ruim):
    with pytest.raises(ValueError):
        parse_cota(ruim)


def test_estados_valor_rateado():
    assert estado_rateio(None, 100.0) == (EstadoRateio.NAO_RATEADO, None)
    assert estado_rateio("", 100.0)[0] == EstadoRateio.NAO_RATEADO
    assert estado_rateio("0.00", 100.0) == (EstadoRateio.NA_FILA, 0.0)
    assert estado_rateio(100.0, 100.0)[0] == EstadoRateio.RATEADO
    assert estado_rateio("55.00", 100.0)[0] == EstadoRateio.RATEADO_DIVERGENTE


def _xlsx(tmp_path, linhas, nome="x.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in linhas:
        ws.append(r)
    p = tmp_path / nome
    wb.save(p)
    return p


CAB_VEIC = ["Placa", "Cota", "Categoria", "Tipo Veículo", "Valor FIPE Veiculo",
            "Situação Veículo", "Situação Associado", "Matrícula Associado"]


def _veic(tmp_path, total_cotas="7,00", n=2):
    return _xlsx(tmp_path, [
        CAB_VEIC,
        ["AAA1A11", "COTA 4,0 - (15.000,01 A 20.000,00) (4.00)", "PASSEIO", "AUTOMOVEL", 19907, "ATIVO", "ATIVO", 1],
        [None, "COTA 3,0 - (10.000,01 A 15.000,00) - VP (3.00)", "PASSEIO", "AUTOMOVEL", 0, "INADIMPLENTE", "ATIVO", 2],
        [None] * 8,
        ["Resumo"] + [None] * 7,
        ["Total de veículos encontrados:", n] + [None] * 6,
        ["Total de cotas encontradas:", total_cotas] + [None] * 6,
    ])


def test_veiculos_confere(tmp_path):
    r = ler_veiculos(_veic(tmp_path, "7.00"))
    assert len(r.veiculos) == 2 and r.conferencia.aprovada
    assert r.veiculos[1].placa is None and r.veiculos[1].valor_fipe is None
    assert r.veiculos[1].sufixo_cota == "VP"


def test_veiculos_rodape_reprova(tmp_path):
    p = _veic(tmp_path, "8.00")
    with pytest.raises(ConferenciaRodapeError):
        ler_veiculos(p)
    r = ler_veiculos(p, estrito=False)
    assert [d.campo for d in r.conferencia.divergencias] == ["cotas"]


CAB_EV = ["Protocolo", "Situacao", "Data Finalizacao", "Valor Reparo", "Valor Participacao",
          "Valor CustoEvento", "Previsao Valor Reparo", "Motivo", "Valor Rateado",
          "Data Cadastro Evento", "Cota", "Categoria", "Modelo", "Tipo Veiculo", "Tipo Evento"]
COTA = "COTA 4,0 - (15.000,01 A 20.000,00) (4.00)"


def _ev(prot, custo, rateado):
    return [prot, "FINALIZADO", datetime(2026, 9, 1), custo + 100, "100.00", f"{custo:.2f}", 0,
            "COLISAO", rateado, datetime(2026, 8, 1), COTA, "PASSEIO", "UNO", "AUTOMOVEL", "Evento Associado"]


def _eventos(tmp_path, custo_rodape=300.0, extra=None):
    linhas = [["HINOVA"], CAB_EV, _ev(2026000001, 100.0, None), _ev(2026000002, 200.0, "0.00")]
    linhas += extra or []
    linhas += [
        [None] * 15,
        ["Total de eventos encontrados: %d" % (2 + len(extra or []))] + [None] * 14,
        ["Valor Total Reparo", 500.0 + 200 * len(extra or [])] + [None] * 13,
        ["Valor Total Participacao", 200.0 + 100 * len(extra or [])] + [None] * 13,
        ["Valor Total Custo Evento", custo_rodape] + [None] * 13,
    ]
    return _xlsx(tmp_path, linhas)


def test_eventos_confere_e_estados(tmp_path):
    r = ler_eventos(_eventos(tmp_path))
    assert r.layout == "30/09" and r.conferencia.aprovada and r.protocolos_duplicados == []
    assert [e.estado_rateio for e in r.eventos] == [EstadoRateio.NAO_RATEADO, EstadoRateio.NA_FILA]
    assert r.eventos[0].peso_cota == 4.0 and r.eventos[0].placa is None


def test_eventos_rodape_reprova(tmp_path):
    p = _eventos(tmp_path, custo_rodape=999.0)
    with pytest.raises(ConferenciaRodapeError) as ex:
        ler_eventos(p)
    assert [d.campo for d in ex.value.conferencia.divergencias] == ["custo"]


def test_eventos_duplicata_reportada(tmp_path):
    r = ler_eventos(_eventos(tmp_path, custo_rodape=400.0, extra=[_ev(2026000001, 100.0, None)]))
    assert r.protocolos_duplicados == [2026000001]


def test_eventos_layout_desconhecido(tmp_path):
    p = _xlsx(tmp_path, [["Foo", "Bar"], [1, 2]])
    with pytest.raises(LayoutDesconhecidoError):
        ler_eventos(p)


# ───────── arquivos reais (pulados se AVAP/ não existir) ─────────

real = pytest.mark.skipif(not AVAP.exists(), reason="AVAP/ (dados reais) ausente")


@real
def test_real_veiculos():
    r = ler_veiculos(AVAP / "Cotas_ativasAVAP_09_26.xlsx")
    assert len(r.veiculos) == 39_242
    assert sum(v.peso_cota for v in r.veiculos) == pytest.approx(361_530.0)
    assert r.conferencia.aprovada


@real
@pytest.mark.parametrize("arq,layout,n", [("foto28-09.xlsx", "28/09", 3095), ("foto30-09.xlsx", "30/09", 3104)])
def test_real_eventos(arq, layout, n):
    r = ler_eventos(AVAP / arq)
    assert r.layout == layout and len(r.eventos) == n and r.conferencia.aprovada
    assert r.protocolos_duplicados == []
    # só evento de terceiro pode vir sem cota (17 casos nas duas fotos)
    assert all(e.peso_cota is not None for e in r.eventos if e.tipo_evento == "Evento Associado")
    assert sum(e.peso_cota is None for e in r.eventos) == 17
