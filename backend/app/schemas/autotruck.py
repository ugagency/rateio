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


class SugerirAjusteRequest(BaseModel):
    mes_ano_ref: str = Field(..., examples=["12/2025"])
    alvo_cota: float | None = Field(
        default=None, description="Cota-alvo. Default: topo da banda ±5% da média 3M (ou R$35)."
    )
    incluir_parciais: bool = Field(
        default=False, description="Inclui parciais como candidatos (oficina/nota fechada — raro)."
    )


class AplicarAjusteRequest(BaseModel):
    mes_ano_ref: str = Field(..., examples=["12/2025"])
    ids_eventos: list[str] = Field(..., min_length=1)
    justificativa: str | None = Field(
        default=None, description="Justificativa técnica (audit trail). Default automático."
    )


class EventoSugeridoOut(BaseModel):
    id_evento: str
    protocolo: str
    data_aviso: str
    tipo_evento: str
    custo_a_ratear: float


class SugestaoAjusteOut(BaseModel):
    segmento: str
    cota_atual: float
    alvo_cota: float
    precisa_ajuste: bool
    reducao_necessaria: float
    eventos_sugeridos: list[EventoSugeridoOut]
    reducao_obtida: float
    cota_resultante: float
    atingiu_alvo: bool
    mensagem: str


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
    media_cota_3m: float = 0.0
    variacao_vs_media: float = 0.0
    alerta_variacao_trimestral: bool = False


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
    alerta_variacao_trimestral: bool = False


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


# --- N5: fechamento mensal (D+0..D+5) ---
class AbrirFechamentoRequest(BaseModel):
    mes_ano_ref: str = Field(default="12/2025", examples=["12/2025"])
    base_cotas_leves: float = Field(default=81_757.0, description="Base de cotas ativas LEVES informada")
    base_cotas_motos: float = Field(default=16_135.0, description="Base de cotas ativas MOTOS informada")
    force: bool = Field(default=False)


class HomologarRequest(BaseModel):
    justificativa: str = Field(..., min_length=3,
                               description="Justificativa técnica (D&O / LC 213).")


class FotoFechamentoOut(BaseModel):
    id: str
    mes_ano_ref: str
    criado_em: str
    hash_insumos: str
    origem: str
    status: str
    n_veiculos: int
    n_eventos: int
    bruto_leves: float
    bruto_motos: float
    invariante_ok: bool
    cota_leves: float
    cota_motos: float
    total_boletos_a_emitir: int
    auditoria: list[AuditLogOut]


class IntegridadeOut(BaseModel):
    id: str
    intacto: bool
    hash_foto: str
    hash_atual: str
    mensagem: str


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
