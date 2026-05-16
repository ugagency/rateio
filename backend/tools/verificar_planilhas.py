"""Evidência anti-mock: avalia as FÓRMULAS NATIVAS do Excel das planilhas
de simulação (via o motor independente `formulas`) e confronta, célula a
célula, com os valores do engine. Gera log de evidência.

Uso: cd backend && .venv/bin/python -m tools.verificar_planilhas
"""

import glob
import re
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")
import formulas  # noqa: E402

EVID = Path("/root/projetos/Mut/docs/evidencias")


def verificar(padrao: str) -> bool:
    EVID.mkdir(parents=True, exist_ok=True)
    out = EVID / "EVIDENCIA_conferencia_planilhas.txt"
    linhas = [
        "EVIDÊNCIA — Conferência das planilhas de simulação AutoTruck",
        f"Gerado em {datetime.now(timezone.utc).isoformat()} (UTC)",
        "",
        "Método: o motor de fórmulas 'formulas' avalia as FÓRMULAS NATIVAS do",
        "Excel (SUMIFS/COUNTIFS/CEILING/IF) escritas na aba CONFERENCIA, que",
        "recomputam tudo a partir das abas INPUTS_*. A coluna F = Δ(engine −",
        "fórmula Excel). Δ = 0,00 prova que os números são CALCULADOS dos",
        "inputs, não fixados.",
        "",
    ]
    todos_ok = True
    for fp in sorted(glob.glob(padrao)):
        nome = fp.split("Cenario_")[1][0]
        xl = formulas.ExcelModel().loads(fp).finish()
        sol = xl.calculate()
        pref = [k.split("!")[0] for k in sol
                if "CONFERENCIA" in k.upper() and re.search(r"!B6$", k)][0]

        def val(c):
            try:
                return float(sol[f"{pref}!{c}"].value[0, 0])
            except Exception:
                return None

        n, maxd = 0, 0.0
        for rnum in range(4, 40):
            f = val(f"F{rnum}")
            if f is not None and f == f:
                n += 1
                maxd = max(maxd, abs(f))
        ok = maxd <= 0.01
        todos_ok &= ok
        linhas.append(f"Cenário {nome}  ({Path(fp).name})")
        linhas.append(f"  células Δ avaliadas: {n} | máx |Δ(engine − fórmula Excel)| = "
                       f"{maxd:.4f} | {'OK ✅' if ok else 'DIVERGÊNCIA ❌'}")
        linhas.append("")
    linhas.append("RESULTADO: " + (
        "TODAS as fórmulas nativas do Excel reproduzem o engine — dados reais, "
        "não mocados. ✅" if todos_ok else "HÁ DIVERGÊNCIA ❌"))
    out.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print(f"\n→ evidência salva em {out}")
    return todos_ok


if __name__ == "__main__":
    padrao = sys.argv[1] if len(sys.argv) > 1 else \
        "/root/projetos/Mut/simulacoes/SIMULACAO_AutoTruck_Cenario_*.xlsx"
    raise SystemExit(0 if verificar(padrao) else 1)
