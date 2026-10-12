"""Rotas do Motor AVAP (prefix /avap), isoladas de ELLO e AutoTruck.

Fluxo: inspecionar arquivos -> selecionar (SGA) -> decidir pendências -> lançamentos -> calcular.
O estado fica em memória por competência (formato `MM-AAAA` na URL), como o repositório json dos
outros motores: zera a cada restart do backend. O critério de elegibilidade do denominador (D2) é
um parâmetro, porque ainda aguarda confirmação do Cícero.
"""

import tempfile
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.avap.domain import (
    Decisao,
    DecisaoEvento,
    EventoAVAP,
    Lancamento,
    LeituraEventos,
    LeituraVeiculos,
    ResultadoAVAP,
    ResultadoSelecao,
    TipoLancamento,
    VeiculoAVAP,
)
from app.avap.engine import calcular_rateio
from app.avap.historico import classificar_linha, ler_historico
from app.avap.ingestao import ConferenciaRodapeError, LayoutDesconhecidoError, ler_eventos, ler_veiculos
from app.avap.reconciliacao import CRITERIOS
from app.avap.rules import REGRAS_PADRAO
from app.avap.selecao import selecionar

router = APIRouter(prefix="/avap", tags=["avap"])

# D2 assumido (aguarda o Cícero): inadimplentes ficam fora do denominador, a compensação vem pelas
# linhas INADIMPLÊNCIA e recuperados. Bate com ~R$ 7,8 por cota sobre as cotas de veículos ativos.
CRITERIO_PADRAO = "VEICULO"

RAIZ = Path(__file__).resolve().parents[3]
DEMO = {
    "veiculos": RAIZ / "AVAP" / "Cotas_ativasAVAP_09_26.xlsx",
    "fila": RAIZ / "AVAP" / "foto28-09.xlsx",
    "historico": RAIZ / "AVAP" / "rateio_agosto.xlsx",
    "aba": "Rateio_setembro",
}


@dataclass
class Sessao:
    mes: str
    veiculos: list[VeiculoAVAP]
    eventos: list[EventoAVAP]
    data_fechamento: date | None = None
    decisoes: dict[int, DecisaoEvento] = field(default_factory=dict)
    lancamentos: list[Lancamento] = field(default_factory=list)
    criterio: str = CRITERIO_PADRAO
    selecao: ResultadoSelecao | None = None
    resultado: ResultadoAVAP | None = None
    comparativo: dict[str, float] = field(default_factory=dict)
    origem: str = "upload"


_SESSOES: dict[str, Sessao] = {}


def _chave(mes: str) -> str:
    return mes.replace("/", "-").strip()


def _sessao(mes: str) -> Sessao:
    s = _SESSOES.get(_chave(mes))
    if not s:
        raise HTTPException(404, f"Nenhum fechamento AVAP carregado para {mes}. Envie os arquivos primeiro.")
    return s


def _resselecionar(s: Sessao) -> ResultadoSelecao:
    s.selecao = selecionar(s.eventos, REGRAS_PADRAO, list(s.decisoes.values()), s.data_fechamento)
    s.resultado = None  # qualquer mudança de seleção invalida o cálculo anterior
    return s.selecao


# ───────────────────────────── serialização ─────────────────────────────


class EventoOut(BaseModel):
    protocolo: int
    motivo: str
    placa: str | None
    data_finalizacao: date | None
    custo_evento: float
    valor_participacao: float
    estado_rateio: str
    origem: str | None = None
    alertas: list[str] = []
    motivo_fora: str | None = None


class AlertaOut(BaseModel):
    codigo: str
    protocolo: int
    mensagem: str


class SelecaoOut(BaseModel):
    mes: str
    origem: str
    total_eventos_lidos: int
    selecionados: int
    custo_selecionado: float
    pendencias: list[int]
    bloqueios: list[int]
    homologavel: bool
    alertas: list[AlertaOut]
    eventos_pendentes: list[EventoOut]
    decisoes: int
    lancamentos: int
    auditoria: list[str]


def _ev(e: EventoAVAP, origem: str | None = None, alertas=(), fora: str | None = None) -> EventoOut:
    return EventoOut(
        protocolo=e.protocolo, motivo=e.motivo, placa=e.placa, data_finalizacao=e.data_finalizacao,
        custo_evento=e.custo_evento, valor_participacao=e.valor_participacao,
        estado_rateio=e.estado_rateio.value, origem=origem, alertas=list(alertas), motivo_fora=fora)


