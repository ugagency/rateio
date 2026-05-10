"""Teste golden — valida que o motor portado produz o mesmo resultado do script original.

Alvo esperado: R$ 716.964,00 | diff = R$ 0,00 | 26 eventos alocados.
"""

import pytest

from app.repositories.json_repo import JSONRepository
from app.services.rateio_service import RateioService

JSON_PATH = "/home/ronaldim/Mut/dados_simulados.json"


@pytest.fixture
def service() -> RateioService:
    return RateioService(JSONRepository(JSON_PATH))


async def test_alvo_e_diff(service: RateioService) -> None:
    resultado = await service.replay("05/2025")
    assert resultado.consolidado.valor_alvo_total == pytest.approx(716_964.00, abs=0.01)
    assert resultado.consolidado.diferenca_alvo_vs_alocado == pytest.approx(0.00, abs=0.01)


async def test_potinhos(service: RateioService) -> None:
    resultado = await service.replay("05/2025")
    nomes = [p.potinho for p in resultado.potinhos]
    assert nomes == ["p1_roubo_furto", "p2_moto_fip", "p3_venture_1", "p4_venture_2"]
    soma = sum(p.valor for p in resultado.potinhos)
    assert soma == pytest.approx(resultado.consolidado.valor_alvo_total, abs=0.01)


async def test_eventos_rateados(service: RateioService) -> None:
    resultado = await service.replay("05/2025")
    assert resultado.consolidado.eventos_alocados == 26
    assert resultado.consolidado.eventos_liquidados == 25
    assert resultado.consolidado.eventos_parciais == 1


async def test_validacao_cruzada_boletos(service: RateioService) -> None:
    """A soma dos rateios nos boletos (não-funcionário) deve bater com o alvo."""
    resultado = await service.replay("05/2025")
    soma_boletos = round(
        sum(b.custo_rateio_calculado for b in resultado.boletos if not b.is_funcionario),
        2,
    )
    assert soma_boletos == pytest.approx(resultado.consolidado.valor_alvo_total, abs=0.01)


async def test_idempotencia(service: RateioService) -> None:
    """Calcular_e_persistir não deve permitir 2x o mesmo mês sem force=True."""
    from app.services.rateio_service import RateioJaExisteError

    await service.calcular_e_persistir("06/2025")
    with pytest.raises(RateioJaExisteError):
        await service.calcular_e_persistir("06/2025")
    # Com force, sobrescreve sem erro
    await service.calcular_e_persistir("06/2025", force=True)
