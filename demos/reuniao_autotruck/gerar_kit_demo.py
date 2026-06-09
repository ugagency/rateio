"""Gera o kit de demonstração da AutoTruck (Modelo Elo Ajustado).

Espelha o kit do ELLO: arquivos de entrada pequenos, com números redondos e
verificáveis ao vivo, mais um par de cenários para provar que o motor lê os
arquivos de verdade. Nada aqui toca o ELLO nem os dados reais do Rodrigo.

A AutoTruck recebe 3 arquivos na aba "Rodar Mês":
  BASE     -> cotas adimplentes/inadimplentes por segmento (denominador)
  RATEIO   -> eventos sinistrados do mês (numerador)
  PRODUTOS -> catálogo de fornecedor (opcional, informativo)

Saídas (nesta pasta):
  BASE_completa.xlsx / BASE_reduzida.xlsx
  RATEIO_completo.xlsx / RATEIO_reduzido.xlsx
  PRODUTOS.xlsx

Reprodutível: roda o motor real (app.autotruck.engine) sobre o que foi gerado
e confere os números esperados antes de salvar a folha de apoio.

Uso: backend/.venv/bin/python3 demos/reuniao_autotruck/gerar_kit_demo.py
"""

import sys
from pathlib import Path

import openpyxl

ROOT = Path("/root/projetos/Mut")
OUT = ROOT / "demos" / "reuniao_autotruck"
sys.path.insert(0, str(ROOT / "backend"))


# --------------------------- BASE ---------------------------
# Layout aceito por app.autotruck.ingestao_partes.ler_base:
# 3 segmentos lado a lado (PESADO@A, MOTO@G, LEVE@N). Cada bloco tem o rotulo
# "Cota por Situacao de Boleto", cabecalhos ABERTO/BAIXADO e uma linha TOTAL
# com os valores. BAIXADO = adimplentes (entram no denominador da cota);
# ABERTO = inadimplentes (ficam no cadastro, mas nao dividem o custo).
_SEG_COL = {"PESADO": 1, "MOTO": 7, "LEVE": 14}
_SEG_NOME = {"PESADO": "PESADOS", "MOTO": "MOTOS", "LEVE": "LEVES"}


def build_base(path: Path, cotas: dict) -> None:
    """cotas[SEGMENTO] = (adimplentes, inadimplentes)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BASE"
    for label, c0 in _SEG_COL.items():
        seg = _SEG_NOME[label]
        adimplentes, inadimplentes = cotas[seg]
        ws.cell(1, c0, label)
        ws.cell(3, c0, "Cota por Situacao de Boleto")
        ws.cell(4, c0 + 1, "ABERTO")
        ws.cell(4, c0 + 2, "BAIXADO")
        ws.cell(5, c0, "TOTAL")
        ws.cell(5, c0 + 1, inadimplentes)
        ws.cell(5, c0 + 2, adimplentes)
    wb.save(path)


# --------------------------- RATEIO ---------------------------
# Layout aceito por ler_rateio_partes: coluna A com marcador de secao
# ("MOTOS ASSOCIADOS", "LEVES TERCEIROS", ...) e, nas linhas-evento, o
# protocolo numerico em A, "INDENIZACAO INTEGRAL/PARCIAL" em B e o Valor
# Rateado na coluna K (11). O cabecalho precisa conter "Valor Rateado".
_RATEIO_HDR = ["Protocolo", "Tipo", "Motivo", "Envolvimento", "Situacao",
               "Placa", "Participacao", "Data", "Tipo Evento", "Mes Ref",
               "Valor Rateado"]


def build_rateio(path: Path, eventos: list) -> None:
    """eventos = lista de (segmento, envolvimento, tipo, valor_rateado),
    agrupada por (segmento, envolvimento) na ordem informada."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rateio POC"
    for c, h in enumerate(_RATEIO_HDR, 1):
        ws.cell(1, c, h)
    row = 2
    proto = 1000
    secao_atual = None
    for seg, env, tipo, valor in eventos:
        secao = (seg, env)
        if secao != secao_atual:
            marcador = f"{seg} {'ASSOCIADOS' if env == 'ASSOCIADO' else 'TERCEIROS'}"
            ws.cell(row, 1, marcador)
            row += 1
            secao_atual = secao
        proto += 1
        ws.cell(row, 1, proto)
        ws.cell(row, 2, f"INDENIZACAO {tipo}")
        ws.cell(row, 6, f"DEMO{proto}")
        ws.cell(row, 8, "2026-05-12")
        ws.cell(row, 11, valor)
        row += 1
    wb.save(path)


# --------------------------- PRODUTOS ---------------------------
# Catalogo de fornecedor. Informativo: nao entra no motor. ler_produtos exige
# cabecalho com FORNECEDOR e SERVICO na linha 1.
_PRODUTOS_HDR = ["FORNECEDOR", "SERVICO", "PRODUTO", "TIPO",
                 "QTD BOLETOS", "VALOR", "TOTAL"]
