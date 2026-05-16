"""Parâmetros do motor AutoTruck.

Alterar valores aqui muda os limiares globalmente, mas nunca a forma do
cálculo. Todos os números vêm da Especificação de Negócio / infográfico
e são parametrizáveis (ver PRD §12 — Premissas e decisões).
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ParametrosAT:
    # Cotas por patrimônio (FIPE) — progressão a cada faixa_fipe
    cota_base: float = 1.0          # ≤ R$10.000 → 1,0 cota
    passo_cota: float = 0.5         # +0,5 por faixa de R$10k (infográfico)
    faixa_fipe: float = 10_000.0
    # Cota especial high-end (não segue progressão linear)
    fipe_cota_especial: float = 450_000.0
    multiplicador_especial: float = 20.0   # faixa permitida 15–20
    # Regra dos 75% (perda total)
    threshold_perda_total: float = 0.75
    # Estabilização / churn
    cota_alvo_min: float = 30.0
    cota_alvo_max: float = 35.0
    var_trimestral_max: float = 0.05       # >5% na média trimestral dispara ajuste
    pct_volatilidade: float = 0.25         # 1 sinistro > 25% do pool → alerta
    # Potes fixos (não entram na divisão de cotas variável)
    arrecadacao_terceiros_estimada: float = 500_000.0  # spec §6 ("Ex.: R$ 500.000,00")
    valor_fixo_terceiros_por_assoc: float = 0.0        # se >0, sobrepõe a estimada
    arrecadacao_caminhao_estimada: float = 0.0
    valor_fixo_caminhao_por_assoc: float = 0.0
    # N4 — preço por produto (transcrição): "terceiro de 50.000 é 20 e poucos
    # reais; de 100.000 é R$30". Casco caminhão = valor fixo mensal por associado.
    preco_terceiros_50k: float = 20.0
    preco_terceiros_100k: float = 30.0
    preco_casco_caminhao: float = 0.0  # >0 ativa arrecadação real do pote caminhão


PRECO_TERCEIROS = {"NENHUM": 0.0, "50K": 20.0, "100K": 30.0}


def preco_cobertura_terceiros(cobertura: str, p: "ParametrosAT") -> float:
    """Preço mensal do produto Danos a Terceiros pela faixa contratada."""
    return {"NENHUM": 0.0, "50K": p.preco_terceiros_50k, "100K": p.preco_terceiros_100k}.get(
        (cobertura or "NENHUM").upper(), 0.0
    )


PARAMS_DEFAULT = ParametrosAT()

LEVES_TIPOS = ("AUTOMOVEL", "UTILITÁRIO", "UTILITARIO", "PREMIUM")
MOTOS_TIPOS = ("MOTOCICLETA",)
PESADOS_TIPOS = ("CAMINHAO", "CAMINHÃO", "SEMI REBOQUE", "SEMIREBOQUE")


def segmento_por_tipo(tipo_veiculo: str) -> str:
    t = (tipo_veiculo or "").strip().upper()
    if t in MOTOS_TIPOS:
        return "MOTOS"
    if t in PESADOS_TIPOS:
        return "PESADOS"
    return "LEVES"


def cotas_por_fipe(valor_fipe: float, p: ParametrosAT = PARAMS_DEFAULT) -> tuple[float, bool]:
    """Devolve (qtd_cotas, é_cota_especial).

    FIPE > teto especial → multiplicador fixo (não progride linearmente).
    Caso contrário, progressão por faixa: ≤10k=1,0; 10.001–20.000=1,5; +0,5/faixa.
    """
    if valor_fipe > p.fipe_cota_especial:
        return p.multiplicador_especial, True
    faixas = max(0, math.ceil(valor_fipe / p.faixa_fipe) - 1)
    return round(p.cota_base + p.passo_cota * faixas, 2), False


def aplica_regra_75(orcamento_reparo: float, valor_fipe: float, p: ParametrosAT = PARAMS_DEFAULT) -> bool:
    """True se o orçamento de reparo supera o threshold do FIPE → vira INTEGRAL."""
    return valor_fipe > 0 and orcamento_reparo > p.threshold_perda_total * valor_fipe
