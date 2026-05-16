"""Rotas do Motor AutoTruck — isoladas do ELLO (prefix /autotruck).

Sub-rotas específicas declaradas ANTES da catch-all GET /{mes_ano_ref:path}
(converter :path é ganancioso — mesma lição do fix de roteamento do ELLO).
"""

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query, status

from app.autotruck.config import get_autotruck_json_path
from app.autotruck.domain import ResultadoRateioAT
from app.autotruck.fechamento import FechamentoError, FechamentoService, FotoFechamento
from app.autotruck.fontes import FonteMemoria
from app.autotruck.repo import AutoTruckRepo
from app.autotruck.service import AutoTruckJaExisteError, AutoTruckService
from app.schemas.autotruck import (
    AbrirFechamentoRequest,
    AplicarAjusteRequest,
    AuditLogOut,
    BoletoATOut,
    CalcularATRequest,
    ConsolidadoATOut,
    EventoRateadoATOut,
    FotoFechamentoOut,
    HomologarRequest,
    IntegridadeOut,
    PaginatedAuditOut,
    PaginatedBoletosATOut,
    PaginatedEventosATOut,
    ResultadoATOut,
    SegmentoOut,
    SugerirAjusteRequest,
    SugestaoAjusteOut,
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


@router.post("/sugerir-ajuste", response_model=list[SugestaoAjusteOut])
def sugerir_ajuste(body: SugerirAjusteRequest) -> list[SugestaoAjusteOut]:
    """Assistente de ajuste: conjunto mínimo de eventos a postergar p/ a
    cota atingir o alvo (estabilização > FIFO; integral recente primeiro)."""
    sugs = _service().sugerir_ajuste(
        body.mes_ano_ref, alvo_cota=body.alvo_cota, incluir_parciais=body.incluir_parciais
    )
    return [SugestaoAjusteOut(**s.__dict__ | {
        "eventos_sugeridos": [e.__dict__ for e in s.eventos_sugeridos]
    }) for s in sugs]


@router.post("/aplicar-ajuste", response_model=ResultadoATOut, status_code=status.HTTP_201_CREATED)
def aplicar_ajuste(body: AplicarAjusteRequest) -> ResultadoATOut:
    """Aplica a sugestão: posterga os eventos (audit trail) e re-persiste."""
    try:
        r = _service().aplicar_ajuste(
            body.mes_ano_ref, body.ids_eventos, justificativa=body.justificativa
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_out(r)


# ---------------- Fechamento mensal — fluxo D+0..D+5 (N5) ----------------

@lru_cache
def _fech() -> FechamentoService:
    return FechamentoService()


def _fonte(mes: str) -> FonteMemoria:
    repo = _service().repo
    return FonteMemoria(repo.listar_veiculos(), repo.listar_eventos(), mes)


def _foto_out(f: FotoFechamento, fs: FechamentoService) -> FotoFechamentoOut:
    co = f.resultado.consolidado
    cota = fs.cota(f.id)
    return FotoFechamentoOut(
        id=f.id, mes_ano_ref=f.mes_ano_ref, criado_em=f.criado_em,
        hash_insumos=f.hash_insumos, origem=f.origem, status=f.status,
        n_veiculos=f.n_veiculos, n_eventos=f.n_eventos,
        bruto_leves=co.bruto_leves, bruto_motos=co.bruto_motos,
        invariante_ok=co.invariante_ok,
        cota_leves=cota["LEVES"]["valor_cota"], cota_motos=cota["MOTOS"]["valor_cota"],
        total_boletos_a_emitir=len(fs.lote_boletos(f.id)),
        auditoria=[AuditLogOut(**a.__dict__) for a in f.auditoria_fechamento],
    )


@router.post("/fechamento/abrir", response_model=FotoFechamentoOut,
             status_code=status.HTTP_201_CREATED)
def fechamento_abrir(body: AbrirFechamentoRequest) -> FotoFechamentoOut:
    """D+0 — Foto de Fechamento: lacra os insumos (hash) e calcula."""
    fs = _fech()
    try:
        f = fs.abrir(_fonte(body.mes_ano_ref),
                     base_cotas_leves=body.base_cotas_leves,
                     base_cotas_motos=body.base_cotas_motos, force=body.force)
    except FechamentoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _foto_out(f, fs)


@router.get("/fechamento/{fid}/integridade", response_model=IntegridadeOut)
def fechamento_integridade(fid: str) -> IntegridadeOut:
    fs = _fech()
    foto = _get_foto(fs, fid)
    return IntegridadeOut(**fs.verificar_integridade(fid, _fonte(foto.mes_ano_ref)))


@router.get("/fechamento/{fid}/lote-boletos", response_model=PaginatedBoletosATOut)
def fechamento_lote(fid: str) -> PaginatedBoletosATOut:
    fs = _fech()
    foto = _get_foto(fs, fid)
    lote = fs.lote_boletos(fid)
    return PaginatedBoletosATOut(
        mes_ano_ref=foto.mes_ano_ref, total=len(lote),
        items=[BoletoATOut(**b.__dict__) for b in lote[:5000]],
    )


@router.post("/fechamento/{fid}/homologar", response_model=FotoFechamentoOut)
def fechamento_homologar(fid: str, body: HomologarRequest) -> FotoFechamentoOut:
    """D+3 — homologação (exige justificativa técnica → audit trail)."""
    fs = _fech()
    try:
        f = fs.homologar(fid, body.justificativa)
    except FechamentoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _foto_out(f, fs)


@router.post("/fechamento/{fid}/emitir", response_model=FotoFechamentoOut)
def fechamento_emitir(fid: str) -> FotoFechamentoOut:
    """D+5 — emissão do lote (exige HOMOLOGADO)."""
    fs = _fech()
    try:
        f = fs.emitir(fid)
    except FechamentoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _foto_out(f, fs)


@router.get("/fechamento/{fid}", response_model=FotoFechamentoOut)
def fechamento_get(fid: str) -> FotoFechamentoOut:
    fs = _fech()
    return _foto_out(_get_foto(fs, fid), fs)


def _get_foto(fs: FechamentoService, fid: str) -> FotoFechamento:
    try:
        return fs.buscar(fid)
    except FechamentoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
