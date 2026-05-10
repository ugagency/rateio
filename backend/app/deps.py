"""Dependency injection — fábrica do repositório e do serviço, escolhida por env var."""

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.repositories.base import RateioRepository
from app.repositories.json_repo import JSONRepository
from app.repositories.supabase_repo import SupabaseRepository
from app.services.rateio_service import RateioService


@lru_cache
def _build_repository() -> RateioRepository:
    s = get_settings()
    if s.rateio_repository == "json":
        return JSONRepository(s.rateio_json_path)
    if s.rateio_repository == "supabase":
        return SupabaseRepository(
            supabase_url=s.supabase_url,
            service_role_key=s.supabase_service_role_key,
            database_url=s.database_url,
        )
    raise RuntimeError(f"RATEIO_REPOSITORY desconhecido: {s.rateio_repository}")


def get_repository(_: Settings = Depends(get_settings)) -> RateioRepository:
    return _build_repository()


def get_service(repo: RateioRepository = Depends(get_repository)) -> RateioService:
    return RateioService(repo)
