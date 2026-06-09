"""Gera o kit de planilhas para a demonstração do Rateio ELLO em reunião.

Isolado: não toca na publicação atual nem no AutoTruck. Apenas produz xlsx
de entrada (contrato oficial do ELLO) numa pasta de demonstração e calcula
os números esperados rodando o MOTOR REAL (app.core.engine), para a folha
de apoio bater com o que a tela vai mostrar.

Rodar: backend/.venv/bin/python3 demos/reuniao_ello/gerar_kit_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, "/root/projetos/Mut/backend")

import openpyxl

from app.core.domain import Evento, ServicoFixo, Veiculo
from app.core.engine import calcular_rateio
from app.core.ingestao_xlsx import ler_eventos, ler_servicos, ler_veiculos

PASTA = Path("/root/projetos/Mut/demos/reuniao_ello")
MES_REF = "05/2026"  # default da tela (mês anterior); aqui é apenas o carimbo

# ---------------------------------------------------------------- planilhas --

def _escrever(path: Path, headers: list[str], linhas: list[list]) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "dados"
    ws.append(headers)
    for ln in linhas:
        ws.append(ln)
    wb.save(path)


# ---- VEÍCULOS: pool desenhado para um Alvo de números redondos -------------
# ROUBO_FURTO x60, MOTO_FIP x20, VENTURE_1 x15, VENTURE_2 x5 = 100 veículos,
# 1 cota cada. Reduzido remove 10 ROUBO_FURTO (VEI-051..060).
H_VEIC = ["ID_Veiculo", "Status_Ativo", "Data_Quebra", "Tipo_Categoria_Risco",
          "Qtd_Cotas", "Tipo_Pagamento", "Is_Funcionario"]


def _linha_veic(i: int, categoria: str) -> list:
    return [f"VEI-{i:03d}", True, None, categoria, 1, "MENSAL", False]


def veiculos_linhas(reduzido: bool) -> list[list]:
    linhas = []
    # ROUBO_FURTO 001..060 (no reduzido, 001..050)
    fim_rf = 50 if reduzido else 60
    for i in range(1, fim_rf + 1):
        linhas.append(_linha_veic(i, "ROUBO_FURTO"))
    # MOTO_FIP 061..080
    for i in range(61, 81):
        linhas.append(_linha_veic(i, "MOTO_FIP"))
    # VENTURE_1 081..095
    for i in range(81, 96):
        linhas.append(_linha_veic(i, "VENTURE_1"))
    # VENTURE_2 096..100
    for i in range(96, 101):
        linhas.append(_linha_veic(i, "VENTURE_2"))
    return linhas


# ---- EVENTOS: "cobre" sobra-cobre o alvo; "falta" deixa buraco -------------
H_EVT = ["ID_Evento", "Data_Ocorrencia_Evento", "Valor_Total_Evento", "Valor_Saldo_Pendente"]

EVENTOS_COBRE = [
    ["EV-001", "2026-05-08", 1500.0, 1500.0],
    ["EV-002", "2026-05-15", 800.0, 800.0],
]
EVENTOS_FALTA = [
    ["EV-001", "2026-05-08", 1500.0, 1500.0],
]

# ---- SERVIÇOS fixos: taxa 30 + assistência 20 = R$50 por veículo -----------
H_SVC = ["ID_Veiculo", "Taxa_Administrativa", "Valor_Assistencia_24h", "Valor_Outros_Produtos"]


def servicos_linhas() -> list[list]:
    return [[f"VEI-{i:03d}", 30.0, 20.0, 0.0] for i in range(1, 101)]


# --------------------------------------------------------------- gerar tudo --

def gerar() -> dict[str, Path]:
    PASTA.mkdir(parents=True, exist_ok=True)
    arquivos = {
        "veiculos_completo": PASTA / "veiculos_completo.xlsx",
        "veiculos_reduzido": PASTA / "veiculos_reduzido.xlsx",
        "eventos_cobre": PASTA / "eventos_cobre.xlsx",
        "eventos_falta": PASTA / "eventos_falta.xlsx",
        "servicos": PASTA / "servicos.xlsx",
    }
    _escrever(arquivos["veiculos_completo"], H_VEIC, veiculos_linhas(reduzido=False))
    _escrever(arquivos["veiculos_reduzido"], H_VEIC, veiculos_linhas(reduzido=True))
    _escrever(arquivos["eventos_cobre"], H_EVT, EVENTOS_COBRE)
    _escrever(arquivos["eventos_falta"], H_EVT, EVENTOS_FALTA)
    _escrever(arquivos["servicos"], H_SVC, servicos_linhas())
    return arquivos


# ------------------------------------------ calcular esperados via motor real --

def rodar(veic: Path, evt: Path, svc: Path):
    vs = ler_veiculos(str(veic))
    es = ler_eventos(str(evt))
    ss = ler_servicos(str(svc))
    return calcular_rateio(mes_ano_ref=MES_REF, veiculos=vs, eventos=es, servicos=ss), len(vs), len(es)


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(v)


def linha_resultado(rotulo, res, nveic, nevt) -> list[str]:
    c = res.consolidado
    return [
        f"## {rotulo}",
        "",
        f"- Linhas lidas: {nveic} veículos, {nevt} eventos",
        f"- Veículos elegíveis: {c.total_veiculos_elegiveis}",
        f"- Cotas apuradas: {fmt(c.total_cotas_apuradas)}",
        f"- ALVO DO MÊS: R$ {fmt(c.valor_alvo_total)}",
        f"  - P1 Roubo/Furto: R$ {fmt(c.valor_p1_roubo_furto)}",
        f"  - P2 Moto FIP: R$ {fmt(c.valor_p2_moto_fip)}",
        f"  - P3 Venture 1: R$ {fmt(c.valor_p3_venture_1)}",
        f"  - P4 Venture 2: R$ {fmt(c.valor_p4_venture_2)}",
        f"- Eventos alocados: {c.eventos_alocados} ({c.eventos_liquidados} liquidados, {c.eventos_parciais} parciais)",
        f"- Saldo p/ próximo mês: R$ {fmt(c.saldo_para_proximo_mes)}",
        f"- Invariante (Δ alvo vs alocado): R$ {fmt(c.diferenca_alvo_vs_alocado)}",
        "",
    ]


def main() -> None:
    a = gerar()
    r_1a, nv_c, ne_c = rodar(a["veiculos_completo"], a["eventos_cobre"], a["servicos"])
    r_1b, nv_r, _ = rodar(a["veiculos_reduzido"], a["eventos_cobre"], a["servicos"])
    r_2b, _, ne_f = rodar(a["veiculos_completo"], a["eventos_falta"], a["servicos"])

    out = []
    out += ["# Folha de apoio — Demonstração Rateio ELLO", "",
            f"Mês de referência usado: {MES_REF} (default da tela). O carimbo de mês",
            "é cosmético; os valores vêm dos arquivos. Números abaixo calculados pelo",
            "motor real (app.core.engine), idênticos ao que a tela mostra.", "",
            "Todos os veículos têm 1 cota. Cota acumulada por categoria: ROUBO_FURTO",
            "R$14, MOTO_FIP R$18, VENTURE_1 R$36, VENTURE_2 R$54.", "",
            "---", "",
            "# DEMONSTRAÇÃO 1 — mover o ALVO (troca o arquivo de VEÍCULOS)", "",
            "Mantenha fixos: eventos_cobre.xlsx e servicos.xlsx. Troque só o veículos.", ""]
    out += linha_resultado("1A) veiculos_completo (100 veículos)", r_1a, nv_c, ne_c)
    out += linha_resultado("1B) veiculos_reduzido (removidos 10 Roubo/Furto)", r_1b, nv_r, ne_c)
    out += ["Frase para a reunião: \"Removi 10 veículos Roubo/Furto. Cada um paga R$14",
            "no P1, então o Alvo deve cair R$140: de R$ {} para R$ {}.\"".format(
                fmt(r_1a.consolidado.valor_alvo_total), fmt(r_1b.consolidado.valor_alvo_total)),
            "", "---", "",
            "# DEMONSTRAÇÃO 2 — mover o INVARIANTE (troca o arquivo de EVENTOS)", "",
            "Mantenha fixos: veiculos_completo.xlsx e servicos.xlsx. Troque só o eventos.", ""]
    out += linha_resultado("2A) eventos_cobre (cobre o alvo)", r_1a, nv_c, ne_c)
    out += linha_resultado("2B) eventos_falta (deletei EV-002, falta cobertura)", r_2b, nv_c, ne_f)
    out += ["Frase para a reunião: \"Deletei o evento EV-002. Agora os eventos não cobrem",
            "o alvo: o Δ sai de R$ 0,00 e acusa exatamente R$ {} de diferença, e os".format(
                fmt(r_2b.consolidado.diferenca_alvo_vs_alocado)),
            "eventos alocados caem de {} para {}.\"".format(
                r_1a.consolidado.eventos_alocados, r_2b.consolidado.eventos_alocados),
            ""]

    (PASTA / "FOLHA_DE_APOIO.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    print("Arquivos gerados em:", PASTA)


if __name__ == "__main__":
    main()