def _selecao_out(s: Sessao) -> SelecaoOut:
    sel = s.selecao or _resselecionar(s)
    pend = set(sel.pendencias)
    return SelecaoOut(
        mes=s.mes, origem=s.origem, total_eventos_lidos=len(s.eventos),
        selecionados=len(sel.selecionados), custo_selecionado=sel.total_custo,
        pendencias=sel.pendencias, bloqueios=sel.bloqueios, homologavel=sel.homologavel,
        alertas=[AlertaOut(codigo=a.codigo, protocolo=a.protocolo, mensagem=a.mensagem) for a in sel.alertas],
        eventos_pendentes=[
            _ev(n.evento, fora=n.motivo) for n in sel.nao_selecionados if n.evento.protocolo in pend],
        decisoes=len(s.decisoes), lancamentos=len(s.lancamentos), auditoria=sel.auditoria[:50])


class ResultadoOut(BaseModel):
    mes: str
    criterio: str
    custo_eventos: float
    somas: float
    deducoes: float
    numerador: float
    total_cotas: float
    valor_cota: float
    veiculos_elegiveis: int
    veiculos_fora: dict[str, int]
    total_boletos: int
    total_rateio: float
    diferenca_arredondamento: float
    invariantes: dict[str, bool]
    aprovado: bool
    eventos_por_motivo: dict[str, int]
    comparativo_criterios: dict[str, float]
    lancamentos: list[dict]
    valor_cota_estimado: bool = True  # D2 aguardando confirmação do Cícero


def _resultado_out(s: Sessao) -> ResultadoOut:
    r = s.resultado
    if r is None:
        raise HTTPException(409, "Rateio ainda não calculado para esta competência.")
    return ResultadoOut(
        mes=s.mes, criterio=s.criterio, custo_eventos=r.custo_eventos, somas=r.somas, deducoes=r.deducoes,
        numerador=r.numerador, total_cotas=r.total_cotas, valor_cota=round(r.valor_cota, 4),
        veiculos_elegiveis=r.veiculos_elegiveis, veiculos_fora=r.veiculos_fora,
        total_boletos=len(r.boletos), total_rateio=round(sum(b.contribuicao_rateio for b in r.boletos), 2),
        diferenca_arredondamento=r.diferenca_arredondamento, invariantes=r.invariantes,
        aprovado=r.aprovado, eventos_por_motivo=r.eventos_por_motivo,
        comparativo_criterios=s.comparativo,
        lancamentos=[{"tipo": x.tipo.value, "codigo": x.codigo, "descricao": x.descricao, "valor": x.valor}
                     for x in s.lancamentos])


# ───────────────────────────── upload ─────────────────────────────


def _salvar_temp(dados: bytes) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="avap-")) / "arquivo.xlsx"
    tmp.write_bytes(dados)
    return tmp


def _limpar(p: Path) -> None:
    try:
        p.unlink()
        p.parent.rmdir()
    except OSError:
        pass


def _ler_veic(p) -> LeituraVeiculos:
    try:
        return ler_veiculos(p)
    except (ConferenciaRodapeError, LayoutDesconhecidoError, ValueError, KeyError) as exc:
        raise HTTPException(422, f"Base de veículos inválida: {exc}") from exc


def _ler_ev(p) -> LeituraEventos:
    try:
        return ler_eventos(p)
    except (ConferenciaRodapeError, LayoutDesconhecidoError, ValueError, KeyError) as exc:
        raise HTTPException(422, f"Relatório de eventos inválido: {exc}") from exc


class InspecionarOut(BaseModel):
    slot: str
    valido: bool
    erro: str | None = None
    resumo: dict = {}


@router.post("/inspecionar-arquivo", response_model=InspecionarOut)
async def inspecionar_arquivo(arquivo: UploadFile = File(...), slot: str = Form(...)) -> InspecionarOut:
    """Valida um único export do SGA (com conferência do rodapé) sem montar o fechamento."""
    slot = slot.strip().upper()
    if slot not in ("VEICULOS", "EVENTOS"):
        raise HTTPException(400, f"slot inválido: {slot}")
    p = _salvar_temp(await arquivo.read())
    try:
        if slot == "VEICULOS":
            try:
                lv = ler_veiculos(p)
            except Exception as exc:  # noqa: BLE001 - qualquer falha de leitura vira badge de erro
                return InspecionarOut(slot=slot, valido=False, erro=str(exc))
            return InspecionarOut(slot=slot, valido=True, resumo={
                "veiculos": len(lv.veiculos), "cotas": round(sum(v.peso_cota for v in lv.veiculos), 2)})
        try:
            le = ler_eventos(p)
        except Exception as exc:  # noqa: BLE001
            return InspecionarOut(slot=slot, valido=False, erro=str(exc))
        fila = [e for e in le.eventos if e.estado_rateio.value == "NA_FILA"]
        return InspecionarOut(slot=slot, valido=True, resumo={
            "eventos": len(le.eventos), "na_fila": len(fila),
            "custo_na_fila": round(sum(e.custo_evento for e in fila), 2), "layout": le.layout})
    finally:
        _limpar(p)


