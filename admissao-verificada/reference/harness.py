"""Harness de reconciliação (SPEC-008): prova que os arquivos exportados pelo
app servem ao motor aprovado, com um caso conhecido (marco M1).

Fluxo: fixture -> exportar BASE/RATEIO -> detectar_tipo -> compor -> motor ->
invariante_ok. Não altera o motor; consome-o como caixa-preta (fronteira =
arquivo). Expõe `rodar_harness()` para a suíte de testes (SPEC-008 secao 7).
"""

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.autotruck.engine import calcular_rateio_at          # noqa: E402
from app.autotruck.ingestao_partes import compor, detectar_tipo, ler_base  # noqa: E402

from exportador import exportar_base, exportar_rateio        # noqa: E402

MES = "06/2026"
SEGS = ("LEVES", "MOTOS", "PESADOS")


def fixture():
    """Caso conhecido, determinístico. 1 veículo = 1 cota (synth do motor)."""
    cotas = {
        "LEVES":   {"baixadas": 120, "abertas": 8, "canceladas": 2},
        "MOTOS":   {"baixadas": 45,  "abertas": 3, "canceladas": 1},
        "PESADOS": {"baixadas": 10,  "abertas": 1, "canceladas": 0},
    }
    eventos = [
        dict(segmento="LEVES", envolvimento="ASSOCIADO", tipo="INTEGRAL",
             protocolo="1001", motivo="Colisão", placa="ABC1D23",
             data="05/06/2026", valor=30000.0),
        dict(segmento="LEVES", envolvimento="ASSOCIADO", tipo="PARCIAL",
             protocolo="1002", motivo="Reparo", placa="ABC1D24",
             data="08/06/2026", valor=8000.0),
        dict(segmento="LEVES", envolvimento="TERCEIRO", tipo="PARCIAL",
             protocolo="1003", motivo="Terceiro", placa="ABC1D25",
             data="10/06/2026", valor=5000.0),
        dict(segmento="MOTOS", envolvimento="ASSOCIADO", tipo="INTEGRAL",
             protocolo="2001", motivo="Furto", placa="XYZ9K88",
             data="06/06/2026", valor=9000.0),
        dict(segmento="MOTOS", envolvimento="ASSOCIADO", tipo="PARCIAL",
             protocolo="2002", motivo="Reparo", placa="XYZ9K89",
             data="12/06/2026", valor=2000.0),
        dict(segmento="PESADOS", envolvimento="TERCEIRO", tipo="PARCIAL",
             protocolo="3001", motivo="Terceiro", placa="CAM1H10",
             data="07/06/2026", valor=4000.0),
    ]
    return cotas, eventos


def rodar_harness(cotas=None, eventos=None) -> dict:
    """Exporta a competência, reconcilia contra o motor e devolve o veredito
    estruturado. Não imprime nem encerra o processo."""
    if cotas is None or eventos is None:
        cotas, eventos = fixture()
    tmp = Path(tempfile.mkdtemp(prefix="harness_"))
    base_path = str(tmp / "BASE_202606.xlsx")
    rateio_path = str(tmp / "RATEIO_202606.xlsx")

    exportar_base(base_path, cotas)
    exportar_rateio(rateio_path, eventos)

    tb, tr = detectar_tipo(base_path), detectar_tipo(rateio_path)

    bc = ler_base(base_path)
    roundtrip = {seg: (cotas[seg]["baixadas"], bc.cotas_baixadas.get(seg, 0)) for seg in SEGS}
    roundtrip_ok = all(esc == lido for esc, lido in roundtrip.values())

    veiculos, evts, _, _, resumo = compor(base_path, rateio_path)
    res = calcular_rateio_at(mes_ano_ref=MES, veiculos=veiculos, eventos=evts)
    c = res.consolidado

    return {
        "tipo_base": tb,
        "tipo_rateio": tr,
        "roundtrip": roundtrip,
        "roundtrip_ok": roundtrip_ok,
        "eventos_exportados": len([e for e in eventos if e["valor"] > 0]),
        "eventos_lidos": len(evts),
        "cota_leves": c.cota_leves,
        "cota_motos": c.cota_motos,
        "dif": c.diferenca_total,
        "invariante_ok": c.invariante_ok,
        "alertas": resumo.alertas,
    }


def main() -> int:
    r = rodar_harness()
    print(f"detectar_tipo BASE   = {r['tipo_base']}")
    print(f"detectar_tipo RATEIO = {r['tipo_rateio']}")
    for seg, (esc, lido) in r["roundtrip"].items():
        print(f"cotas BAIXADAS {seg}: escrito={esc} lido={lido}")
    print(f"eventos exportados={r['eventos_exportados']} lidos={r['eventos_lidos']}")
    if r["alertas"]:
        print("alertas:", r["alertas"])
    print(f"cota LEVES=R$ {r['cota_leves']:.2f}  cota MOTOS=R$ {r['cota_motos']:.2f}")
    print(f"Δ invariante=R$ {r['dif']:.2f}  invariante_ok={r['invariante_ok']}")
    print("-" * 60)
    ok = (r["tipo_base"] == "BASE" and r["tipo_rateio"] == "RATEIO"
          and r["roundtrip_ok"] and r["invariante_ok"]
          and r["eventos_lidos"] == r["eventos_exportados"])
    print("HARNESS APROVADO" if ok else "HARNESS REPROVADO")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
