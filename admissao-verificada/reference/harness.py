"""Harness de reconciliação (SPEC-008): prova que os arquivos exportados pelo
app servem ao motor aprovado, com um caso conhecido (marco M1).

Fluxo: fixture -> exportar BASE/RATEIO -> detectar_tipo -> compor -> motor ->
invariante_ok. Não altera o motor; consome-o como caixa-preta (fronteira =
arquivo). Roda com o venv do backend e PYTHONPATH apontando para backend/.
"""

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.autotruck.engine import calcular_rateio_at          # noqa: E402
from app.autotruck.ingestao_partes import compor, detectar_tipo, ler_base  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exportador import exportar_base, exportar_rateio        # noqa: E402

MES = "06/2026"


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


def main() -> int:
    cotas, eventos = fixture()
    tmp = Path(tempfile.mkdtemp(prefix="harness_"))
    base_path = str(tmp / "BASE_202606.xlsx")
    rateio_path = str(tmp / "RATEIO_202606.xlsx")

    exportar_base(base_path, cotas)
    exportar_rateio(rateio_path, eventos)

    falhas = []

    # 1) detectar_tipo (SPEC-000 AC-1/AC-2)
    tb, tr = detectar_tipo(base_path), detectar_tipo(rateio_path)
    print(f"detectar_tipo BASE   = {tb}")
    print(f"detectar_tipo RATEIO = {tr}")
    if tb != "BASE":
        falhas.append(f"BASE detectada como {tb}")
    if tr != "RATEIO":
        falhas.append(f"RATEIO detectado como {tr}")

    # 2) roundtrip da BASE: ler_base devolve as cotas baixadas que escrevemos
    bc = ler_base(base_path)
    for seg in ("LEVES", "MOTOS", "PESADOS"):
        esperado = cotas[seg]["baixadas"]
        lido = bc.cotas_baixadas.get(seg, 0)
        print(f"cotas BAIXADAS {seg}: escrito={esperado} lido={lido}")
        if lido != esperado:
            falhas.append(f"roundtrip BASE {seg}: escrito {esperado}, lido {lido}")

    # 3) compor + motor + invariante (SPEC-000 AC-3, ADR-002 C6)
    veiculos, evts, _, _, resumo = compor(base_path, rateio_path)
    print(f"veículos compostos={len(veiculos)} eventos lidos={len(evts)}")
    if resumo.alertas:
        print("alertas de coerência:", resumo.alertas)
    res = calcular_rateio_at(mes_ano_ref=MES, veiculos=veiculos, eventos=evts)
    c = res.consolidado
    print(f"cota LEVES=R$ {c.cota_leves:.2f}  cota MOTOS=R$ {c.cota_motos:.2f}")
    print(f"Δ invariante=R$ {c.diferenca_total:.2f}  invariante_ok={c.invariante_ok}")
    if len(evts) != len(eventos):
        falhas.append(f"eventos: exportados {len(eventos)}, lidos {len(evts)}")
    if not c.invariante_ok:
        falhas.append(f"invariante não fechou: Δ={c.diferenca_total}")

    print("-" * 60)
    if falhas:
        print("HARNESS REPROVADO:")
        for f in falhas:
            print("  -", f)
        return 1
    print("HARNESS APROVADO: arquivos servem ao motor, invariante zero.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
