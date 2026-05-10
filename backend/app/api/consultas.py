"""Rotas de consulta: eventos rateados, boletos, extrato de veículo."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_service
from app.schemas.rateio import (
    BoletoOut,
    EventoRateadoOut,
    PaginatedBoletos,
    PaginatedEventosRateados,
)
from app.services.rateio_service import RateioService

router = APIRouter(tags=["consultas"])


@router.get("/rateio/{mes_ano_ref:path}/eventos", response_model=PaginatedEventosRateados)
async def listar_eventos_rateados(
    mes_ano_ref: str,
    status_filter: str | None = Query(default=None, alias="status"),
    service: RateioService = Depends(get_service),
) -> PaginatedEventosRateados:
    eventos = await service.repo.listar_eventos_rateados(mes_ano_ref)
    if status_filter:
        eventos = [e for e in eventos if e.status_evento == status_filter]
    return PaginatedEventosRateados(
        mes_ano_ref=mes_ano_ref,
        total=len(eventos),
        items=[EventoRateadoOut(**e.__dict__) for e in eventos],
    )


@router.get("/boletos/{mes_ano_ref:path}", response_model=PaginatedBoletos)
async def listar_boletos(
    mes_ano_ref: str,
    categoria: str | None = None,
    gera_boleto: bool | None = None,
    id_veiculo: str | None = None,
    limit: int = Query(default=200, ge=1, le=10_000),
    offset: int = Query(default=0, ge=0),
    service: RateioService = Depends(get_service),
) -> PaginatedBoletos:
    boletos = await service.repo.listar_boletos(mes_ano_ref)
    if categoria:
        boletos = [b for b in boletos if b.tipo_categoria_risco == categoria]
    if gera_boleto is not None:
        boletos = [b for b in boletos if b.gera_boleto == gera_boleto]
    if id_veiculo:
        boletos = [b for b in boletos if b.id_veiculo == id_veiculo]

    total = len(boletos)
    page = boletos[offset : offset + limit]
    return PaginatedBoletos(
        mes_ano_ref=mes_ano_ref,
        total=total,
        items=[BoletoOut(**b.__dict__) for b in page],
    )


@router.get("/veiculos/{id_veiculo}/extrato/{mes_ano_ref:path}", response_model=BoletoOut)
async def extrato_veiculo(
    id_veiculo: str,
    mes_ano_ref: str,
    service: RateioService = Depends(get_service),
) -> BoletoOut:
    """Auditoria por veículo (LC 213/2025) — breakdown completo do boleto."""
    boletos = await service.repo.listar_boletos(mes_ano_ref)
    achado = next((b for b in boletos if b.id_veiculo == id_veiculo), None)
    if not achado:
        raise HTTPException(status_code=404, detail=f"Veículo {id_veiculo} não consta em {mes_ano_ref}")
    return BoletoOut(**achado.__dict__)
