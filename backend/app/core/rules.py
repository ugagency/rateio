"""Parâmetros do motor de rateio (LC 213/2025).

Mantemos os 4 potinhos cumulativos como tupla nomeada — alterar valores aqui
muda os degraus globalmente, mas nunca a forma cumulativa do cálculo.
"""

from dataclasses import dataclass

CategoriaRisco = str  # "ROUBO_FURTO" | "MOTO_FIP" | "VENTURE_1" | "VENTURE_2"


@dataclass(frozen=True)
class Degrau:
    nome: str
    valor_por_cota: float
    categorias_que_pagam: tuple[CategoriaRisco, ...]


DEGRAUS_DEFAULT: tuple[Degrau, ...] = (
    Degrau("p1_roubo_furto", 14.0, ("ROUBO_FURTO", "MOTO_FIP", "VENTURE_1", "VENTURE_2")),
    Degrau("p2_moto_fip",     4.0, ("MOTO_FIP", "VENTURE_1", "VENTURE_2")),
    Degrau("p3_venture_1",   18.0, ("VENTURE_1", "VENTURE_2")),
    Degrau("p4_venture_2",   18.0, ("VENTURE_2",)),
)


def tabela_cota_por_categoria(degraus: tuple[Degrau, ...] = DEGRAUS_DEFAULT) -> dict[CategoriaRisco, float]:
    """Soma cumulativa dos degraus que cada categoria paga.

    Ex.: VENTURE_2 = 14 + 4 + 18 + 18 = 54
    """
    todas: set[CategoriaRisco] = set()
    for d in degraus:
        todas.update(d.categorias_que_pagam)
    return {c: round(sum(d.valor_por_cota for d in degraus if c in d.categorias_que_pagam), 2) for c in todas}
