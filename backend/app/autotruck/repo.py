"""Repositório AutoTruck — in-memory + JSON próprio (não usa o repo do ELLO).

Carrega `dados_autotruck.json`; se ausente, gera o dataset calibrado em
memória. Persiste resultados por mês na instância (zera a cada restart,
igual ao repo `json` do ELLO).
"""

import json
import os

from .domain import EventoAT, ResultadoRateioAT, VeiculoAT
from .gerar_dados import build_dataset


class AutoTruckRepo:
    def __init__(self, json_path: str) -> None:
        self._path = json_path
        self._ds = self._load()
        self._resultados: dict[str, ResultadoRateioAT] = {}

    def _load(self) -> dict:
        if self._path and os.path.exists(self._path):
            with open(self._path, encoding="utf-8") as fh:
                return json.load(fh)
        return build_dataset()  # fallback determinístico

    @property
    def mes_ref_base(self) -> str:
        return self._ds.get("mes_ref", "12/2025")

    @property
    def alvos(self) -> dict:
        return self._ds.get("alvos", {})

    def listar_veiculos(self) -> list[VeiculoAT]:
        return [VeiculoAT(**v) for v in self._ds.get("veiculos", [])]

    def listar_eventos(self) -> list[EventoAT]:
        return [EventoAT(**e) for e in self._ds.get("eventos", [])]

    # --- persistência em memória ---
    def existe(self, mes_ano_ref: str) -> bool:
        return mes_ano_ref in self._resultados

    def persistir(self, resultado: ResultadoRateioAT) -> None:
        self._resultados[resultado.mes_ano_ref] = resultado

    def buscar(self, mes_ano_ref: str) -> ResultadoRateioAT | None:
        return self._resultados.get(mes_ano_ref)
