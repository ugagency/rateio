"""Roda o motor portado (app/core/engine.py) contra o JSON simulado e imprime o resultado.

Uso (sem dependências externas):
    python3 backend/scripts/validar_engine.py
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.domain import Evento, ServicoFixo, Veiculo  # noqa: E402
from app.core.engine import calcular_rateio  # noqa: E402

JSON_PATH = "/home/ronaldim/Mut/dados_simulados.json"


def carregar(json_path: str):
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    veiculos = [
        Veiculo(
            id_veiculo=v["ID_Veiculo"],
            status_ativo=v["Status_Ativo"],
            data_quebra=v["Data_Quebra"],
            tipo_categoria_risco=v["Tipo_Categoria_Risco"],
            qtd_cotas=int(v["Qtd_Cotas"]),
            tipo_pagamento=v["Tipo_Pagamento"],
            is_funcionario=v["Is_Funcionario"],
        )
        for v in d["veiculos"]
    ]
    eventos = [
        Evento(
            id_evento=e["ID_Evento"],
            data_ocorrencia=e["Data_Ocorrencia_Evento"],
            valor_total=float(e["Valor_Total_Evento"]),
            valor_saldo_pendente=float(e["Valor_Saldo_Pendente"]),
        )
        for e in d["eventos"]
    ]
    servicos = [
        ServicoFixo(
            id_veiculo=s["ID_Veiculo"],
            taxa_administrativa=float(s["Taxa_Administrativa"]),
            valor_assistencia_24h=float(s["Valor_Assistencia_24h"]),
            valor_outros_produtos=float(s["Valor_Outros_Produtos"]),
        )
        for s in d["servicos"]
    ]
    return veiculos, eventos, servicos, d["mes_ref"]


async def main() -> int:
    veiculos, eventos, servicos, mes_ref = carregar(JSON_PATH)
    resultado = calcular_rateio(
        mes_ano_ref=mes_ref,
        veiculos=veiculos,
        eventos=eventos,
        servicos=servicos,
    )
    c = resultado.consolidado

    print("=" * 60)
    print(f"Mês de referência       : {c.mes_ano_ref}")
    print(f"Veículos elegíveis      : {c.total_veiculos_elegiveis:,}")
    print(f"Cotas apuradas          : {c.total_cotas_apuradas:,.1f}")
    print(f"Alvo total              : R$ {c.valor_alvo_total:,.2f}")
    print(f"P1 Roubo/Furto          : R$ {c.valor_p1_roubo_furto:,.2f}")
    print(f"P2 Moto FIP             : R$ {c.valor_p2_moto_fip:,.2f}")
    print(f"P3 Venture 1            : R$ {c.valor_p3_venture_1:,.2f}")
    print(f"P4 Venture 2            : R$ {c.valor_p4_venture_2:,.2f}")
    print(f"Eventos alocados        : {c.eventos_alocados}")
    print(f"  - liquidados          : {c.eventos_liquidados}")
    print(f"  - parciais            : {c.eventos_parciais}")
    print(f"Saldo p/ próximo mês    : R$ {c.saldo_para_proximo_mes:,.2f}")
    print(f"Diferença alvo×alocado  : R$ {c.diferenca_alvo_vs_alocado:,.2f} (deve ser 0)")
    print("-" * 60)

    boletos_emitir = [b for b in resultado.boletos if b.gera_boleto]
    isentos = [b for b in resultado.boletos if not b.gera_boleto]
    receita = sum(b.valor_total_boleto for b in boletos_emitir)
    print(f"Total de boletos        : {len(resultado.boletos):,}")
    print(f"Boletos a emitir        : {len(boletos_emitir):,}")
    print(f"Isentos (anual+func.)   : {len(isentos):,}")
    print(f"Receita esperada        : R$ {receita:,.2f}")
    if boletos_emitir:
        print(f"Ticket médio            : R$ {receita / len(boletos_emitir):,.2f}")
    print("-" * 60)

    soma_rateios = round(
        sum(b.custo_rateio_calculado for b in resultado.boletos if not b.is_funcionario),
        2,
    )
    diff_cruz = round(soma_rateios - c.valor_alvo_total, 2)
    print(f"Soma rateios em boletos : R$ {soma_rateios:,.2f}")
    print(f"Validação cruzada (Δ)   : R$ {diff_cruz:,.2f} (deve ser 0)")
    print("=" * 60)

    ok = abs(c.diferenca_alvo_vs_alocado) < 0.01 and abs(diff_cruz) < 0.01
    if ok:
        print("OK — motor portado bate com o resultado original.")
        return 0
    print("FALHA — divergência detectada!")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
