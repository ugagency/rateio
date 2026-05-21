"""Service layer — orquestra leitura, motor e persistência."""

import asyncio
from typing import Iterable

from app.core.domain import Evento, ResultadoRateio, ServicoFixo, Veiculo
from app.core.engine import calcular_rateio
from app.repositories.base import RateioRepository


class RateioJaExisteError(RuntimeError):
    """Idempotência: rateio já calculado para este mês."""


class RateioService:
    def __init__(self, repo: RateioRepository) -> None:
        self.repo = repo
        self._lock = asyncio.Lock()  # 1 cálculo por vez na instância

    async def replay(self, mes_ano_ref: str) -> ResultadoRateio:
        veiculos, eventos, servicos = await asyncio.gather(
            self.repo.listar_veiculos(),
            self.repo.listar_eventos_pendentes(),
            self.repo.listar_servicos(),
        )
        return calcular_rateio(
            mes_ano_ref=mes_ano_ref,
            veiculos=veiculos,
            eventos=eventos,
            servicos=servicos,
        )

    async def rodar_externos_e_persistir(
        self,
        mes_ano_ref: str,
        veiculos: Iterable[Veiculo],
        eventos: Iterable[Evento],
        servicos: Iterable[ServicoFixo],
        *,
        force: bool = True,
    ) -> ResultadoRateio:
        """Roda o motor com dados vindos de fora (upload) e persiste —
        não toca no dataset carregado pelo repo. Sempre force=True por
        default (upload sempre sobrescreve)."""
        async with self._lock:
            if not force and await self.repo.existe_rateio(mes_ano_ref):
                raise RateioJaExisteError(
                    f"Rateio para {mes_ano_ref} já existe. Use force=true para sobrescrever."
                )
            resultado = calcular_rateio(
                mes_ano_ref=mes_ano_ref,
                veiculos=list(veiculos),
                eventos=list(eventos),
                servicos=list(servicos),
            )
            await self.repo.persistir_resultado(
                mes_ano_ref=mes_ano_ref,
                consolidado=resultado.consolidado,
                eventos_rateados=resultado.eventos_rateados,
                boletos=resultado.boletos,
            )
            return resultado

    async def calcular_e_persistir(self, mes_ano_ref: str, *, force: bool = False) -> ResultadoRateio:
        async with self._lock:
            if not force and await self.repo.existe_rateio(mes_ano_ref):
                raise RateioJaExisteError(
                    f"Rateio para {mes_ano_ref} já existe. Use force=true para sobrescrever."
                )
            resultado = await self.replay(mes_ano_ref)
            await self.repo.persistir_resultado(
                mes_ano_ref=mes_ano_ref,
                consolidado=resultado.consolidado,
                eventos_rateados=resultado.eventos_rateados,
                boletos=resultado.boletos,
            )
            return resultado
