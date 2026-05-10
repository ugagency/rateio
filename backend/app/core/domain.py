"""Tipos de domínio do motor — entrada e saída puros, sem dependência de I/O."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Veiculo:
    id_veiculo: str
    status_ativo: bool
    data_quebra: str  # ISO YYYY-MM-DD
    tipo_categoria_risco: str
    qtd_cotas: int
    tipo_pagamento: Literal["MENSAL", "ANUAL"]
    is_funcionario: bool


@dataclass(frozen=True)
class Evento:
    id_evento: str
    data_ocorrencia: str  # ISO YYYY-MM-DD
    valor_total: float
    valor_saldo_pendente: float


@dataclass(frozen=True)
class ServicoFixo:
    id_veiculo: str
    taxa_administrativa: float
    valor_assistencia_24h: float
    valor_outros_produtos: float


@dataclass(frozen=True)
class PotinhoResultado:
    potinho: str
    degrau: float
    base_cotas: float
    valor: float


@dataclass(frozen=True)
class EventoRateado:
    mes_ano_ref: str
    id_evento: str
    data_ocorrencia: str
    valor_total_evento: float
    valor_saldo_antes: float
    valor_rateado_neste_mes: float
    valor_saldo_apos: float
    status_evento: Literal["LIQUIDADO", "SALDO_RESTANTE"]


@dataclass(frozen=True)
class Boleto:
    id_veiculo: str
    mes_ano_ref: str
    tipo_categoria_risco: str
    qtd_cotas: int
    custo_rateio_calculado: float
    custo_produtos_fixos: float
    valor_total_boleto: float
    tipo_pagamento: str
    is_funcionario: bool
    gera_boleto: bool


@dataclass(frozen=True)
class Consolidado:
    mes_ano_ref: str
    total_cotas_apuradas: float
    total_veiculos_elegiveis: int
    valor_alvo_total: float
    valor_p1_roubo_furto: float
    valor_p2_moto_fip: float
    valor_p3_venture_1: float
    valor_p4_venture_2: float
    eventos_alocados: int
    eventos_liquidados: int
    eventos_parciais: int
    saldo_para_proximo_mes: float
    diferenca_alvo_vs_alocado: float


@dataclass(frozen=True)
class ResultadoRateio:
    mes_ano_ref: str
    consolidado: Consolidado
    potinhos: list[PotinhoResultado] = field(default_factory=list)
    eventos_rateados: list[EventoRateado] = field(default_factory=list)
    boletos: list[Boleto] = field(default_factory=list)
