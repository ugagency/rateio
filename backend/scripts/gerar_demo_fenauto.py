"""Gera os arquivos fictícios da demonstração Fenauto a partir dos arquivos reais de 09/2026 da AVAP.

Troca protocolo, placa, matrícula, nome do associado e usuário do rodapé por valores fictícios, com
mapeamento fixo (semente) e consistente entre os 3 arquivos. Valores, pesos, datas e rodapés do SGA
ficam intactos, então a leitura confere e o motor seleciona os mesmos 103 eventos. Só o fechamento
muda num ponto: a linha sem descrição vira "RECEITA COM VENDAS DE SALVADOS" e é ajustada para que o
total a ratear dê exatamente R$ 7,78 por cota, e os boletos somem o total sem diferença de centavo.

Os arquivos reais (pasta AVAP/, fora do git) só são lidos aqui. A saída (pasta demo_fenauto/) não tem
dado real e vai para o git.

Uso:
    backend/.venv/bin/python backend/scripts/gerar_demo_fenauto.py
"""

import random
import string
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[2]
ORIGEM = RAIZ / "AVAP"
DESTINO = RAIZ / "demo_fenauto"
VALOR_COTA = 7.78
OPERADOR = "OPERADOR DEMONSTRACAO"

NOMES = ["ANA", "BRUNO", "CARLA", "DANIEL", "ELAINE", "FABIO", "GABRIELA", "HELIO", "IRENE", "JOAO",
         "KATIA", "LUCAS", "MARINA", "NELSON", "OLIVIA", "PAULO", "RAQUEL", "SERGIO", "TATIANA", "VITOR"]
SOBRENOMES = ["ALMEIDA", "BARBOSA", "CARDOSO", "DIAS", "FERREIRA", "GOMES", "LIMA", "MOREIRA", "NUNES",
              "PEREIRA", "RAMOS", "SANTOS", "TEIXEIRA", "VIEIRA", "XAVIER", "ROCHA", "MENDES", "COSTA"]

rnd = random.Random(213)
protos: dict[int, int] = {}
placas: dict[str, str] = {}
mats: dict[int, int] = {}
nomes: dict[str, str] = {}
REAIS: set = set()  # todo valor dos arquivos reais: nenhum fictício pode coincidir com um deles


def proto(p):
    """Mantém tamanho e, nos protocolos de 10 dígitos, o ano (não muda o alerta A1)."""
    if not p:
        return p
    p = int(p)
    if p not in protos:
        txt = str(p)
        pre = txt[:4] if len(txt) >= 10 else ""
        while True:
            novo = int(pre + "".join(rnd.choices(string.digits, k=len(txt) - len(pre))))
            if len(str(novo)) == len(txt) and novo not in protos.values() and novo not in REAIS:
                break
        protos[p] = novo
    return protos[p]


def placa(p):
    if not p:
        return p
    p = str(p).strip()
    if p not in placas:
        while True:
            nova = ("".join(rnd.choices(string.ascii_uppercase, k=3)) + rnd.choice(string.digits)
                    + rnd.choice(string.ascii_uppercase) + "".join(rnd.choices(string.digits, k=2)))
            if nova not in placas.values() and nova not in REAIS:
                break
        placas[p] = nova
    return placas[p]


def mat(m):
    if m is None or m == "":
        return m
    if m not in mats:
        mats[m] = 100000 + len(mats)
    return mats[m]


def nome(n):
    if not n:
        return n
    if n not in nomes:
        while True:
            novo = f"{rnd.choice(NOMES)} {rnd.choice(SOBRENOMES)} {rnd.choice(SOBRENOMES)}"
            if novo not in REAIS:
                break
        nomes[n] = novo
    return nomes[n]


def rodape_usuario(ws, col: int) -> None:
    """Troca o nome do usuário do SGA nas linhas de rodapé (texto 'data-hora-NOME')."""
    for row in ws.iter_rows():
        c = row[col]
        if isinstance(c.value, str) and c.value[:2].isdigit() and c.value.count("-") >= 2 and "/" in c.value[:6]:
            c.value = c.value.rsplit("-", 1)[0] + "-" + OPERADOR