@router.post("/selecionar", response_model=SelecaoOut)
async def selecionar_fechamento(
    veiculos: UploadFile = File(...),
    eventos: UploadFile = File(...),
    mes_ano_ref: str = Form(...),
    data_fechamento: date | None = Form(None),
) -> SelecaoOut:
    pv, pe = _salvar_temp(await veiculos.read()), _salvar_temp(await eventos.read())
    try:
        lv, le = _ler_veic(pv), _ler_ev(pe)
    finally:
        _limpar(pv)
        _limpar(pe)
    s = Sessao(mes=mes_ano_ref, veiculos=lv.veiculos, eventos=le.eventos, data_fechamento=data_fechamento)
    _SESSOES[_chave(mes_ano_ref)] = s
    _resselecionar(s)
    return _selecao_out(s)


@router.post("/demo-setembro", response_model=SelecaoOut)
def demo_setembro() -> SelecaoOut:
    """Carrega os arquivos reais de 09/2026 do servidor e reproduz as decisões e lançamentos do
    fechamento feito hoje pela AVAP. Fallback do estande: o upload continua sendo o caminho principal."""
    faltando = [str(p.name) for k, p in DEMO.items() if k != "aba" and not p.exists()]
    if faltando:
        raise HTTPException(404, f"Arquivos de demonstração ausentes em AVAP/: {', '.join(faltando)}")
    veic = _ler_veic(DEMO["veiculos"]).veiculos
    fila = _ler_ev(DEMO["fila"]).eventos
    hist = ler_historico(DEMO["historico"])[DEMO["aba"]]
    na_fila = {e.protocolo for e in fila if e.estado_rateio in REGRAS_PADRAO.estados_candidatos}
    decisoes = {p: DecisaoEvento(p, Decisao.INCLUIR, "consta no fechamento real de 09/2026") for p in hist.protocolos}
    decisoes.update({p: DecisaoEvento(p, Decisao.EXCLUIR, "na fila do SGA e fora do fechamento real")
                     for p in na_fila - hist.protocolos})
    s = Sessao(mes="09/2026", veiculos=veic, eventos=fila, decisoes=decisoes,
               lancamentos=list(hist.lancamentos), origem="demonstração (09/2026)")
    _SESSOES[_chave(s.mes)] = s
    _resselecionar(s)
    return _selecao_out(s)


# ───────────────────────────── consultas e decisões ─────────────────────────────


@router.get("/{mes}/selecao", response_model=SelecaoOut)
def ver_selecao(mes: str) -> SelecaoOut:
    return _selecao_out(_sessao(mes))


class DecisaoIn(BaseModel):
    protocolo: int
    decisao: Decisao
    justificativa: str = Field(min_length=3)


class DecidirIn(BaseModel):
    decisoes: list[DecisaoIn]


@router.post("/{mes}/decidir", response_model=SelecaoOut)
def decidir(mes: str, body: DecidirIn) -> SelecaoOut:
    s = _sessao(mes)
    for d in body.decisoes:
        s.decisoes[d.protocolo] = DecisaoEvento(d.protocolo, d.decisao, d.justificativa.strip())
    _resselecionar(s)
    return _selecao_out(s)


class LancamentoIn(BaseModel):
    descricao: str = Field(min_length=2)
    valor: float  # com sinal: positivo soma, negativo deduz


class LancamentosIn(BaseModel):
    lancamentos: list[LancamentoIn]


@router.post("/{mes}/lancamentos", response_model=SelecaoOut)
def definir_lancamentos(mes: str, body: LancamentosIn) -> SelecaoOut:
    s = _sessao(mes)
    s.lancamentos = [classificar_linha(x.descricao, x.valor) for x in body.lancamentos if x.valor]
    s.resultado = None
    return _selecao_out(s)


