"""Rotas de execução do motor: calcular, replay, consultar consolidado."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_service
from app.schemas.rateio import (
    CalcularRateioRequest,
    ConsolidadoOut,
    PotinhoOut,
    ResultadoRateioOut,
)
from app.services.rateio_service import RateioJaExisteError, RateioService

router = APIRouter(prefix="/rateio", tags=["rateio"])


def _to_resultado_out(resultado) -> ResultadoRateioOut:
    boletos_a_emitir = [b for b in resultado.boletos if b.gera_boleto]
    return ResultadoRateioOut(
        mes_ano_ref=resultado.mes_ano_ref,
        consolidado=ConsolidadoOut(**resultado.consolidado.__dict__),
        potinhos=[PotinhoOut(**p.__dict__) for p in resultado.potinhos],
        total_eventos_rateados=len(resultado.eventos_rateados),
        total_boletos=len(resultado.boletos),
        total_boletos_a_emitir=len(boletos_a_emitir),
        receita_total_esperada=round(sum(b.valor_total_boleto for b in boletos_a_emitir), 2),
    )


@router.post("/calcular", response_model=ResultadoRateioOut, status_code=status.HTTP_201_CREATED)
async def calcular_rateio(
    body: CalcularRateioRequest,
    service: RateioService = Depends(get_service),
) -> ResultadoRateioOut:
    try:
        resultado = await service.calcular_e_persistir(body.mes_ano_ref, force=body.force)
    except RateioJaExisteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_resultado_out(resultado)


@router.post("/replay", response_model=ResultadoRateioOut)
async def replay_rateio(
    body: CalcularRateioRequest,
    service: RateioService = Depends(get_service),
) -> ResultadoRateioOut:
    """Simula o rateio sem persistir — útil para conferir antes de fechar o mês."""
    resultado = await service.replay(body.mes_ano_ref)
    return _to_resultado_out(resultado)


@router.get("/{mes_ano_ref:path}", response_model=ConsolidadoOut)
async def get_consolidado(
    mes_ano_ref: str,
    service: RateioService = Depends(get_service),
) -> ConsolidadoOut:
    consolidado = await service.repo.buscar_consolidado(mes_ano_ref)
    if not consolidado:
        raise HTTPException(status_code=404, detail=f"Rateio não encontrado para {mes_ano_ref}")
    return ConsolidadoOut(**consolidado.__dict__)
