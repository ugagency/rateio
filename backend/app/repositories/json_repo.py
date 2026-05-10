"""Repositório de dados em memória, alimentado pelo `dados_simulados.json`.

Para dev e testes locais. Persistência (resultados do motor) é mantida em dicionários
indexados por `mes_ano_ref`, suficiente para o ciclo CRUD da API durante o desenvolvimento.
"""

import json
from pathlib import Path
from threading import Lock

from app.core.domain import (
    Boleto,
    Consolidado,
    Evento,
    EventoRateado,
    ServicoFixo,
    Veiculo,
)


class JSONRepository:
    def __init__(self, json_path: str | Path) -> None:
        self._path = Path(json_path)
        self._lock = Lock()
        self._loaded = False
        self._veiculos: list[Veiculo] = []
        self._eventos: list[Evento] = []
        self._servicos: list[ServicoFixo] = []

        self._consolidados: dict[str, Consolidado] = {}
        self._eventos_rateados: dict[str, list[EventoRateado]] = {}
        self._boletos: dict[str, list[Boleto]] = {}

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            with self._path.open(encoding="utf-8") as f:
                data = json.load(f)
            self._veiculos = [
                Veiculo(
                    id_veiculo=v["ID_Veiculo"],
                    status_ativo=v["Status_Ativo"],
                    data_quebra=v["Data_Quebra"],
                    tipo_categoria_risco=v["Tipo_Categoria_Risco"],
                    qtd_cotas=int(v["Qtd_Cotas"]),
                    tipo_pagamento=v["Tipo_Pagamento"],
                    is_funcionario=v["Is_Funcionario"],
                )
                for v in data["veiculos"]
            ]
            self._eventos = [
                Evento(
                    id_evento=e["ID_Evento"],
                    data_ocorrencia=e["Data_Ocorrencia_Evento"],
                    valor_total=float(e["Valor_Total_Evento"]),
                    valor_saldo_pendente=float(e["Valor_Saldo_Pendente"]),
                )
                for e in data["eventos"]
            ]
            self._servicos = [
                ServicoFixo(
                    id_veiculo=s["ID_Veiculo"],
                    taxa_administrativa=float(s["Taxa_Administrativa"]),
                    valor_assistencia_24h=float(s["Valor_Assistencia_24h"]),
                    valor_outros_produtos=float(s["Valor_Outros_Produtos"]),
                )
                for s in data["servicos"]
            ]
            self._loaded = True

    # ---- Leitura ---------------------------------------------------------

    async def listar_veiculos(self) -> list[Veiculo]:
        self._ensure_loaded()
        return list(self._veiculos)

    async def listar_eventos_pendentes(self) -> list[Evento]:
        self._ensure_loaded()
        return [e for e in self._eventos if e.valor_saldo_pendente > 0]

    async def listar_servicos(self) -> list[ServicoFixo]:
        self._ensure_loaded()
        return list(self._servicos)

    # ---- Saída -----------------------------------------------------------

    async def buscar_consolidado(self, mes_ano_ref: str) -> Consolidado | None:
        return self._consolidados.get(mes_ano_ref)

    async def listar_eventos_rateados(self, mes_ano_ref: str) -> list[EventoRateado]:
        return list(self._eventos_rateados.get(mes_ano_ref, []))

    async def listar_boletos(self, mes_ano_ref: str) -> list[Boleto]:
        return list(self._boletos.get(mes_ano_ref, []))

    async def existe_rateio(self, mes_ano_ref: str) -> bool:
        return mes_ano_ref in self._consolidados

    async def persistir_resultado(
        self,
        *,
        mes_ano_ref: str,
        consolidado: Consolidado,
        eventos_rateados: list[EventoRateado],
        boletos: list[Boleto],
    ) -> None:
        with self._lock:
            self._consolidados[mes_ano_ref] = consolidado
            self._eventos_rateados[mes_ano_ref] = list(eventos_rateados)
            self._boletos[mes_ano_ref] = list(boletos)
            # Atualiza saldo pendente dos eventos consumidos (rateio parcial → próximo mês)
            saldo_apos: dict[str, float] = {er.id_evento: er.valor_saldo_apos for er in eventos_rateados}
            self._eventos = [
                Evento(
                    id_evento=e.id_evento,
                    data_ocorrencia=e.data_ocorrencia,
                    valor_total=e.valor_total,
                    valor_saldo_pendente=saldo_apos.get(e.id_evento, e.valor_saldo_pendente),
                )
                for e in self._eventos
            ]
