"""Dataclasses puras do domínio AVAP (sem I/O)."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class EstadoRateio(str, Enum):
    """Estados do campo Valor Rateado do SGA (PRD 4.2.1).

    Atenção: o campo do SGA NÃO define o fechamento real (ver
    docs/ANALISE_RATEIO_AGOSTO_SETEMBRO_AVAP.md); é só um atributo lido.
    """

    RATEADO = "RATEADO"
    NA_FILA = "NA_FILA"
    NAO_RATEADO = "NAO_RATEADO"
    RATEADO_DIVERGENTE = "RATEADO_DIVERGENTE"


@dataclass(frozen=True)
class VeiculoAVAP:
    placa: str | None
    rotulo_cota: str
    peso_cota: float
    sufixo_cota: str | None
    categoria: str
    tipo_veiculo: str
    valor_fipe: float | None
    situacao_veiculo: str
    situacao_associado: str
    matricula: int | None


@dataclass(frozen=True)
class EventoAVAP:
    protocolo: int
    situacao: str
    data_finalizacao: date | None
    valor_reparo: float
    valor_participacao: float
    custo_evento: float
    previsao_reparo: float
    motivo: str
    estado_rateio: EstadoRateio
    valor_rateado: float | None
    data_cadastro: date | None
    rotulo_cota: str | None
    peso_cota: float | None
    sufixo_cota: str | None
    categoria: str | None
    modelo: str | None
    tipo_veiculo: str | None
    tipo_evento: str | None
    placa: str | None  # o Nome do associado NÃO é carregado (dado pessoal)


@dataclass(frozen=True)
class Divergencia:
    campo: str
    lido: float
    rodape: float


@dataclass
class Conferencia:
    """Resultado da conferência entre o que foi lido e o rodapé do SGA."""

    divergencias: list[Divergencia] = field(default_factory=list)

    @property
    def aprovada(self) -> bool:
        return not self.divergencias


@dataclass
class LeituraVeiculos:
    veiculos: list[VeiculoAVAP]
    rodape: dict[str, float]
    conferencia: Conferencia


@dataclass
class LeituraEventos:
    eventos: list[EventoAVAP]
    rodape: dict[str, float]
    conferencia: Conferencia
    layout: str  # "28/09" (com Nome/Placa) ou "30/09" (com Tipo Veiculo)
    protocolos_duplicados: list[int] = field(default_factory=list)


# ───────────────────────── fase 1: seleção, lançamentos, motor ─────────────────────────


class TipoLancamento(str, Enum):
    SOMA = "SOMA"
    DEDUCAO = "DEDUCAO"


@dataclass(frozen=True)
class Lancamento:
    """Linha de soma ou dedução do fechamento (PRD 4.3). O valor é sempre positivo."""

    tipo: TipoLancamento
    codigo: str
    descricao: str
    valor: float
    documento: str | None = None


class Decisao(str, Enum):
    INCLUIR = "INCLUIR"
    EXCLUIR = "EXCLUIR"


@dataclass(frozen=True)
class DecisaoEvento:
    protocolo: int
    decisao: Decisao
    justificativa: str


@dataclass(frozen=True)
class Alerta:
    codigo: str  # A1..A7
    protocolo: int
    mensagem: str


@dataclass(frozen=True)
class EventoSelecionado:
    evento: EventoAVAP
    origem: str  # "REGRA" (fila do SGA sem alerta) ou "DECISAO" (operador)
    alertas: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventoNaoSelecionado:
    evento: EventoAVAP
    motivo: str


@dataclass
class ResultadoSelecao:
    selecionados: list[EventoSelecionado]
    nao_selecionados: list[EventoNaoSelecionado]
    alertas: list[Alerta]
    pendencias: list[int]  # protocolos com alerta e sem decisão: bloqueiam a homologação
    bloqueios: list[int]  # duplicatas divergentes: bloqueiam a homologação
    auditoria: list[str]

    @property
    def homologavel(self) -> bool:
        return not self.pendencias and not self.bloqueios

    @property
    def total_custo(self) -> float:
        return round(sum(s.evento.custo_evento for s in self.selecionados), 2)


@dataclass(frozen=True)
class BoletoAVAP:
    """Composição do boleto por veículo (split do art. 70 da Res. 491, PRD 9.4)."""

    placa: str | None
    matricula: int | None
    peso_cota: float
    contribuicao_rateio: float
    contribuicao_estabilizacao: float
    taxa_administracao: float
    produtos_beneficios: float

    @property
    def total(self) -> float:
        return round(
            self.contribuicao_rateio + self.contribuicao_estabilizacao
            + self.taxa_administracao + self.produtos_beneficios, 2)


@dataclass
class ResultadoAVAP:
    custo_eventos: float
    somas: float
    deducoes: float
    numerador: float
    total_cotas: float
    valor_cota: float
    veiculos_elegiveis: int
    veiculos_fora: dict[str, int]  # motivo -> quantidade
    boletos: list[BoletoAVAP]
    diferenca_arredondamento: float
    invariantes: dict[str, bool]
    eventos_por_motivo: dict[str, int]

    @property
    def aprovado(self) -> bool:
        return all(self.invariantes.values())
