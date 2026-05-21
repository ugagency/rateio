"""Rotas de execução do motor: calcular, replay, consultar consolidado."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.ingestao_xlsx import (
    IngestaoError,
    ler_eventos,
    ler_servicos,
    ler_veiculos,
    validar_slot,
)
from app.deps import get_service
from app.schemas.rateio import (
    CalcularRateioRequest,
    ConsolidadoOut,
    PotinhoOut,
    ResultadoRateioOut,
)
from app.services.rateio_service import RateioJaExisteError, RateioService

router = APIRouter(prefix="/rateio", tags=["rateio"])


class RodarMesELLOOut(BaseModel):
    """Saída do /rateio/rodar-mes — resultado + contagens de ingestão."""

    resultado: ResultadoRateioOut
    ingestao: dict


@router.post("/rodar-mes", response_model=RodarMesELLOOut, status_code=status.HTTP_201_CREATED)
async def rodar_mes_ello(
    veiculos: UploadFile = File(..., description="Planilha veiculos.xlsx (cadastro elegível)."),
    eventos: UploadFile = File(..., description="Planilha eventos.xlsx (sinistros pendentes)."),
    servicos: UploadFile = File(..., description="Planilha servicos.xlsx (produtos fixos por veículo)."),
    mes_ano_ref: str = Form(..., description="Mês de referência MM/AAAA."),
    service: RateioService = Depends(get_service),
) -> RodarMesELLOOut:
    """Aceita os 3 xlsx de entrada do ELLO via upload, ingere, roda o motor
    e persiste no repo. Após o sucesso, `/rateio/{mes}` e endpoints de
    consulta refletem o resultado."""
    tmpdir = Path(tempfile.mkdtemp(prefix="rodar-mes-ello-"))
    try:
        vp = tmpdir / "veiculos.xlsx"
        ep = tmpdir / "eventos.xlsx"
        sp = tmpdir / "servicos.xlsx"
        vp.write_bytes(await veiculos.read())
        ep.write_bytes(await eventos.read())
        sp.write_bytes(await servicos.read())
        # validação anti-troca-de-slot
        erros = [
            msg for slot, p in (("VEICULOS", vp), ("EVENTOS", ep), ("SERVICOS", sp))
            if (msg := validar_slot(slot, str(p)))
        ]
        if erros:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=" • ".join(erros))
        try:
            vs = ler_veiculos(str(vp))
            es = ler_eventos(str(ep))
            ss = ler_servicos(str(sp))
        except IngestaoError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        resultado = await service.rodar_externos_e_persistir(
            mes_ano_ref, vs, es, ss, force=True
        )
        return RodarMesELLOOut(
            resultado=_to_resultado_out(resultado),
            ingestao={
                "veiculos": len(vs),
                "eventos": len(es),
                "servicos": len(ss),
                "veiculos_elegiveis": resultado.consolidado.total_veiculos_elegiveis,
                "valor_alvo_total": resultado.consolidado.valor_alvo_total,
                "diferenca_alvo_vs_alocado": resultado.consolidado.diferenca_alvo_vs_alocado,
            },
        )
    finally:
        for p in tmpdir.iterdir():
            try:
                p.unlink()
            except OSError:
                pass
        try:
            tmpdir.rmdir()
        except OSError:
            pass


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
