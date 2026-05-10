"""Repositório Supabase/Postgres — stub para a próxima fase.

Esta classe implementará a mesma interface do `JSONRepository` lendo/escrevendo
no Postgres do Supabase real do cliente. Mantida como placeholder para que a
configuração `RATEIO_REPOSITORY=supabase` falhe explicitamente até integrarmos.
"""

from app.core.domain import (
    Boleto,
    Consolidado,
    Evento,
    EventoRateado,
    ServicoFixo,
    Veiculo,
)


class SupabaseRepository:
    def __init__(self, *, supabase_url: str, service_role_key: str, database_url: str) -> None:
        if not (supabase_url and service_role_key and database_url):
            raise RuntimeError(
                "SupabaseRepository exige SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY e DATABASE_URL configurados."
            )
        self._url = supabase_url
        self._key = service_role_key
        self._db_url = database_url

    async def listar_veiculos(self) -> list[Veiculo]:
        raise NotImplementedError("SupabaseRepository será implementado após validação do schema real do cliente.")

    async def listar_eventos_pendentes(self) -> list[Evento]:
        raise NotImplementedError

    async def listar_servicos(self) -> list[ServicoFixo]:
        raise NotImplementedError

    async def buscar_consolidado(self, mes_ano_ref: str) -> Consolidado | None:
        raise NotImplementedError

    async def listar_eventos_rateados(self, mes_ano_ref: str) -> list[EventoRateado]:
        raise NotImplementedError

    async def listar_boletos(self, mes_ano_ref: str) -> list[Boleto]:
        raise NotImplementedError

    async def existe_rateio(self, mes_ano_ref: str) -> bool:
        raise NotImplementedError

    async def persistir_resultado(
        self,
        *,
        mes_ano_ref: str,
        consolidado: Consolidado,
        eventos_rateados: list[EventoRateado],
        boletos: list[Boleto],
    ) -> None:
        raise NotImplementedError
