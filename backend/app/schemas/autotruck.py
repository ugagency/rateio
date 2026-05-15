"""Schemas Pydantic AutoTruck — saída da API (isolado do schema ELLO)."""

from typing import Literal

from pydantic import BaseModel, Field


class CalcularATRequest(BaseModel):
    mes_ano_ref: str = Field(..., examples=["12/2025"])
    force: bool = Field(default=False, description="Sobrescreve rateio existente para o mês.")
    exclusoes: dict[str, str] = Field(
        default_factory=dict,
        description="{id_evento: justificativa_tecnica} — exclusão manual exige justificativa (audit trail).",
    )


class SegmentoOut(BaseModel):
    segmento: str
    modo: str
    custo_integrais: float
    custo_parciais: float
    deducao_salvados: float
    deducao_franquias: float
    recuperacao_terceiros: float
    custo_a_ratear: float
    cotas_ativas: float
    valor_cota: float
    arrecadado: float
    reserva_ou_deficit: float
    alerta_volatilidade: bool
    faixa_estabilizacao: str
    sugestao: str
    diferenca_alvo_vs_alocado: float


class ConsolidadoATOut(BaseModel):
    mes_ano_ref: str
    cota_leves: float
    cota_motos: float
    custo_a_ratear_leves: float
    custo_a_ratear_motos: float
    bruto_leves: float
    bruto_motos: float
    recuperacao_terceiros_leves: float
    recuperacao_terceiros_motos: float
    pote_caminhao_arrecadado: float
    pote_caminhao_custo: float
    pote_caminhao_reserva: float
    pote_terceiros_arrecadado: float
    pote_terceiros_custo: float
    pote_terceiros_reserva: float
    total_veiculos: int
    total_veiculos_elegiveis: int
    total_cotas_leves: float
    total_cotas_motos: float
    eventos_alocados: int
    eventos_postergados: int
    eventos_reclassificados_75pct: int
    diferenca_total: float
    invariante_ok: bool


class EventoRateadoATOut(BaseModel):
    mes_ano_ref: str
    id_evento: str
    protocolo: str
    segmento: str
    envolvimento: str
    data_aviso: str
    tipo_evento: str
    reclassificado_75pct: bool
    valor_evento: float
    custo_a_ratear: float
    ordem_fifo: int
    status: str


class BoletoATOut(BaseModel):
    id_veiculo: str
    placa: str
    mes_ano_ref: str
    segmento: str
    valor_fipe: float
    qtd_cotas: float
    cota_especial: bool
    custo_rateio: float
    custo_pote_terceiros: float
    custo_pote_caminhao: float
    servicos_adicionais: float
    valor_total_boleto: float
    gera_boleto: bool


class AuditLogOut(BaseModel):
    mes_ano_ref: str
    acao: str
    id_evento: str
    justificativa: str
    timestamp: str


class ResultadoATOut(BaseModel):
    mes_ano_ref: str
    consolidado: ConsolidadoATOut
    segmentos: list[SegmentoOut]
    total_eventos: int
    total_boletos: int
    total_boletos_a_emitir: int
    receita_total_esperada: float


class PaginatedOut(BaseModel):
    mes_ano_ref: str
    total: int
    items: list


class PaginatedEventosATOut(BaseModel):
    mes_ano_ref: str
    total: int
    items: list[EventoRateadoATOut]


class PaginatedBoletosATOut(BaseModel):
    mes_ano_ref: str
    total: int
    items: list[BoletoATOut]


class PaginatedAuditOut(BaseModel):
    mes_ano_ref: str
    total: int
    items: list[AuditLogOut]