@router.get("/{mes}/lancamentos")
def ver_lancamentos(mes: str) -> list[dict]:
    s = _sessao(mes)
    return [{"descricao": x.descricao, "codigo": x.codigo, "tipo": x.tipo.value,
             "valor": x.valor if x.tipo == TipoLancamento.SOMA else -x.valor} for x in s.lancamentos]


class CalcularIn(BaseModel):
    criterio: str = CRITERIO_PADRAO


@router.post("/{mes}/calcular", response_model=ResultadoOut)
def calcular(mes: str, body: CalcularIn) -> ResultadoOut:
    s = _sessao(mes)
    if body.criterio not in CRITERIOS:
        raise HTTPException(400, f"Critério inválido: {body.criterio}. Use um de {', '.join(CRITERIOS)}.")
    sel = s.selecao or _resselecionar(s)
    if not sel.homologavel:
        raise HTTPException(409, f"Fechamento não homologável: {len(sel.pendencias)} pendência(s) e "
                                 f"{len(sel.bloqueios)} bloqueio(s). Decida cada evento antes de calcular.")
    eventos = [x.evento for x in sel.selecionados]
    if not eventos:
        raise HTTPException(409, "Nenhum evento selecionado.")
    s.criterio = body.criterio
    try:
        s.resultado = calcular_rateio(eventos, s.lancamentos, s.veiculos,
                                      replace(REGRAS_PADRAO, criterio_elegibilidade=body.criterio))
        s.comparativo = {}
        for c in CRITERIOS:
            try:
                s.comparativo[c] = round(calcular_rateio(
                    eventos, s.lancamentos, s.veiculos,
                    replace(REGRAS_PADRAO, criterio_elegibilidade=c)).valor_cota, 4)
            except ValueError:
                continue
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _resultado_out(s)


@router.get("/{mes}/resultado", response_model=ResultadoOut)
def ver_resultado(mes: str) -> ResultadoOut:
    return _resultado_out(_sessao(mes))


class EventosPagina(BaseModel):
    total: int
    items: list[EventoOut]


@router.get("/{mes}/eventos", response_model=EventosPagina)
def eventos(mes: str, incluidos: bool = True, page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=500)) -> EventosPagina:
    s = _sessao(mes)
    sel = s.selecao or _resselecionar(s)
    if incluidos:
        lista = [_ev(x.evento, x.origem, x.alertas) for x in sel.selecionados]
    else:
        lista = [_ev(n.evento, fora=n.motivo) for n in sel.nao_selecionados
                 if n.evento.situacao == "FINALIZADO" and n.evento.tipo_evento == "Evento Associado"]
    lista.sort(key=lambda e: -e.custo_evento)
    ini = (page - 1) * page_size
    return EventosPagina(total=len(lista), items=lista[ini:ini + page_size])


class BoletoOut(BaseModel):
    placa: str | None
    matricula: int | None
    peso_cota: float
    contribuicao_rateio: float
    total: float


class BoletosPagina(BaseModel):
    total: int
    soma_rateio: float
    items: list[BoletoOut]


def _boletos_filtrados(s: Sessao, q: str) -> list:
    if s.resultado is None:
        raise HTTPException(409, "Rateio ainda não calculado para esta competência.")
    bs = s.resultado.boletos
    q = q.strip().upper()
    if q:
        bs = [b for b in bs if q in (b.placa or "").upper() or q == str(b.matricula or "")]
    return bs


@router.get("/{mes}/boletos", response_model=BoletosPagina)
def boletos(mes: str, q: str = "", page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=500)) -> BoletosPagina:
    bs = _boletos_filtrados(_sessao(mes), q)
    ini = (page - 1) * page_size
    return BoletosPagina(
        total=len(bs), soma_rateio=round(sum(b.contribuicao_rateio for b in bs), 2),
        items=[BoletoOut(placa=b.placa, matricula=b.matricula, peso_cota=b.peso_cota,
                         contribuicao_rateio=b.contribuicao_rateio, total=b.total)
               for b in bs[ini:ini + page_size]])


@router.get("/{mes}/boletos.csv")
def boletos_csv(mes: str) -> Response:
    bs = _boletos_filtrados(_sessao(mes), "")
    linhas = ["placa;matricula;peso_cota;contribuicao_rateio;total"]
    linhas += [f"{b.placa or ''};{b.matricula or ''};{b.peso_cota:.2f};"
               f"{b.contribuicao_rateio:.2f};{b.total:.2f}".replace(".", ",") for b in bs]
    return Response("\n".join(linhas), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="boletos_avap_{_chave(mes)}.csv"'})