def carregar_reais() -> None:
    for arq in ("Cotas_ativasAVAP_09_26.xlsx", "foto28-09.xlsx", "rateio_agosto.xlsx"):
        wb = openpyxl.load_workbook(ORIGEM / arq, read_only=True)
        for ws in wb.worksheets:
            for r in ws.iter_rows(values_only=True):
                REAIS.update(c.strip() if isinstance(c, str) else c for c in r if c is not None)
        wb.close()


def veiculos() -> int:
    wb = openpyxl.load_workbook(ORIGEM / "Cotas_ativasAVAP_09_26.xlsx")
    ws = wb.worksheets[0]
    for row in ws.iter_rows(min_row=2):
        if row[0].value and row[1].value and str(row[1].value).startswith("COTA"):
            row[0].value = placa(row[0].value)
            row[7].value = mat(row[7].value)
    rodape_usuario(ws, 1)
    wb.save(DESTINO / "Cotas_ativas_FENAUTO_09_26.xlsx")
    return ws.max_row


def fila() -> None:
    wb = openpyxl.load_workbook(ORIGEM / "foto28-09.xlsx")
    ws = wb.worksheets[0]
    for row in ws.iter_rows(min_row=2):
        if isinstance(row[0].value, int):
            row[0].value = proto(row[0].value)
            row[1].value = nome(row[1].value)
            row[2].value = placa(row[2].value)
    rodape_usuario(ws, 0)
    wb.save(DESTINO / "foto_eventos_28-09_FENAUTO.xlsx")


def historico() -> None:
    wb = openpyxl.load_workbook(ORIGEM / "rateio_agosto.xlsx")
    for aba in [w for w in wb.worksheets if w.title != "Rateio_setembro"]:
        wb.remove(aba)
    ws = wb["Rateio_setembro"]
    linhas = [r for r in ws.iter_rows(min_row=2) if any(c.value is not None for c in r)]
    for r in linhas:
        if r[1].value:
            r[1].value = placa(r[1].value)
            r[2].value = proto(r[2].value)
    # A linha sem descrição vira salvados e absorve a diferença para o valor por cota fechar em 7,78.
    sem_desc = next(r for r in linhas if not r[1].value and not r[3].value)
    numerador = round(sum(float(r[7].value or 0) for r in linhas), 2)
    alvo = round(_total_cotas_ativas() * VALOR_COTA, 2)
    ajuste = round(alvo - numerador, 2)
    sem_desc[3].value = "RECEITA COM VENDAS DE SALVADOS"
    for c in (5, 7):
        sem_desc[c].value = round(float(sem_desc[c].value) + ajuste, 2)
    print(f"numerador real {numerador:,.2f} -> fictício {alvo:,.2f} (ajuste {ajuste:+,.2f} em salvados)")
    wb.save(DESTINO / "rateio_setembro_FENAUTO.xlsx")


def _total_cotas_ativas() -> float:
    """Cotas no denominador do critério vigente (veículo ativo), lidas pelo próprio motor."""
    import sys
    sys.path.insert(0, str(RAIZ / "backend"))
    from app.avap.engine import _motivo_fora
    from app.avap.ingestao import ler_veiculos
    from app.avap.rules import REGRAS_PADRAO
    vs = ler_veiculos(DESTINO / "Cotas_ativas_FENAUTO_09_26.xlsx").veiculos
    return sum(v.peso_cota for v in vs if _motivo_fora(v, REGRAS_PADRAO) is None)

if __name__ == "__main__":
    DESTINO.mkdir(exist_ok=True)
    carregar_reais()
    veiculos()
    fila()
    historico()
    print(f"{len(protos)} protocolos, {len(placas)} placas, {len(mats)} matrículas, {len(nomes)} nomes trocados")
    print(f"arquivos em {DESTINO}")
