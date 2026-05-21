"""Ingestão dos 3 xlsx de entrada do ELLO (veículos, eventos, serviços).

Mesmo contrato de colunas do CLI `rodar_motor_rateio.py` da raiz — quem
mudar lá, espelha aqui. O endpoint `/rateio/rodar-mes` consome estes
leitores para aceitar upload via multipart e gerar o resultado sem tocar
no dataset pré-carregado.
"""

from datetime import date, datetime

import openpyxl

from .domain import Evento, ServicoFixo, Veiculo

COLS_VEICULOS = ["ID_Veiculo", "Status_Ativo", "Data_Quebra", "Tipo_Categoria_Risco",
                 "Qtd_Cotas", "Tipo_Pagamento", "Is_Funcionario"]
COLS_EVENTOS = ["ID_Evento", "Data_Ocorrencia_Evento",
                "Valor_Total_Evento", "Valor_Saldo_Pendente"]
COLS_SERVICOS = ["ID_Veiculo", "Taxa_Administrativa",
                 "Valor_Assistencia_24h", "Valor_Outros_Produtos"]


class IngestaoError(ValueError):
    """Falha na leitura/validação de uma planilha de entrada."""


# -------- Detecção de tipo do arquivo (validação anti-troca-de-slot) --------

# Colunas exclusivas de cada xlsx — bastam pra identificar o tipo pelo header.
_MARKERS = {
    "VEICULOS": ("ID_VEICULO", "TIPO_CATEGORIA_RISCO", "QTD_COTAS"),
    "EVENTOS":  ("ID_EVENTO", "VALOR_SALDO_PENDENTE", "DATA_OCORRENCIA_EVENTO"),
    "SERVICOS": ("ID_VEICULO", "TAXA_ADMINISTRATIVA", "VALOR_ASSISTENCIA_24H"),
}
_NOME_HUMANO = {
    "VEICULOS": "veículos (cadastro elegível)",
    "EVENTOS":  "eventos (sinistros pendentes)",
    "SERVICOS": "serviços fixos (produtos por veículo)",
    "DESCONHECIDO": "formato desconhecido",
}


def detectar_tipo(path: str) -> str:
    """Retorna 'VEICULOS' | 'EVENTOS' | 'SERVICOS' | 'DESCONHECIDO' lendo
    só o cabeçalho (linha 1) da primeira aba. Pontua cada candidato pelo
    nº de colunas-marcador presentes e devolve o vencedor (empate em
    favor do mais específico)."""
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    except Exception:
        return "DESCONHECIDO"
    ws = wb.active
    try:
        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
    except Exception:
        return "DESCONHECIDO"
    if not header_row:
        return "DESCONHECIDO"
    headers = {str(h).strip().upper() for h in header_row if h is not None}

    scores: dict[str, int] = {}
    for tipo, marks in _MARKERS.items():
        scores[tipo] = sum(1 for m in marks if m in headers)
    # SERVICOS e VEICULOS compartilham ID_VEICULO — desempata pelo único exclusivo
    if scores["SERVICOS"] >= 2 and "TAXA_ADMINISTRATIVA" in headers:
        return "SERVICOS"
    if scores["VEICULOS"] >= 2 and "TIPO_CATEGORIA_RISCO" in headers:
        return "VEICULOS"
    if scores["EVENTOS"] >= 2 and "ID_EVENTO" in headers:
        return "EVENTOS"
    return "DESCONHECIDO"


def validar_slot(slot_esperado: str, path: str) -> str | None:
    """None se OK; senão devolve mensagem de erro pronta para o usuário."""
    tipo = detectar_tipo(path)
    if tipo == slot_esperado:
        return None
    if tipo == "DESCONHECIDO":
        return (f"Arquivo no slot '{slot_esperado.lower()}' não tem cabeçalho reconhecido. "
                f"Esperado: {_NOME_HUMANO[slot_esperado]}.")
    return (f"Arquivo no slot '{slot_esperado.lower()}' parece ser {_NOME_HUMANO[tipo]}. "
            f"Esperado: {_NOME_HUMANO[slot_esperado]}. Verifique se trocou os arquivos.")


def _data(v) -> str:
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    if not v:
        return ""
    s = str(v).strip()
    if len(s) >= 10 and s[2] == "/" and s[5] == "/":
        try:
            return datetime.strptime(s[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return s[:10]
    return s[:10]


def _bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in ("true", "1", "sim", "s", "verdadeiro")


def _num(v, default=0.0) -> float:
    if v is None or v == "":
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return default


def _ler(path: str, cols_obrigatorias: list[str], label: str) -> list[dict]:
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:
        raise IngestaoError(f"falha ao abrir planilha de {label}: {exc}") from exc
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = next(rows, None)
    if not headers:
        raise IngestaoError(f"planilha de {label} está vazia")
    headers = [str(h).strip() if h is not None else "" for h in headers]
    faltando = [c for c in cols_obrigatorias if c not in headers]
    if faltando:
        raise IngestaoError(
            f"colunas faltando em {label}: {faltando}. "
            f"esperado: {cols_obrigatorias}; encontrado: {headers}"
        )
    idx = {c: headers.index(c) for c in cols_obrigatorias}
    out = []
    for r in rows:
        if r is None or all(c is None or c == "" for c in r):
            continue
        out.append({c: r[idx[c]] for c in cols_obrigatorias})
    return out


def ler_veiculos(path: str) -> list[Veiculo]:
    raw = _ler(path, COLS_VEICULOS, "veículos")
    return [
        Veiculo(
            id_veiculo=str(r["ID_Veiculo"]).strip(),
            status_ativo=_bool(r["Status_Ativo"]),
            data_quebra=_data(r["Data_Quebra"]),
            tipo_categoria_risco=str(r["Tipo_Categoria_Risco"]).strip(),
            qtd_cotas=int(_num(r["Qtd_Cotas"], 0)),
            tipo_pagamento=str(r["Tipo_Pagamento"]).strip().upper(),
            is_funcionario=_bool(r["Is_Funcionario"]),
        )
        for r in raw
    ]


def ler_eventos(path: str) -> list[Evento]:
    raw = _ler(path, COLS_EVENTOS, "eventos")
    return [
        Evento(
            id_evento=str(r["ID_Evento"]).strip(),
            data_ocorrencia=_data(r["Data_Ocorrencia_Evento"]),
            valor_total=_num(r["Valor_Total_Evento"]),
            valor_saldo_pendente=_num(r["Valor_Saldo_Pendente"]),
        )
        for r in raw
    ]


def ler_servicos(path: str) -> list[ServicoFixo]:
    raw = _ler(path, COLS_SERVICOS, "serviços")
    return [
        ServicoFixo(
            id_veiculo=str(r["ID_Veiculo"]).strip(),
            taxa_administrativa=_num(r["Taxa_Administrativa"]),
            valor_assistencia_24h=_num(r["Valor_Assistencia_24h"]),
            valor_outros_produtos=_num(r["Valor_Outros_Produtos"]),
        )
        for r in raw
    ]
