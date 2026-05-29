"""Verificação de paridade do exportador TypeScript (P2).

Gera BASE e RATEIO pelo escritor TS (app/src/lib/export/xlsx.ts), usando a MESMA
fixture do harness Python (fonte única em reference/harness.py), e valida os
arquivos contra o motor aprovado: detectar_tipo, roundtrip das cotas e
invariante zero. Prova que o caminho TS é equivalente ao Python de referência.

Requer Node e as dependências do app instaladas (esbuild via devDependency).
Expõe `rodar()` para a suíte (backend/tests/test_export_ts_parity.py).
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
APP = REPO / "admissao-verificada" / "app"
REF = REPO / "admissao-verificada" / "reference"
GEN = Path(__file__).resolve().parent / "gen.mjs"
XLSX_TS = APP / "src" / "lib" / "export" / "xlsx.ts"
ESBUILD = APP / "node_modules" / ".bin" / "esbuild"

sys.path.insert(0, str(REF))
sys.path.insert(0, str(REPO / "backend"))


def disponivel() -> tuple[bool, str]:
    if shutil.which("node") is None:
        return False, "node ausente"
    if not ESBUILD.exists():
        return False, "esbuild ausente (rode npm install no app)"
    return True, ""


def rodar() -> dict:
    from harness import fixture  # fonte única da fixture

    from app.autotruck.engine import calcular_rateio_at
    from app.autotruck.ingestao_partes import compor, detectar_tipo, ler_base

    cotas, eventos = fixture()
    tmp = Path(tempfile.mkdtemp(prefix="p2_"))
    bundle = tmp / "xlsx.mjs"
    fixture_json = tmp / "fixture.json"
    fixture_json.write_text(json.dumps({"cotas": cotas, "eventos": eventos}), "utf8")

    # 1) bundle do exportador TS (resolve alias @/ e embute exceljs; banner
    # injeta createRequire para o exceljs CJS funcionar em ESM).
    subprocess.run(
        [str(ESBUILD), str(XLSX_TS), "--bundle", "--format=esm", "--platform=node",
         f"--alias:@={APP / 'src'}",
         "--banner:js=import { createRequire as __cr } from 'module'; const require = __cr(import.meta.url);",
         f"--outfile={bundle}"],
        check=True, capture_output=True, cwd=str(APP),
    )

    # 2) gera BASE e RATEIO pelo caminho TS
    subprocess.run(["node", str(GEN), str(bundle), str(fixture_json), str(tmp)],
                   check=True, capture_output=True)

    base = str(tmp / "BASE_202606.xlsx")
    rateio = str(tmp / "RATEIO_202606.xlsx")

    # 3) valida contra o motor
    tb, tr = detectar_tipo(base), detectar_tipo(rateio)
    bc = ler_base(base)
    roundtrip_ok = all(bc.cotas_baixadas.get(s, 0) == cotas[s]["baixadas"]
                       for s in ("LEVES", "MOTOS", "PESADOS"))
    veic, ev, _, _, _ = compor(base, rateio)
    c = calcular_rateio_at(mes_ano_ref="06/2026", veiculos=veic, eventos=ev).consolidado
    return {
        "tipo_base": tb, "tipo_rateio": tr, "roundtrip_ok": roundtrip_ok,
        "eventos_lidos": len(ev), "dif": c.diferenca_total, "invariante_ok": c.invariante_ok,
    }


if __name__ == "__main__":
    ok, motivo = disponivel()
    if not ok:
        print("pulado:", motivo)
        raise SystemExit(0)
    r = rodar()
    print(r)
    bom = (r["tipo_base"] == "BASE" and r["tipo_rateio"] == "RATEIO"
           and r["roundtrip_ok"] and r["invariante_ok"])
    print("PARIDADE TS OK" if bom else "PARIDADE TS FALHOU")
    raise SystemExit(0 if bom else 1)
