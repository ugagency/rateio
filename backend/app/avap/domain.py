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
