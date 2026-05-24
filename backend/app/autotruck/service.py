"""Service layer AutoTruck — orquestra repo + engine + persistência.

Síncrono e isolado (não usa o RateioService do ELLO).
"""

import threading
from typing import Iterable

from .domain import EventoAT, ResultadoRateioAT, SugestaoAjuste, VeiculoAT
from .engine import calcular_rateio_at, sugerir_ajuste
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
            historico_cotas=self.repo.historico_cotas(mes_ano_ref),
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

    def rodar_externos_e_persistir(
        self,
        mes_ano_ref: str,
        veiculos: Iterable[VeiculoAT],
        eventos: Iterable[EventoAT],
        *,
        force: bool = True,
    ) -> ResultadoRateioAT:
        """Roda o engine com veículos+eventos vindos de fora (upload) e
        persiste — não toca no dataset embutido do repo. Sempre force=True
        por default (upload sempre sobrescreve)."""
        with self._lock:
            if not force and self.repo.existe(mes_ano_ref):
                raise AutoTruckJaExisteError(
                    f"Rateio AutoTruck para {mes_ano_ref} já existe. Use force=true para sobrescrever."
                )
            resultado = calcular_rateio_at(
                mes_ano_ref=mes_ano_ref,
                veiculos=veiculos,
                eventos=eventos,
                params=self.params,
                historico_cotas=self.repo.historico_cotas(mes_ano_ref),
            )
            self.repo.persistir(resultado)
            return resultado

    def sugerir_ajuste(
        self,
        mes_ano_ref: str,
        *,
        alvo_cota: float | None = None,
        alvos_cota: dict[str, float] | None = None,
        incluir_parciais: bool = False,
    ) -> list[SugestaoAjuste]:
        """Assistente de ajuste sobre o resultado persistido (ou replay)."""
        resultado = self.repo.buscar(mes_ano_ref) or self.replay(mes_ano_ref)
        return sugerir_ajuste(
            resultado,
            params=self.params,
            alvo_cota=alvo_cota,
            alvos_cota=alvos_cota,
            incluir_parciais=incluir_parciais,
        )

    def aplicar_ajuste(
        self,
        mes_ano_ref: str,
        ids_eventos: list[str],
        *,
        justificativa: str | None = None,
    ) -> ResultadoRateioAT:
        """Posterga os eventos sugeridos (via exclusão com justificativa →
        registrado no audit trail) e re-persiste o fechamento."""
        just = (justificativa or "").strip() or (
            f"Postergado pelo assistente de ajuste (estabilização > FIFO) — "
            f"fechamento {mes_ano_ref}"
        )
        exclusoes = {eid: just for eid in ids_eventos if eid}
        if not exclusoes:
            raise ValueError("Nenhum evento informado para o ajuste.")
        return self.calcular_e_persistir(mes_ano_ref, force=True, exclusoes=exclusoes)
