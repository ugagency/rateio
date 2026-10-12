"""Parâmetros do motor AVAP (PRD 5.2, 6 e 12). Tudo configurável; defaults do MVP."""

from dataclasses import dataclass, field

from .domain import EstadoRateio

MOTIVOS_INTEGRAIS = frozenset({"V.F.I", "FURTO", "ROUBO"})


@dataclass(frozen=True)
class RegrasAVAP:
    # Seleção (5.1/5.2). Só a fila do SGA (Valor Rateado "0.00") é candidata por regra; o vazio
    # (NAO_RATEADO) só entra por decisão manual do operador (confirmado com o fechamento de 09/2026).
    estados_candidatos: frozenset[EstadoRateio] = frozenset({EstadoRateio.NA_FILA})
    ano_minimo_protocolo: int = 2023  # A1
    custo_minimo_sem_participacao: float = 500.0  # A3
    pct_concentracao: float = 0.10  # A4
    motivos_integrais: frozenset[str] = MOTIVOS_INTEGRAIS  # A5

    # Denominador (6, D2): "VEICULO", "ASSOCIADO" ou "AMBOS" ativos; "TODOS" não filtra.
    # D2 decidido: conta o veículo ativo (docs/REGRAS_RATEIO_AVAP.md, 3.1). Os outros ficam só para comparação.
    criterio_elegibilidade: str = "VEICULO"

    # Split do boleto (9.4)
    taxa_administracao_por_cota: float = 0.0
    produtos_beneficios_por_cota: float = 0.0
    contribuicao_estabilizacao_por_cota: float = 0.0  # D5: 0 até a definição

    # Classificação das linhas sem placa da planilha de rateio (D7): (trecho da descrição, código)
    codigos_soma: tuple[tuple[str, str], ...] = (
        ("E-SAUDE", "E_SAUDE"),
        ("RASTREAMENTO", "RASTREAMENTO"),
        ("INADIMPL", "INADIMPLENCIA"),
    )
    codigos_deducao: tuple[tuple[str, str], ...] = (
        ("SALVADO", "SALVADOS"),
        ("RECEITA INAD", "RECUP_INADIMPLENCIA"),
        ("RECEBIDOS", "RECUP_INADIMPLENCIA"),
    )
    situacoes_pendentes: frozenset[str] = field(default=frozenset({
        "PENDENTE", "PENDENTE REVISTORIA", "PENDENTE ADESÃO", "PENDENTE ADESAO"}))


REGRAS_PADRAO = RegrasAVAP()
