"""Exportador de referência (SPEC-007): gera BASE.xlsx e RATEIO.xlsx no layout
que o motor aprovado lê (espelha backend/app/autotruck/ingestao_partes.py).

Esta é a implementação de referência e oráculo: o exportador do app (TypeScript)
deve produzir arquivos byte-compatíveis com o que estas funções geram, validado
pelo harness (SPEC-008). Não calcula rateio; apenas serializa.
"""

from itertools import groupby

from openpyxl import Workbook

# ADR-002 C4: app guarda segmento no plural; BASE usa o singular.
SEG_SINGULAR = {"PESADOS": "PESADO", "MOTOS": "MOTO", "LEVES": "LEVE"}
SEG_ORDER = ["PESADOS", "MOTOS", "LEVES"]
BLOCK_START = {"PESADOS": 1, "MOTOS": 6, "LEVES": 11}
ENV_LABEL = {"ASSOCIADO": "ASSOCIADOS", "TERCEIRO": "TERCEIROS"}

# Layout de colunas do RATEIO esperado por ler_rateio_partes (_RC):
# 1=Protocolo 2=Tipo(B) 3=Motivo 4=Envolvimento 5=Situação 6=Placa
# 7=Participação 8=Data Comunic 9=Tipo Evento 10=Mês Ref 11=Valor Rateado


def exportar_base(path: str, cotas: dict) -> None:
    """cotas: {segmento_plural: {'baixadas': int, 'abertas': int, 'canceladas': int}}.

    BAIXADO e o denominador (ADR-002 C1/C7); ABERTO e CANCELADO informativos.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "BASE"
    for seg in SEG_ORDER:
        c0 = BLOCK_START[seg]
        ws.cell(1, c0, SEG_SINGULAR[seg])           # rótulo de segmento na linha 1
        ws.cell(3, c0, "Cota por Situação")          # rótulo do sub-bloco
        ws.cell(4, c0 + 1, "BAIXADO")
        ws.cell(4, c0 + 2, "ABERTO")
        ws.cell(4, c0 + 3, "CANCELADO")
        ws.cell(5, c0, "TOTAL")
        d = cotas.get(seg, {})
        ws.cell(5, c0 + 1, int(d.get("baixadas", 0)))
        ws.cell(5, c0 + 2, int(d.get("abertas", 0)))
        ws.cell(5, c0 + 3, int(d.get("canceladas", 0)))
    wb.save(path)


def exportar_rateio(path: str, eventos: list[dict]) -> None:
    """eventos: lista de dicts com chaves segmento, envolvimento
    (ASSOCIADO/TERCEIRO), tipo (INTEGRAL/PARCIAL), protocolo, motivo, placa,
    data (dd/mm/aaaa), valor. Agrupa por marcador de seção (ADR-002 C4)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "RATEIO"
    cab = {1: "PROTOCOLO", 3: "MOTIVO", 4: "ENVOLVIMENTO", 5: "SITUAÇÃO",
           6: "PLACA", 7: "PARTICIPAÇÃO", 8: "DATA COMUNIC", 9: "TIPO EVENTO",
           10: "MÊS REF", 11: "VALOR RATEADO"}
    for c, v in cab.items():
        ws.cell(1, c, v)

    def chave(e):
        return (e["segmento"], e["envolvimento"])

    evs = sorted(eventos, key=lambda e: (e["segmento"], e["envolvimento"], e["data"]))
    r = 2
    for (seg, env), grp in groupby(evs, key=chave):
        ws.cell(r, 1, f"{seg} {ENV_LABEL[env]}")     # marcador de seção
        r += 1
        for e in grp:
            if not e.get("protocolo") or float(e.get("valor", 0)) <= 0:
                continue                             # o motor ignora; não exportar
            proto = e["protocolo"]
            ws.cell(r, 1, int(proto) if str(proto).isdigit() else str(proto))
            ws.cell(r, 2, f"INDENIZAÇÃO {e['tipo']}")
            ws.cell(r, 3, e.get("motivo", ""))
            ws.cell(r, 4, ENV_LABEL[env])
            ws.cell(r, 6, e.get("placa", ""))
            ws.cell(r, 8, e["data"])
            ws.cell(r, 9, e["tipo"])
            ws.cell(r, 11, float(e["valor"]))
            r += 1
    wb.save(path)
