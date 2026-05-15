"""Tipos de domínio do motor AutoTruck — puros, sem I/O nem framework.

Segmentação LEVES/MOTOS (rateio variável, bases separadas) e PESADOS
(casco caminhão = pote fixo segregado). Espelha o estilo do `app/core`
do ELLO mas é totalmente independente.
"""

from dataclasses import dataclass, field
from typing import Literal

Segmento = Literal["LEVES", "MOTOS", "PESADOS"]
TipoEvento = Literal["INTEGRAL", "PARCIAL"]
Envolvimento = Literal["ASSOCIADO", "TERCEIRO"]


@dataclass(frozen=True)
class VeiculoAT:
    id_veiculo: str
    placa: str
    segmento: Segmento
    tipo_veiculo: str          # AUTOMOVEL, UTILITÁRIO, PREMIUM, MOTOCICLETA, CAMINHAO, SEMI REBOQUE
    valor_fipe: float
    status_ativo: bool         # ativo no SGA (foto de fechamento)
    adimplente: bool           # pagou — modelo purista (entra no denominador)
    servicos_adicionais: float = 0.0  # soma fixa de serviços contratados (Assist 24h, Vidros, etc.)


@dataclass(frozen=True)
class EventoAT:
    id_evento: str
    protocolo: str
    placa: str
    segmento: Segmento
    envolvimento: Envolvimento  # ASSOCIADO = custo; TERCEIRO = recuperação (abate)
    tipo_evento: TipoEvento     # pode ser reclassificado p/ INTEGRAL pela regra dos 75%
    valor_evento: float         # valor bruto do evento
    orcamento_reparo: float     # base da regra dos 75%
    valor_fipe: float           # base do valor integral (perda total)
    data_aviso: str             # ISO YYYY-MM-DD — chave FIFO
    franquia: float = 0.0
    valor_salvado: float = 0.0
    salvado_liquidado: bool = False  # crédito só vale no mês da liquidação financeira
    postergado: bool = False         # cortado em mês anterior → prioridade #1 absoluta


@dataclass(frozen=True)
class SegmentoResultado:
    segmento: Segmento
    modo: Literal["RATEIO_VARIAVEL", "POTE_FIXO"]
    custo_integrais: float
    custo_parciais: float
    deducao_salvados: float
    deducao_franquias: float
    recuperacao_terceiros: float
    custo_a_ratear: float
    cotas_ativas: float
    valor_cota: float
    arrecadado: float            # potes fixos
    reserva_ou_deficit: float    # arrecadado - custo (>0 reserva/"gordura", <0 déficit)
    alerta_volatilidade: bool    # único sinistro > 25% do pool
    faixa_estabilizacao: Literal["ABAIXO", "OK", "ACIMA"]
    sugestao: str
    diferenca_alvo_vs_alocado: float


@dataclass(frozen=True)
class EventoRateadoAT:
    mes_ano_ref: str
    id_evento: str
    protocolo: str
    segmento: Segmento
    envolvimento: Envolvimento
    data_aviso: str
    tipo_evento: TipoEvento
    reclassificado_75pct: bool
    valor_evento: float
    custo_a_ratear: float
    ordem_fifo: int
    status: Literal["ALOCADO", "POSTERGADO"]


@dataclass(frozen=True)
class BoletoAT:
    id_veiculo: str
    placa: str
    mes_ano_ref: str
    segmento: Segmento
    valor_fipe: float
    qtd_cotas: float
    cota_especial: bool
    custo_rateio: float
    custo_pote_terceiros: float
    custo_pote_caminhao: float
    servicos_adicionais: float
    valor_total_boleto: float
    gera_boleto: bool


@dataclass(frozen=True)
class AuditLog:
    mes_ano_ref: str
    acao: str            # ex.: "EXCLUSAO_MANUAL", "INCLUSAO_MANUAL"
    id_evento: str
    justificativa: str
    timestamp: str


@dataclass(frozen=True)
class ConsolidadoAT:
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


@dataclass(frozen=True)
class ResultadoRateioAT:
    mes_ano_ref: str
    consolidado: ConsolidadoAT
    segmentos: list[SegmentoResultado] = field(default_factory=list)
    eventos_rateados: list[EventoRateadoAT] = field(default_factory=list)
    boletos: list[BoletoAT] = field(default_factory=list)
    auditoria: list[AuditLog] = field(default_factory=list)
