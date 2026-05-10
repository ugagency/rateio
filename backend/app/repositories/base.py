"""Protocolo de repositório — qualquer fonte (JSON, Supabase, Postgres) implementa esta interface."""

from typing import Protocol

from app.core.domain import Boleto, Consolidado, Evento, EventoRateado, ServicoFixo, Veiculo


class RateioRepository(Protocol):
    """Porta para leitura de dados de entrada e (opcional) persistência da saída."""

    async def listar_veiculos(self) -> list[Veiculo]: ...

    async def listar_eventos_pendentes(self) -> list[Evento]: ...

    async def listar_servicos(self) -> list[ServicoFixo]: ...

    async def buscar_consolidado(self, mes_ano_ref: str) -> Consolidado | None: ...

    async def listar_eventos_rateados(self, mes_ano_ref: str) -> list[EventoRateado]: ...

    async def listar_boletos(self, mes_ano_ref: str) -> list[Boleto]: ...

    async def persistir_resultado(
        self,
        *,
        mes_ano_ref: str,
        consolidado: Consolidado,
        eventos_rateados: list[EventoRateado],
        boletos: list[Boleto],
    ) -> None: ...

    async def existe_rateio(self, mes_ano_ref: str) -> bool: ...
