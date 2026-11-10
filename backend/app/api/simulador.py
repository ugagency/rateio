"""Simulador rápido da Fenaprove: registra o contato do visitante e o que ele respondeu na simulação.

O cálculo da simulação roda no navegador. Aqui só fica o registro do lead, em dois momentos:
1) logo depois dos dados de contato (etapa "contato"), para não perder quem abandona a simulação;
2) ao mostrar o resultado (etapa "resultado"), com as faixas respondidas e a estimativa.
Os dois registros usam o mesmo ``id`` e o segundo atualiza a mesma linha.

Os leads vão para um CSV FORA do repositório, para nunca entrarem num commit:
pasta ``MUT_LEADS_DIR`` (variável de ambiente) ou, por padrão, ``~/Mut-leads``.

Envio ao n8n (opcional): com ``N8N_WEBHOOK_URL`` definida, cada lead gravado é enviado ao webhook
em segundo plano, com o cabeçalho ``X-Mut-Secret`` = ``N8N_WEBHOOK_SECRET``. O n8n grava na planilha
e faz o envio do WhatsApp. A coluna ``sincronizado`` do CSV guarda o que já chegou ao n8n: se a
internet cair, o lead fica pendente e vai junto no próximo lead ou em ``POST /avap/simulador/sincronizar``.
"""

from __future__ import annotations

import csv
import logging
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

router = APIRouter(prefix="/avap/simulador", tags=["simulador"])

_TRAVA = threading.Lock()
_TRAVA_SYNC = threading.Lock()
log = logging.getLogger(__name__)

CAMPOS_CONTATO = (
    "nome", "whatsapp", "email", "associacao", "cargo", "sistema_gestao",
    "modelo_rateio", "rateio_hoje", "observacao",
)
CAMPOS_SIM = (
    "faixa_veiculos", "faixa_fipe", "faixa_eventos", "faixa_custo",
    "veiculos_ativos", "cotas_total", "eventos_qtd", "eventos_valor", "valor_cota",
)
CAMPOS = [
    "id", "registrado_em", "atualizado_em", "etapa", "classificacao",
    *CAMPOS_CONTATO[:6], "modelo_rateio", "rateio_hoje", "quer_whatsapp", "consentimento",
    *CAMPOS_SIM, "observacao", "sincronizado",
]


def _arquivo() -> Path:
    pasta = Path(os.environ.get("MUT_LEADS_DIR") or (Path.home() / "Mut-leads"))
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / "leads_fenaprove.csv"


# DDDs em uso no Brasil (Anatel). Mesma lista e mesmas regras da tela do simulador.
DDDS = frozenset({
    11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68, 69, 71, 73, 74, 75, 77, 79, 81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99,
})
_EMAIL = re.compile(r"^[^\s@]+@[^\s@.]+(\.[^\s@.]+)*\.[A-Za-z]{2,}$")


def erro_whatsapp(valor: str) -> str:
    """Mensagem de erro do WhatsApp, ou "" se válido. Aceita com ou sem +55 e com ou sem máscara."""
    d = re.sub(r"\D", "", valor or "")
    if len(d) in (12, 13) and d.startswith("55"):
        d = d[2:]
    if len(d) not in (10, 11):
        return "Informe o WhatsApp com DDD, por exemplo (31) 99999-0000."
    if int(d[:2]) not in DDDS:
        return "O DDD informado não existe. Confira os dois primeiros números."
    numero = d[2:]
    if len(set(numero)) == 1:
        return "Esse número de WhatsApp não parece real. Confira os dígitos."
    if len(numero) == 9 and numero[0] != "9":
        return "Celular com 9 dígitos deve começar com 9."
    return ""


def erro_email(valor: str) -> str:
    return "" if _EMAIL.match((valor or "").strip()) else "O e-mail não parece válido. Confira o endereço."


class LeadIn(BaseModel):
    id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    etapa: Literal["contato", "resultado"] = "contato"
    nome: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=120)
    whatsapp: str = Field(default="", max_length=30)
    associacao: str = Field(default="", max_length=160)
    cargo: str = Field(default="", max_length=60)
    sistema_gestao: str = Field(default="", max_length=60)
    rateio_hoje: str = Field(default="", max_length=60)
    modelo_rateio: str = Field(default="", max_length=80)
    quer_whatsapp: bool = False
    consentimento: bool
    observacao: str = Field(default="", max_length=500)
    simulacao: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _contato_valido(self) -> LeadIn:
        self.email = self.email.strip()
        if msg := erro_email(self.email):
            raise ValueError(msg)
        # o WhatsApp só é pedido (e só é guardado) quando o visitante quer receber também por lá
        if self.quer_whatsapp:
            if msg := erro_whatsapp(self.whatsapp):
                raise ValueError(msg)
        else:
            self.whatsapp = ""
        return self


def classificar(lead: LeadIn) -> str:
    """Toda versão simplificada vai por e-mail. Quente: usa SGA e pediu também o WhatsApp.
    Morno: usa SGA sem WhatsApp, ou pediu o WhatsApp com outro sistema. Frio: outro sistema e só e-mail."""
    sga = lead.sistema_gestao.upper().startswith("SGA")
    if sga and lead.quer_whatsapp:
        return "quente"
    return "morno" if (sga or lead.quer_whatsapp) else "frio"