_PRODUTOS_LINHAS = [
    ("Assist 24h Brasil", "Assistencia 24h", "AUTOMOVEL", "MENSAL", 1000, 12.00, 12000.00),
    ("Assist 24h Brasil", "Assistencia 24h", "MOTOCICLETA", "MENSAL", 2000, 8.00, 16000.00),
    ("VidroForte", "Cobertura Vidros", "AUTOMOVEL", "MENSAL", 600, 10.00, 6000.00),
    ("RastreioJa", "Rastreador", "CAMINHAO", "MENSAL", 300, 25.00, 7500.00),
]


def build_produtos(path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "FORNECEDOR"
    for c, h in enumerate(_PRODUTOS_HDR, 1):
        ws.cell(1, c, h)
    for i, linha in enumerate(_PRODUTOS_LINHAS, start=2):
        for c, v in enumerate(linha, 1):
            ws.cell(i, c, v)
    wb.save(path)


# --------------------------- Dados do kit ---------------------------
# Eventos do mes (numerador). Associados entram no custo a ratear (bruto);
# terceiros sao rastreados a parte e NAO abatem a cota.
EVENTOS_COMPLETO = [
    ("MOTOS", "ASSOCIADO", "INTEGRAL", 30000.0),
    ("MOTOS", "ASSOCIADO", "PARCIAL", 10000.0),
    ("MOTOS", "TERCEIRO", "INTEGRAL", 6000.0),
    ("LEVES", "ASSOCIADO", "INTEGRAL", 50000.0),
    ("LEVES", "ASSOCIADO", "PARCIAL", 10000.0),
    ("LEVES", "TERCEIRO", "INTEGRAL", 5000.0),
    ("PESADOS", "TERCEIRO", "INTEGRAL", 8000.0),
]
# Cenario reduzido: remove o evento PARCIAL de MOTOS (10.000), derrubando o
# custo a ratear de MOTOS de 40.000 para 30.000.
EVENTOS_REDUZIDO = [e for e in EVENTOS_COMPLETO
                    if not (e[0] == "MOTOS" and e[2] == "PARCIAL")]

# Cotas adimplentes/inadimplentes por segmento.
COTAS_COMPLETA = {"LEVES": (1000, 100), "MOTOS": (2000, 200), "PESADOS": (300, 10)}
# Cenario reduzido: metade dos motociclistas adimplentes (2000 -> 1000),
# dobrando a cota de MOTOS.
COTAS_REDUZIDA = {"LEVES": (1000, 100), "MOTOS": (1000, 200), "PESADOS": (300, 10)}


def _rodar(base_path: Path, rateio_path: Path):
    from app.autotruck.ingestao_partes import compor
    from app.autotruck.engine import calcular_rateio_at
    veiculos, eventos, _prod, _bc, resumo = compor(
        str(base_path), str(rateio_path), produtos_path=str(OUT / "PRODUTOS.xlsx"))
    r = calcular_rateio_at(mes_ano_ref="DEMO_AUTOTRUCK", veiculos=veiculos, eventos=eventos)
    return r.consolidado, resumo


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    build_produtos(OUT / "PRODUTOS.xlsx")
    build_base(OUT / "BASE_completa.xlsx", COTAS_COMPLETA)
    build_base(OUT / "BASE_reduzida.xlsx", COTAS_REDUZIDA)
    build_rateio(OUT / "RATEIO_completo.xlsx", EVENTOS_COMPLETO)
    build_rateio(OUT / "RATEIO_reduzido.xlsx", EVENTOS_REDUZIDO)

    cenarios = {
        "BASE_completa + RATEIO_completo": (OUT / "BASE_completa.xlsx", OUT / "RATEIO_completo.xlsx"),
        "BASE_reduzida + RATEIO_completo": (OUT / "BASE_reduzida.xlsx", OUT / "RATEIO_completo.xlsx"),
        "BASE_completa + RATEIO_reduzido": (OUT / "BASE_completa.xlsx", OUT / "RATEIO_reduzido.xlsx"),
    }
    print("=" * 78)
    for nome, (b, r) in cenarios.items():
        co, resumo = _rodar(b, r)
        print(f"\n[{nome}]")
        print(f"  cotas adimplentes  LEVES={resumo.cotas_leves} MOTOS={resumo.cotas_motos} PESADOS={resumo.cotas_pesados}")
        print(f"  eventos lidos      {resumo.eventos_total}")
        print(f"  custo a ratear     LEVES=R$ {co.bruto_leves:,.2f}   MOTOS=R$ {co.bruto_motos:,.2f}")
        print(f"  cota por cota      LEVES=R$ {co.cota_leves:,.2f}   MOTOS=R$ {co.cota_motos:,.2f}")
        print(f"  terceiros (nao abate) LEVES=R$ {co.recuperacao_terceiros_leves:,.2f}  MOTOS=R$ {co.recuperacao_terceiros_motos:,.2f}")
        print(f"  eventos alocados   {co.eventos_alocados}")
        print(f"  invariante         Δ={co.diferenca_total}  OK={co.invariante_ok}")
        if resumo.alertas:
            print(f"  ALERTAS: {resumo.alertas}")
    print("\n" + "=" * 78)
    print(f"Kit gerado em: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
