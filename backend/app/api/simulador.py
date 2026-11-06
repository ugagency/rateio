"""Simulador rápido da Fenaprove: registra o contato do visitante e o que ele respondeu na simulação.

O cálculo da simulação roda no navegador. Aqui só fica o registro do lead, em dois momentos:
1) logo depois dos dados de contato (etapa "contato"), para não perder quem abandona a simulação;
2) ao mostrar o resultado (etapa "resultado"), com as faixas respondidas e a estimativa.
Os dois registros usam o mesmo ``id`` e o segundo atualiza a mesma linha.

Os leads vão para um CSV FORA do repositório, para nunca entrarem num commit:
pasta ``MUT_LEADS_DIR`` (variável de ambiente) ou, por padrão, ``~/Mut-leads``.
"""

from __future__ import annotations

import csv
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/avap/simulador", tags=["simulador"])

_TRAVA = threading.Lock()

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
    *CAMPOS_CONTATO[:6], "modelo_rateio", "rateio_hoje", "quer_versao", "consentimento",
    *CAMPOS_SIM, "observacao",
]


def _arquivo() -> Path:
    pasta = Path(os.environ.get("MUT_LEADS_DIR") or (Path.home() / "Mut-leads"))
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / "leads_fenaprove.csv"


class LeadIn(BaseModel):
    id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    etapa: Literal["contato", "resultado"] = "contato"
    nome: str = Field(min_length=2, max_length=120)
    whatsapp: str = Field(min_length=8, max_length=30)
    email: str = Field(default="", max_length=120)
    associacao: str = Field(default="", max_length=160)
    cargo: str = Field(default="", max_length=60)
    sistema_gestao: str = Field(default="", max_length=60)
    rateio_hoje: str = Field(default="", max_length=60)
    modelo_rateio: str = Field(default="", max_length=80)
    quer_versao: bool = False
    consentimento: bool
    observacao: str = Field(default="", max_length=500)
    simulacao: dict = Field(default_factory=dict)


def classificar(lead: LeadIn) -> str:
    """Quente: quer a versão simplificada e usa SGA. Morno: quer a versão e usa outro sistema. Frio: não quer."""
    if not lead.quer_versao:
        return "frio"
    return "quente" if lead.sistema_gestao.upper().startswith("SGA") else "morno"


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


@router.post("/lead")
def registrar_lead(lead: LeadIn) -> dict:
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
                "quer_versao": "sim" if lead.quer_versao else "não",
                "consentimento": "sim",
                **{k: sim.get(k, antes.get(k, "")) for k in CAMPOS_SIM},
            }
            if pos is None:
                linhas.append(linha)
            else:
                linhas[pos] = linha
            _gravar(arq, linhas)
    except OSError as e:
        # no Windows, o arquivo aberto no Excel não pode ser regravado
        raise HTTPException(503, "Não foi possível gravar a planilha. Feche o arquivo no Excel.") from e
    return {"ok": True, "classificacao": linha["classificacao"], "etapa": linha["etapa"]}


@router.get("/leads")
def resumo_leads() -> dict:
    arq = _arquivo()
    linhas = _ler(arq)
    cont = {c: sum(1 for x in linhas if x.get("classificacao") == c) for c in ("quente", "morno", "frio")}
    return {
        "total": len(linhas), **cont,
        "com_simulacao": sum(1 for x in linhas if x.get("etapa") == "resultado"),
        "arquivo": str(arq),
    }


@router.get("/leads.csv")
def baixar_leads() -> Response:
    arq = _arquivo()
    corpo = arq.read_bytes() if arq.exists() else ("﻿" + ";".join(CAMPOS) + "\n").encode("utf-8")
    return Response(corpo, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="leads_fenaprove.csv"'})
