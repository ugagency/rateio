"""Reconciliação de aceite da AVAP: fechamento real (planilha de rateio) contra o motor.

Uso:
  cd backend && .venv/bin/python -m tools.reconciliar_avap <rateio.xlsx> --aba Rateio_setembro \\
      --eventos <foto SGA pós-fechamento> --veiculos <base de cotas> \\
      [--fila <foto SGA pré-fechamento>] [--valor-cota 5.00]

Aprovado (código 0) quando nenhuma linha está em FALHA. Sem --valor-cota, o valor por cota sai
como informativo (PENDENTE) para cada critério de elegibilidade. Com --valor-cota, os critérios
que não reproduzem o valor aparecem em FALHA. O D2 já está decidido (VEICULO, ver
docs/REGRAS_RATEIO_AVAP.md); os outros critérios ficam só como comparação.
Obs.: com --valor-cota, os critérios que não batem reprovam por construção; use a linha do
critério correto como o aceite.
"""

import argparse
import sys
from pathlib import Path

from app.avap.historico import ler_historico
from app.avap.ingestao import ler_eventos, ler_veiculos
from app.avap.reconciliacao import reconciliar


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rateio")
    ap.add_argument("--aba", required=True)
    ap.add_argument("--eventos", required=True)
    ap.add_argument("--veiculos", required=True)
    ap.add_argument("--fila")
    ap.add_argument("--valor-cota", type=float)
    a = ap.parse_args(argv)

    hist = ler_historico(a.rateio)
    if a.aba not in hist:
        print(f"Aba '{a.aba}' não existe. Abas: {', '.join(hist)}", file=sys.stderr)
        return 2
    fila = ler_eventos(a.fila).eventos if a.fila else None
    rec = reconciliar(hist[a.aba], ler_eventos(a.eventos).eventos, ler_veiculos(a.veiculos).veiculos,
                      fila, a.valor_cota)

    print(f"\nReconciliação AVAP: {Path(a.rateio).name} / {a.aba}\n")
    grupo = None
    for ln in rec.linhas:
        if ln.grupo != grupo:
            grupo = ln.grupo
            print(f"[{grupo}]")
        dec = "-" if ln.declarado is None else f"{ln.declarado:,.2f}"
        cal = "-" if ln.calculado is None else f"{ln.calculado:,.4f}".rstrip("0").rstrip(".")
        print(f"  {ln.status:8} {ln.item}: declarado {dec} | motor {cal}" + (f"  ({ln.obs})" if ln.obs else ""))
    print("\nRESULTADO:", "APROVADO" if rec.aprovado else "REPROVADO")
    return 0 if rec.aprovado else 1


if __name__ == "__main__":
    sys.exit(main())
