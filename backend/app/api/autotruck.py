"""Rotas do Motor AutoTruck — isoladas do ELLO (prefix /autotruck).

Sub-rotas específicas declaradas ANTES da catch-all GET /{mes_ano_ref:path}
(converter :path é ganancioso — mesma lição do fix de roteamento do ELLO).
"""

import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.autotruck.config import get_autotruck_json_path
from app.autotruck.domain import ResultadoRateioAT
from app.autotruck.fechamento import FechamentoError, FechamentoService, FotoFechamento
from app.autotruck.fontes import FonteMemoria
from app.autotruck.ingestao_partes import (
    ParteIngestaoResumo,
    compor,
    detectar_tipo,
    ler_base,
    ler_rateio_partes,
    validar_slot,
)
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


# ---------------- Rodar Mês: ingestão de BASE+RATEIO+PRODUTOS separados ----------------


class InspecionarArquivoOut(BaseModel):
    """Resposta da inspeção rápida (1 arquivo, sem rodar engine)."""

    tipo_detectado: str          # BASE | RATEIO | PRODUTOS | DESCONHECIDO
    valido: bool
    erro: str | None = None
    extras: dict = {}            # se BASE: cotas_baixadas/abertas (para auto-preencher form)


@router.post("/inspecionar-arquivo", response_model=InspecionarArquivoOut)
async def inspecionar_arquivo(
    arquivo: UploadFile = File(...),
    slot_esperado: str = Form(..., description="BASE | RATEIO | PRODUTOS"),
) -> InspecionarArquivoOut:
    """Lê **um único** xlsx, devolve tipo detectado, validade e (se BASE) as
    cotas já pré-extraídas. Frontend chama no onChange do file input para
    validar slot + auto-preencher overrides — sem rodar o motor."""
    slot = slot_esperado.strip().upper()
    if slot not in ("BASE", "RATEIO", "PRODUTOS"):
        raise HTTPException(status_code=400, detail=f"slot_esperado inválido: {slot_esperado}")
    tmpdir = Path(tempfile.mkdtemp(prefix="inspect-"))
    try:
        path = tmpdir / "arquivo.xlsx"
        path.write_bytes(await arquivo.read())
        msg = validar_slot(slot, str(path))
        tipo = detectar_tipo(str(path))
        extras: dict = {}
        if tipo == "BASE" and msg is None:
            try:
                bc = ler_base(str(path))
                extras = {
                    "cotas_baixadas": bc.cotas_baixadas,
                    "cotas_abertas": bc.cotas_abertas,
                    "boletos_baixados": bc.boletos_baixados,
                    "boletos_abertos": bc.boletos_abertos,
                }
            except Exception:
                pass  # detecção valeu; extras é só bônus
        elif tipo == "RATEIO" and msg is None:
            try:
                evs = ler_rateio_partes(str(path))
                # segmentos com eventos → o frontend usa p/ guard de cota faltante
                extras = {"segmentos": sorted({e.segmento for e in evs})}
            except Exception:
                pass
        return InspecionarArquivoOut(
            tipo_detectado=tipo, valido=(msg is None), erro=msg, extras=extras,
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


class RodarMesOut(BaseModel):
    """Saída do endpoint /autotruck/rodar-mes — ingestão de arquivos
    separados (BASE + RATEIO + PRODUTOS opcional) e cálculo do mês."""

    resultado: ResultadoATOut
    ingestao: dict


@router.post("/rodar-mes", response_model=RodarMesOut, status_code=status.HTTP_201_CREATED)
async def rodar_mes(
    base: UploadFile = File(..., description="Planilha BASE (cotas/boletos por situação)."),
    rateio: UploadFile = File(..., description="Planilha RATEIO (eventos sinistrados do mês)."),
    produtos: UploadFile | None = File(default=None, description="Catálogo de produtos (opcional)."),
    mes_ano_ref: str = Form(..., description="Mês de referência MM/AAAA (ex.: 04/2026)."),
    cotas_leves: int | None = Form(default=None, description="Override de cotas LEVES adimplentes (a BASE do Rodrigo costuma não trazer)."),
    cotas_motos: int | None = Form(default=None, description="Override de cotas MOTOS adimplentes."),
) -> RodarMesOut:
    """Recebe BASE+RATEIO (e opcionalmente PRODUTOS) como upload, compõe
    insumos do engine, calcula o rateio e persiste no repo do mês indicado.
    Após o sucesso, os endpoints `/autotruck/{mes}/*` (segmentos, eventos,
    boletos, …) já refletem o resultado."""
    tmpdir = Path(tempfile.mkdtemp(prefix="rodar-mes-"))
    try:
        base_path = tmpdir / "base.xlsx"
        rateio_path = tmpdir / "rateio.xlsx"
        base_path.write_bytes(await base.read())
        rateio_path.write_bytes(await rateio.read())
        produtos_path = None
        if produtos is not None and (produtos.filename or "").strip():
            produtos_path = tmpdir / "produtos.xlsx"
            produtos_path.write_bytes(await produtos.read())
        # validação anti-troca-de-slot (antes de qualquer parsing pesado)
        erros: list[str] = []
        for slot, p in (("BASE", base_path), ("RATEIO", rateio_path)):
            msg = validar_slot(slot, str(p))
            if msg:
                erros.append(msg)
        if produtos_path:
            msg = validar_slot("PRODUTOS", str(produtos_path))
            if msg:
                erros.append(msg)
        if erros:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=" • ".join(erros))
        try:
            veiculos, eventos, _produtos_cat, _base_counts, resumo = compor(
                str(base_path), str(rateio_path),
                produtos_path=str(produtos_path) if produtos_path else None,
                cotas_leves_override=cotas_leves,
                cotas_motos_override=cotas_motos,
            )
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Falha lendo planilhas: {exc}") from exc
        resultado = _service().rodar_externos_e_persistir(
            mes_ano_ref, veiculos, eventos, force=True
        )
        return RodarMesOut(resultado=_to_out(resultado), ingestao=resumo.__dict__)
    finally:
        # limpa o tmp dir
        for p in tmpdir.iterdir():
            try:
                p.unlink()
            except OSError:
                pass
        try:
            tmpdir.rmdir()
        except OSError:
            pass


