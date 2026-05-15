"""Service layer AutoTruck — orquestra repo + engine + persistência.

Síncrono e isolado (não usa o RateioService do ELLO).
"""

import threading

from .domain import ResultadoRateioAT
from .engine import calcular_rateio_at
from .repo import AutoTruckRepo
from .rules import PARAMS_DEFAULT, ParametrosAT


class AutoTruckJaExisteError(RuntimeError):
    """Idempotência: rateio AutoTruck já calculado para este mês."""


class AutoTruckService:
    def __init__(self, repo: AutoTruckRepo, params: ParametrosAT = PARAMS_DEFAULT) -> None:
        self.repo = repo
        self.params = params
        self._lock = threading.Lock()

    def replay(
        self, mes_ano_ref: str, exclusoes: dict[str, str] | None = None
    ) -> ResultadoRateioAT:
        return calcular_rateio_at(
            mes_ano_ref=mes_ano_ref,
            veiculos=self.repo.listar_veiculos(),
            eventos=self.repo.listar_eventos(),
            params=self.params,
            exclusoes=exclusoes,
        )

    def calcular_e_persistir(
        self,
        mes_ano_ref: str,
        *,
        force: bool = False,
        exclusoes: dict[str, str] | None = None,
    ) -> ResultadoRateioAT:
        with self._lock:
            if not force and self.repo.existe(mes_ano_ref):
                raise AutoTruckJaExisteError(
                    f"Rateio AutoTruck para {mes_ano_ref} já existe. Use force=true para sobrescrever."
                )
            resultado = self.replay(mes_ano_ref, exclusoes=exclusoes)
            self.repo.persistir(resultado)
            return resultado
