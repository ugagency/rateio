"""Rotas do Motor AutoTruck — isoladas do ELLO (prefix /autotruck).

Sub-rotas específicas declaradas ANTES da catch-all GET /{mes_ano_ref:path}
(converter :path é ganancioso — mesma lição do fix de roteamento do ELLO).
"""

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query, status

from app.autotruck.config import get_autotruck_json_path
from app.autotruck.domain import ResultadoRateioAT
from app.autotruck.repo import AutoTruckRepo
from app.autotruck.service import AutoTruckJaExisteError, AutoTruckService
from app.schemas.autotruck import (
    AuditLogOut,
    BoletoATOut,
    CalcularATRequest,
    ConsolidadoATOut,
    EventoRateadoATOut,
    PaginatedAuditOut,
    PaginatedBoletosATOut,
    PaginatedEventosATOut,
    ResultadoATOut,
    SegmentoOut,
)

router = APIRouter(prefix="/autotruck", tags=["autotruck"])


@lru_cache
def _service() -> AutoTruckService:
    return AutoTruckService(AutoTruckRepo(get_autotruck_json_path()))


def _to_out(r: ResultadoRateioAT) -> ResultadoATOut:
    emitir = [b for b in r.boletos if b.gera_boleto]
    return ResultadoATOut(
        mes_ano_ref=r.mes_ano_ref,
        consolidado=ConsolidadoATOut(**r.consolidado.__dict__),
        segmentos=[SegmentoOut(**s.__dict__) for s in r.segmentos],
        total_eventos=len(r.eventos_rateados),
        total_boletos=len(r.boletos),
        total_boletos_a_emitir=len(emitir),
        receita_total_esperada=round(sum(b.valor_total_boleto for b in emitir), 2),
    )


def _buscar(mes_ano_ref: str) -> ResultadoRateioAT:
    r = _service().repo.buscar(mes_ano_ref)
    if not r:
        raise HTTPException(status_code=404, detail=f"Rateio AutoTruck não encontrado para {mes_ano_ref}")
    return r


@router.post("/calcular", response_model=ResultadoATOut, status_code=status.HTTP_201_CREATED)
def calcular(body: CalcularATRequest) -> ResultadoATOut:
    try:
        r = _service().calcular_e_persistir(
            body.mes_ano_ref, force=body.force, exclusoes=body.exclusoes
        )
    except AutoTruckJaExisteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_out(r)


@router.post("/replay", response_model=ResultadoATOut)
def replay(body: CalcularATRequest) -> ResultadoATOut:
    """Painel de simulação — recalcula sem persistir (trocas hipotéticas)."""
    return _to_out(_service().replay(body.mes_ano_ref, exclusoes=body.exclusoes))


@router.get("/{mes_ano_ref:path}/segmentos", response_model=list[SegmentoOut])
def segmentos(mes_ano_ref: str) -> list[SegmentoOut]:
    return [SegmentoOut(**s.__dict__) for s in _buscar(mes_ano_ref).segmentos]


@router.get("/{mes_ano_ref:path}/eventos", response_model=PaginatedEventosATOut)
def eventos(
    mes_ano_ref: str,
    segmento: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
) -> PaginatedEventosATOut:
    evs = _buscar(mes_ano_ref).eventos_rateados
    if segmento:
        evs = [e for e in evs if e.segmento == segmento]
    if status_filter:
        evs = [e for e in evs if e.status == status_filter]
    return PaginatedEventosATOut(
        mes_ano_ref=mes_ano_ref, total=len(evs),
        items=[EventoRateadoATOut(**e.__dict__) for e in evs],
    )


@router.get("/{mes_ano_ref:path}/boletos", response_model=PaginatedBoletosATOut)
def boletos(
    mes_ano_ref: str,
    segmento: str | None = None,
    gera_boleto: bool | None = None,
    limit: int = Query(default=200, ge=1, le=20_000),
    offset: int = Query(default=0, ge=0),
) -> PaginatedBoletosATOut:
    bs = _buscar(mes_ano_ref).boletos
    if segmento:
        bs = [b for b in bs if b.segmento == segmento]
    if gera_boleto is not None:
        bs = [b for b in bs if b.gera_boleto == gera_boleto]
    total = len(bs)
    page = bs[offset : offset + limit]
    return PaginatedBoletosATOut(
        mes_ano_ref=mes_ano_ref, total=total,
        items=[BoletoATOut(**b.__dict__) for b in page],
    )


@router.get("/{mes_ano_ref:path}/potes", response_model=list[SegmentoOut])
def potes(mes_ano_ref: str) -> list[SegmentoOut]:
    """Potes fixos (não-variáveis): casco caminhão e danos a terceiros."""
    return [
        SegmentoOut(**s.__dict__)
        for s in _buscar(mes_ano_ref).segmentos
        if s.modo == "POTE_FIXO"
    ]


@router.get("/{mes_ano_ref:path}/auditoria", response_model=PaginatedAuditOut)
def auditoria(mes_ano_ref: str) -> PaginatedAuditOut:
    logs = _buscar(mes_ano_ref).auditoria
    return PaginatedAuditOut(
        mes_ano_ref=mes_ano_ref, total=len(logs),
        items=[AuditLogOut(**a.__dict__) for a in logs],
    )


@router.get("/{mes_ano_ref:path}", response_model=ResultadoATOut)
def consolidado(mes_ano_ref: str) -> ResultadoATOut:
    return _to_out(_buscar(mes_ano_ref))
