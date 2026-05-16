"""Fecha o mês AutoTruck ponta a ponta — D+0 → D+5 — a partir do export
real do SGA (FECHAMENTO.xlsx). Demonstra o conector + lock + emissão.

Uso: cd backend && .venv/bin/python -m tools.fechar_mes \
        [FECHAMENTO.xlsx] [--leves N] [--motos N]

Gera: simulacoes/LOTE_BOLETOS_<id>.xlsx  e
       docs/evidencias/FECHAMENTO_<id>_trilha.txt
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from app.autotruck.cenarios import _frota  # frota representativa determinística
from app.autotruck.domain import VeiculoAT
from app.autotruck.fechamento import FechamentoService
from app.autotruck.fontes import FonteFechamentoXlsx, FonteMemoria

H = Font(bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor="1F4E79")
MONEY = "#,##0.00"


def _frota_repr():
    import random
    return [VeiculoAT(**v) if isinstance(v, dict) else v
            for v in _frota(random.Random(7), 520, 170, 60)]


def _xlsx_lote(foto, svc, destino: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "LOTE_BOLETOS"
    ws["A1"] = f"LOTE DE BOLETOS — {foto.id} ({foto.mes_ano_ref}) — status {foto.status}"
    ws["A1"].font = Font(bold=True, size=13)
    cols = ["id_veiculo", "placa", "segmento", "fipe", "qtd_cotas",
            "cota_especial", "rateio", "pote_terceiros", "pote_caminhao",
            "servicos", "TOTAL"]
    for i, c in enumerate(cols, 1):
        x = ws.cell(3, i, c)
        x.font = H
        x.fill = HF
    for j, b in enumerate(svc.lote_boletos(foto.id), start=4):
        for k, val in enumerate([b.id_veiculo, b.placa, b.segmento, b.valor_fipe,
                                 b.qtd_cotas, "SIM" if b.cota_especial else "",
                                 b.custo_rateio, b.custo_pote_terceiros,
                                 b.custo_pote_caminhao, b.servicos_adicionais,
                                 b.valor_total_boleto], 1):
            c = ws.cell(j, k, val)
            if isinstance(val, float):
                c.number_format = MONEY
    ws.freeze_panes = "A4"
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)


def _trilha(foto, destino: Path):
    linhas = [
        f"TRILHA DE FECHAMENTO — {foto.id} ({foto.mes_ano_ref})",
        f"Gerado em {datetime.now(timezone.utc).isoformat()} (UTC)",
        f"Origem: {foto.origem}",
        f"Hash dos insumos (lacre D+0): {foto.hash_insumos}",
        f"Status final: {foto.status}",
        "",
        "Audit trail (log imutável — LC 213 / D&O):",
    ]
    for a in foto.auditoria_fechamento:
        linhas.append(f"  [{a.acao}] {a.timestamp}  {a.justificativa}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas), encoding="utf-8")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = args[0] if args else \
        "/root/projetos/Mut/backend/tests/fixtures/FECHAMENTO_referencia.xlsx"
    leves = motos = 0.0
    for a in sys.argv:
        if a.startswith("--leves"):
            leves = float(a.split("=")[-1]) if "=" in a else 81757.0
        if a.startswith("--motos"):
            motos = float(a.split("=")[-1]) if "=" in a else 16135.0
    leves = leves or 81757.0
    motos = motos or 16135.0

    svc = FechamentoService()
    fonte = FonteFechamentoXlsx(src, mes_ano_ref="12/2025")

    print(f"\n┌─ FECHAMENTO AutoTruck — {src.split('/')[-1]}")
    f = svc.abrir(fonte, veiculos_base=_frota_repr(),
                  base_cotas_leves=leves, base_cotas_motos=motos)
    co = f.resultado.consolidado
    cota = svc.cota(f.id)
    print(f"│ D+0  Foto lacrada  id={f.id}  hash={f.hash_insumos[:16]}…")
    print(f"│      {f.n_eventos} eventos reais · invariante={'OK' if co.invariante_ok else 'FALHA'}")
    print(f"│      RATEIO LEVES={co.bruto_leves:,.2f}  MOTOS={co.bruto_motos:,.2f}  (espelha o ANALITICO real)")
    print(f"│      Cota LEVES=R$ {cota['LEVES']['valor_cota']}  MOTOS=R$ {cota['MOTOS']['valor_cota']}  (base informada)")

    itg = svc.verificar_integridade(f.id, fonte)
    print(f"│ ——   Integridade do lacre: {'ÍNTEGRO ✅' if itg['intacto'] else 'VIOLADO ❌'}")
    itg2 = svc.verificar_integridade(
        f.id, FonteMemoria([], fonte.carregar()[1][:-1], "12/2025"))
    print(f"│      Detecção de violação (fonte alterada): "
          f"{'detectou ✅' if not itg2['intacto'] else 'FALHOU ❌'}")

    svc.homologar(f.id, "Homologado pela diretoria AutoTruck — conferência D+1–D+3 (LC 213).")
    print(f"│ D+3  Homologado")
    svc.emitir(f.id)
    lote = svc.lote_boletos(f.id)
    print(f"│ D+5  Emitido — lote de {len(lote)} boletos")

    out_lote = Path("/root/projetos/Mut/simulacoes") / f"LOTE_BOLETOS_{f.id}.xlsx"
    out_trilha = Path("/root/projetos/Mut/docs/evidencias") / f"FECHAMENTO_{f.id}_trilha.txt"
    _xlsx_lote(f, svc, out_lote)
    _trilha(f, out_trilha)
    print(f"└─ artefatos: {out_lote}")
    print(f"             {out_trilha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
