"""Schemas Pydantic — entrada/saída da API."""

from typing import Literal

from pydantic import BaseModel, Field


MesAnoRef = str  # formato MM/AAAA


class CalcularRateioRequest(BaseModel):
    mes_ano_ref: MesAnoRef = Field(..., examples=["05/2025"])
    force: bool = Field(default=False, description="Sobrescreve rateio existente para o mês.")


class PotinhoOut(BaseModel):
    potinho: str
    degrau: float
    base_cotas: float
    valor: float


class ConsolidadoOut(BaseModel):
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


class EventoRateadoOut(BaseModel):
    mes_ano_ref: str
    id_evento: str
    data_ocorrencia: str
    valor_total_evento: float
    valor_saldo_antes: float
    valor_rateado_neste_mes: float
    valor_saldo_apos: float
    status_evento: Literal["LIQUIDADO", "SALDO_RESTANTE"]


class BoletoOut(BaseModel):
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


class ResultadoRateioOut(BaseModel):
    mes_ano_ref: str
    consolidado: ConsolidadoOut
    potinhos: list[PotinhoOut]
    total_eventos_rateados: int
    total_boletos: int
    total_boletos_a_emitir: int
    receita_total_esperada: float


class PaginatedBoletos(BaseModel):
    mes_ano_ref: str
    total: int
    items: list[BoletoOut]


class PaginatedEventosRateados(BaseModel):
    mes_ano_ref: str
    total: int
    items: list[EventoRateadoOut]