# Caminho dos arquivos da reunião 19/05 com o Rodrigo (Remonta/) — o usuário
# os mantém versionados localmente; o endpoint abaixo serve para uma demo
# 1-clique sem precisar reupload manual a cada sessão.
_REMONTA_DIR = Path(__file__).resolve().parents[3] / "Remonta"
_REMONTA_BASE = _REMONTA_DIR / "BASE_Reconstruida.xlsx"
_REMONTA_RATEIO = _REMONTA_DIR / "Rateio_POC_Completo.xlsx"
_REMONTA_COTAS_LEVES_FALLBACK = 30_000  # idem tools/poc_remonta.py


@router.post("/poc-remonta", response_model=RodarMesOut, status_code=status.HTTP_201_CREATED)
def poc_remonta(
    mes_ano_ref: str = Query("04/2026", description="Mês de referência da PoC."),
    cotas_leves: int = Query(_REMONTA_COTAS_LEVES_FALLBACK,
                              description="Override de cotas LEVES (a BASE do Rodrigo não traz)."),
) -> RodarMesOut:
    """Carrega 1-clique os arquivos da reunião com a AutoTruck (Remonta/) e
    roda o motor em `mes_ano_ref`. Idêntico ao `/rodar-mes`, mas sem upload —
    útil para demonstrar a PoC na plataforma sem fricção."""
    if not _REMONTA_BASE.exists() or not _REMONTA_RATEIO.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arquivos Remonta ausentes em {_REMONTA_DIR}",
        )
    try:
        veiculos, eventos, _produtos_cat, _base_counts, resumo = compor(
            str(_REMONTA_BASE), str(_REMONTA_RATEIO),
            produtos_path=None,
            cotas_leves_override=cotas_leves,
            cotas_motos_override=None,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Falha lendo planilhas Remonta: {exc}") from exc
    resultado = _service().rodar_externos_e_persistir(
        mes_ano_ref, veiculos, eventos, force=True,
    )
    return RodarMesOut(resultado=_to_out(resultado), ingestao=resumo.__dict__)


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


@router.get("/{mes_ano_ref:path}/export-analitico")
def export_analitico(mes_ano_ref: str) -> Response:
    """Exporta a aba ANALITICO **preenchida com os números do mês** (do motor),
    fiel ao FECHAMENTO (posições/labels/cores/formatos). Campos de faturamento
    (VALOR RECEBIDO, RESUMO, FORNECEDOR) saem em branco com uma NOTA de origem
    em cada célula — o motor de rateio não os calcula."""
    from app.autotruck.export_analitico import gerar_analitico_xlsx

    conteudo = gerar_analitico_xlsx(_buscar(mes_ano_ref))
    nome = f"ANALITICO_AutoTruck_{mes_ano_ref.replace('/', '-')}.xlsx"
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.get("/{mes_ano_ref:path}", response_model=ResultadoATOut)
def consolidado(mes_ano_ref: str) -> ResultadoATOut:
    return _to_out(_buscar(mes_ano_ref))