def _ler(arq: Path) -> list[dict]:
    if not arq.exists():
        return []
    with arq.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _preparar(arq: Path) -> None:
    """Se o arquivo existente tem outro cabeçalho (versão anterior do simulador), guarda uma cópia e recomeça."""
    if not arq.exists():
        return
    with arq.open(encoding="utf-8-sig", newline="") as f:
        cabecalho = next(csv.reader(f, delimiter=";"), [])
    if cabecalho != CAMPOS:
        arq.rename(arq.with_name(f"leads_fenaprove_anterior_{datetime.now():%Y%m%d_%H%M%S}.csv"))


def _gravar(arq: Path, linhas: list[dict]) -> None:
    tmp = arq.with_suffix(".tmp")
    # utf-8-sig: o Excel no Windows abre com acentos corretos.
    with tmp.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=";", extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(linhas)
    os.replace(tmp, arq)


def _webhook() -> tuple[str, str]:
    return os.environ.get("N8N_WEBHOOK_URL", "").strip(), os.environ.get("N8N_WEBHOOK_SECRET", "").strip()


def sincronizar_pendentes() -> int:
    """Envia ao n8n as linhas ainda não sincronizadas. Devolve quantas o n8n aceitou."""
    url, segredo = _webhook()
    if not url or not _TRAVA_SYNC.acquire(blocking=False):
        return 0  # sem webhook configurado, ou já há uma sincronização rodando
    try:
        with _TRAVA:
            pendentes = [x for x in _ler(_arquivo()) if x.get("sincronizado") != "sim"]
        aceitos: dict[str, str] = {}
        cabecalhos = {"X-Mut-Secret": segredo} if segredo else {}
        with httpx.Client(timeout=8) as cli:
            for linha in pendentes:
                corpo = {k: (v or "") for k, v in linha.items() if k in CAMPOS and k != "sincronizado"}
                try:
                    cli.post(url, json=corpo, headers=cabecalhos).raise_for_status()
                except httpx.HTTPError as e:
                    log.warning("n8n não recebeu o lead %s (%s); fica pendente", linha.get("id"), e)
                    break
                aceitos[linha["id"]] = linha.get("atualizado_em", "")
        if aceitos:
            with _TRAVA:
                arq = _arquivo()
                linhas = _ler(arq)
                for x in linhas:
                    # só marca se a linha não mudou enquanto era enviada
                    if x.get("id") in aceitos and aceitos[x["id"]] == x.get("atualizado_em"):
                        x["sincronizado"] = "sim"
                _gravar(arq, linhas)
        return len(aceitos)
    except OSError:
        log.warning("CSV em uso (Excel aberto?); sincronização com o n8n adiada")
        return 0
    finally:
        _TRAVA_SYNC.release()


@router.post("/lead")
def registrar_lead(lead: LeadIn, tarefas: BackgroundTasks) -> dict:
    if not lead.consentimento:
        raise HTTPException(422, "Sem consentimento o contato não é registrado.")
    agora = datetime.now().isoformat(timespec="seconds")
    sim = lead.simulacao or {}
    try:
        with _TRAVA:
            arq = _arquivo()
            _preparar(arq)
            linhas = _ler(arq)
            pos = next((i for i, x in enumerate(linhas) if x.get("id") == lead.id), None)
            antes = linhas[pos] if pos is not None else {}
            linha = {
                "id": lead.id,
                "registrado_em": antes.get("registrado_em") or agora,
                "atualizado_em": agora,
                # a etapa nunca volta atrás: depois de "resultado", um reenvio de "contato" não a desfaz
                "etapa": "resultado" if "resultado" in (lead.etapa, antes.get("etapa")) else "contato",
                "classificacao": classificar(lead),
                **{k: getattr(lead, k) for k in CAMPOS_CONTATO},
                "quer_whatsapp": "sim" if lead.quer_whatsapp else "não",
                "consentimento": "sim",
                **{k: sim.get(k, antes.get(k, "")) for k in CAMPOS_SIM},
                "sincronizado": "não",
            }
            if pos is None:
                linhas.append(linha)
            else:
                linhas[pos] = linha
            _gravar(arq, linhas)
    except OSError as e:
        # no Windows, o arquivo aberto no Excel não pode ser regravado
        raise HTTPException(503, "Não foi possível gravar a planilha. Feche o arquivo no Excel.") from e
    tarefas.add_task(sincronizar_pendentes)
    return {"ok": True, "classificacao": linha["classificacao"], "etapa": linha["etapa"]}


@router.get("/leads")
def resumo_leads() -> dict:
    arq = _arquivo()
    linhas = _ler(arq)
    cont = {c: sum(1 for x in linhas if x.get("classificacao") == c) for c in ("quente", "morno", "frio")}
    return {
        "total": len(linhas), **cont,
        "com_simulacao": sum(1 for x in linhas if x.get("etapa") == "resultado"),
        "pendentes_n8n": sum(1 for x in linhas if x.get("sincronizado") != "sim"),
        "n8n_configurado": bool(_webhook()[0]),
        "arquivo": str(arq),
    }


@router.post("/sincronizar")
def sincronizar() -> dict:
    """Reenvia ao n8n os leads pendentes (por exemplo, depois que a internet voltou)."""
    if not _webhook()[0]:
        raise HTTPException(409, "N8N_WEBHOOK_URL não está configurada no backend.")
    enviados = sincronizar_pendentes()
    pendentes = sum(1 for x in _ler(_arquivo()) if x.get("sincronizado") != "sim")
    return {"enviados": enviados, "pendentes": pendentes}


@router.get("/leads.csv")
def baixar_leads() -> Response:
    arq = _arquivo()
    corpo = arq.read_bytes() if arq.exists() else ("﻿" + ";".join(CAMPOS) + "\n").encode("utf-8")
    return Response(corpo, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="leads_fenaprove.csv"'})
