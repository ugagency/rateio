#!/usr/bin/env python3
"""
Motor de Rateio — lê 3 planilhas .xlsx (veiculos, eventos, servicos) e gera
3 tabelas de SAÍDA em xlsx (consolidado, eventos rateados, faturamento boletos).

Uso típico:
    python rodar_motor_rateio.py
    python rodar_motor_rateio.py --mes 06/2025
    python rodar_motor_rateio.py \\
        --veiculos ./inputs/veiculos.xlsx \\
        --eventos  ./inputs/eventos.xlsx \\
        --servicos ./inputs/servicos.xlsx \\
        --mes 05/2025 \\
        --saida ./outputs/

Sem argumentos, lê inputs/{veiculos,eventos,servicos}.xlsx e escreve em outputs/.
"""
import argparse
import os
import sys
from collections import defaultdict
from datetime import date, datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TABELA_COTA = {"ROUBO_FURTO": 14, "MOTO_FIP": 18, "VENTURE_1": 36, "VENTURE_2": 54}
DEGRAUS = [
    ("p1_roubo_furto", 14, ["ROUBO_FURTO", "MOTO_FIP", "VENTURE_1", "VENTURE_2"]),
    ("p2_moto_fip",     4, ["MOTO_FIP", "VENTURE_1", "VENTURE_2"]),
    ("p3_venture_1",   18, ["VENTURE_1", "VENTURE_2"]),
    ("p4_venture_2",   18, ["VENTURE_2"]),
]

COLS_VEICULOS = ["ID_Veiculo", "Status_Ativo", "Data_Quebra", "Tipo_Categoria_Risco",
                 "Qtd_Cotas", "Tipo_Pagamento", "Is_Funcionario"]
COLS_EVENTOS  = ["ID_Evento", "Data_Ocorrencia_Evento", "Valor_Total_Evento",
                 "Valor_Saldo_Pendente", "Faixa_Sim"]
COLS_SERVICOS = ["ID_Veiculo", "Taxa_Administrativa", "Valor_Assistencia_24h",
                 "Valor_Outros_Produtos"]


def _err(msg):
    sys.exit(f"ERRO: {msg}")


def _coerce_bool(v):
    if isinstance(v, bool):
        return v
    if v is None or v == "":
        return False
    s = str(v).strip().lower()
    return s in ("true", "1", "sim", "s", "yes", "y", "verdadeiro", "x")


def _coerce_data(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    return str(v).strip()[:10]


def _coerce_int(v, default=0):
    if v is None or v == "":
        return default
    return int(float(v))


def _coerce_float(v, default=0.0):
    if v is None or v == "":
        return default
    return float(v)


def ler_xlsx(path, cols_obrigatorias, label):
    if not os.path.exists(path):
        _err(f"planilha de {label} não encontrada: {path}")
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = next(rows, None)
    if not headers:
        _err(f"planilha de {label} ({path}) está vazia")
    headers = [str(h).strip() if h is not None else "" for h in headers]
    faltando = [c for c in cols_obrigatorias if c not in headers]
    if faltando:
        _err(
            f"colunas faltando em {label} ({path}): {faltando}\n"
            f"  esperado: {cols_obrigatorias}\n"
            f"  encontrado: {headers}"
        )
    idx = {c: headers.index(c) for c in cols_obrigatorias}
    out = []
    for r in rows:
        if r is None or all(c is None or c == "" for c in r):
            continue
        out.append({c: r[idx[c]] for c in cols_obrigatorias})
    return out


def normalizar(veiculos, eventos, servicos):
    for v in veiculos:
        v["ID_Veiculo"] = str(v["ID_Veiculo"]).strip()
        v["Status_Ativo"] = _coerce_bool(v["Status_Ativo"])
        v["Is_Funcionario"] = _coerce_bool(v["Is_Funcionario"])
        v["Qtd_Cotas"] = _coerce_int(v["Qtd_Cotas"])
        v["Data_Quebra"] = _coerce_data(v["Data_Quebra"])
        v["Tipo_Categoria_Risco"] = str(v["Tipo_Categoria_Risco"]).strip()
        v["Tipo_Pagamento"] = str(v["Tipo_Pagamento"]).strip().upper()
    for e in eventos:
        e["ID_Evento"] = str(e["ID_Evento"]).strip()
        e["Data_Ocorrencia_Evento"] = _coerce_data(e["Data_Ocorrencia_Evento"])
        e["Valor_Total_Evento"] = _coerce_float(e["Valor_Total_Evento"])
        e["Valor_Saldo_Pendente"] = _coerce_float(e["Valor_Saldo_Pendente"])
    for s in servicos:
        s["ID_Veiculo"] = str(s["ID_Veiculo"]).strip()
        s["Taxa_Administrativa"] = _coerce_float(s["Taxa_Administrativa"])
        s["Valor_Assistencia_24h"] = _coerce_float(s["Valor_Assistencia_24h"])
        s["Valor_Outros_Produtos"] = _coerce_float(s["Valor_Outros_Produtos"])


def validar(veiculos, eventos, servicos):
    cats_validas = set(TABELA_COTA.keys())
    cat_invalidas = [v["ID_Veiculo"] for v in veiculos if v["Tipo_Categoria_Risco"] not in cats_validas]
    if cat_invalidas:
        amostra = ", ".join(cat_invalidas[:10])
        _err(
            f"{len(cat_invalidas)} veículo(s) com categoria inválida (esperado {sorted(cats_validas)}). "
            f"Exemplos: {amostra}"
        )

    ids_serv = {s["ID_Veiculo"] for s in servicos}
    sem_serv = [v["ID_Veiculo"] for v in veiculos if v["ID_Veiculo"] not in ids_serv]
    if sem_serv:
        amostra = ", ".join(sem_serv[:10])
        _err(
            f"{len(sem_serv)} veículo(s) sem entrada na planilha de serviços. "
            f"Exemplos: {amostra}"
        )

    ids_evento = [e["ID_Evento"] for e in eventos]
    if len(ids_evento) != len(set(ids_evento)):
        _err("planilha de eventos contém ID_Evento duplicado")


def calcular_potinhos(elegiveis):
    cotas_por_tipo = defaultdict(float)
    for v in elegiveis:
        cotas_por_tipo[v["Tipo_Categoria_Risco"]] += v["Qtd_Cotas"]
    potinhos = []
    alvo_total = 0.0
    for nome, degrau, tipos in DEGRAUS:
        base_cotas = sum(cotas_por_tipo[t] for t in tipos)
        valor = round(base_cotas * degrau, 2)
        alvo_total += valor
        potinhos.append({"potinho": nome, "degrau": degrau, "base_cotas": round(base_cotas, 2), "valor_R$": valor})
    return potinhos, round(alvo_total, 2), cotas_por_tipo


def alocar_eventos(eventos, alvo_total, mes_ref):
    eventos_ord = sorted(
        eventos,
        key=lambda e: (e["Data_Ocorrencia_Evento"] or "", -e["Valor_Saldo_Pendente"], e["ID_Evento"]),
    )
    restante = alvo_total
    alocados = []
    for e in eventos_ord:
        if restante <= 0.005:
            break
        usar = round(min(e["Valor_Saldo_Pendente"], restante), 2)
        if usar <= 0:
            continue
        parcial = usar < e["Valor_Saldo_Pendente"] - 0.005
        alocados.append({
            "Mes_Ano_Ref": mes_ref,
            "ID_Evento": e["ID_Evento"],
            "Data_Ocorrencia_Evento": e["Data_Ocorrencia_Evento"],
            "Valor_Total_Evento": e["Valor_Total_Evento"],
            "Valor_Saldo_Antes": e["Valor_Saldo_Pendente"],
            "Valor_Rateado_Neste_Mes": usar,
            "Valor_Saldo_Apos": round(e["Valor_Saldo_Pendente"] - usar, 2),
            "Status_Evento": "SALDO_RESTANTE" if parcial else "LIQUIDADO",
        })
        restante -= usar
    return alocados


def gerar_boletos(veiculos, servicos_by_id, mes_ref):
    boletos = []
    for v in veiculos:
        rateio = v["Qtd_Cotas"] * TABELA_COTA[v["Tipo_Categoria_Risco"]] if not v["Is_Funcionario"] else 0
        sv = servicos_by_id[v["ID_Veiculo"]]
        fixos = sv["Taxa_Administrativa"] + sv["Valor_Assistencia_24h"] + sv["Valor_Outros_Produtos"]
        total = rateio + fixos
        gera = (not v["Is_Funcionario"]) and v["Tipo_Pagamento"] != "ANUAL"
        boletos.append({
            "ID_Veiculo": v["ID_Veiculo"], "Mes_Ano_Ref": mes_ref,
            "Tipo_Categoria_Risco": v["Tipo_Categoria_Risco"], "Qtd_Cotas": v["Qtd_Cotas"],
            "Custo_Rateio_Calculado": round(rateio, 2),
            "Custo_Produtos_Fixos": round(fixos, 2),
            "Valor_Total_Boleto": round(total, 2),
            "Tipo_Pagamento": v["Tipo_Pagamento"],
            "Is_Funcionario": v["Is_Funcionario"],
            "Gera_Boleto": gera,
        })
    return boletos


# ---------- escrita xlsx ----------
THIN = Side(border_style="thin", color="CCCCCC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HF = PatternFill("solid", start_color="0F172A")
HFB = Font(bold=True, color="FFFFFF", name="Arial", size=11)
CF = Font(name="Arial", size=10)


def salvar_xlsx(path, sheet_name, headers, rows, descricao=""):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    if descricao:
        ws_desc = wb.create_sheet("README")
        ws_desc["A1"] = descricao
        ws_desc["A1"].alignment = Alignment(wrap_text=True)
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = HF; cell.font = HFB
        cell.alignment = Alignment(horizontal="center"); cell.border = BORDER
    for r in rows:
        ws.append([r.get(h) for h in headers])
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(headers)):
        for c in row:
            c.font = CF; c.border = BORDER
    ws.freeze_panes = "A2"
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = max(12, min(35, max_len + 2))
    wb.save(path)


def carregar_dados(inputs_dir, mes_ref="05/2025"):
    """Lê os 3 xlsx de inputs_dir, normaliza, valida e devolve o dict que o
    dashboard consome (mesmo schema antigo de dados_simulados.json)."""
    veiculos = ler_xlsx(os.path.join(inputs_dir, "veiculos.xlsx"), COLS_VEICULOS, "veículos")
    eventos  = ler_xlsx(os.path.join(inputs_dir, "eventos.xlsx"),  COLS_EVENTOS,  "eventos")
    servicos = ler_xlsx(os.path.join(inputs_dir, "servicos.xlsx"), COLS_SERVICOS, "serviços")
    normalizar(veiculos, eventos, servicos)
    validar(veiculos, eventos, servicos)

    elegiveis = [v for v in veiculos if v["Status_Ativo"] and not v["Is_Funcionario"]]
    _potinhos, alvo_total, _cotas = calcular_potinhos(elegiveis)
    total_cotas = sum(v["Qtd_Cotas"] for v in elegiveis)
    por_tipo = {}
    for cat in TABELA_COTA:
        vs = [v for v in elegiveis if v["Tipo_Categoria_Risco"] == cat]
        por_tipo[cat] = {"veiculos": len(vs), "cotas": sum(v["Qtd_Cotas"] for v in vs)}

    return {
        "veiculos": veiculos,
        "eventos": eventos,
        "servicos": servicos,
        "estatisticas": {
            "total_veiculos": len(veiculos),
            "total_cotas": total_cotas,
            "alvo_esperado": round(alvo_total, 2),
            "por_tipo": por_tipo,
        },
        "mes_ref": mes_ref,
    }


def main():
    p = argparse.ArgumentParser(description="Motor de Rateio — lê 3 xlsx e gera 3 xlsx de saída.")
    p.add_argument("--veiculos", default=os.path.join(BASE_DIR, "inputs", "veiculos.xlsx"))
    p.add_argument("--eventos",  default=os.path.join(BASE_DIR, "inputs", "eventos.xlsx"))
    p.add_argument("--servicos", default=os.path.join(BASE_DIR, "inputs", "servicos.xlsx"))
    p.add_argument("--mes", default="05/2025", help="Mês de referência no formato MM/AAAA")
    p.add_argument("--saida", default=os.path.join(BASE_DIR, "outputs"), help="Pasta destino dos xlsx de saída")
    args = p.parse_args()

    print(f"Lendo:")
    print(f"  veiculos: {args.veiculos}")
    print(f"  eventos:  {args.eventos}")
    print(f"  servicos: {args.servicos}")

    veiculos = ler_xlsx(args.veiculos, COLS_VEICULOS, "veículos")
    eventos  = ler_xlsx(args.eventos,  COLS_EVENTOS,  "eventos")
    servicos = ler_xlsx(args.servicos, COLS_SERVICOS, "serviços")

    normalizar(veiculos, eventos, servicos)
    validar(veiculos, eventos, servicos)

    print(f"  → {len(veiculos)} veículos, {len(eventos)} eventos, {len(servicos)} serviços")

    servicos_by_id = {s["ID_Veiculo"]: s for s in servicos}

    elegiveis = [v for v in veiculos if v["Status_Ativo"] and not v["Is_Funcionario"]]
    potinhos, alvo_total, _cotas = calcular_potinhos(elegiveis)
    print(f"\nAlvo calculado: R$ {alvo_total:,.2f}")

    alocados = alocar_eventos(eventos, alvo_total, args.mes)
    boletos = gerar_boletos(veiculos, servicos_by_id, args.mes)

    consolidado = {
        "Mes_Ano_Ref": args.mes,
        "Total_Cotas_Apuradas": round(sum(v["Qtd_Cotas"] for v in elegiveis), 1),
        "Total_Veiculos_Elegiveis": len(elegiveis),
        "Valor_Alvo_Total": alvo_total,
        "Valor_P1_Roubo_Furto": potinhos[0]["valor_R$"],
        "Valor_P2_Moto_FIP":    potinhos[1]["valor_R$"],
        "Valor_P3_Venture_1":   potinhos[2]["valor_R$"],
        "Valor_P4_Venture_2":   potinhos[3]["valor_R$"],
        "Eventos_Alocados":     len(alocados),
        "Eventos_Liquidados":   sum(1 for a in alocados if a["Status_Evento"] == "LIQUIDADO"),
        "Eventos_Parciais":     sum(1 for a in alocados if a["Status_Evento"] == "SALDO_RESTANTE"),
        "Saldo_Para_Proximo_Mes": round(sum(a["Valor_Saldo_Apos"] for a in alocados), 2),
        "Diferenca_Alvo_vs_Alocado": round(alvo_total - sum(a["Valor_Rateado_Neste_Mes"] for a in alocados), 2),
    }

    soma_boletos = sum(b["Custo_Rateio_Calculado"] for b in boletos if not b["Is_Funcionario"])
    diff = round(soma_boletos - alvo_total, 2)
    print(f"Soma rateios em boletos (não-funcionário): R$ {soma_boletos:,.2f}")
    print(f"Alvo via potinhos:                          R$ {alvo_total:,.2f}")
    print(f"Diferença (deve ser 0):                     R$ {diff:,.2f}")
    if abs(diff) > 0.01:
        print("AVISO: invariante alvo == soma_rateios quebrada — investigar.")

    os.makedirs(args.saida, exist_ok=True)
    salvar_xlsx(
        os.path.join(args.saida, "TB_SAIDA_CONSOLIDADO_ALVO_MES.xlsx"),
        "CONSOLIDADO", list(consolidado.keys()), [consolidado],
        "Retrato consolidado do fechamento do mês — 1 linha por mês de referência.",
    )
    salvar_xlsx(
        os.path.join(args.saida, "TB_SAIDA_EVENTOS_RATEADOS.xlsx"),
        "EVENTOS_RATEADOS",
        ["Mes_Ano_Ref", "ID_Evento", "Data_Ocorrencia_Evento", "Valor_Total_Evento",
         "Valor_Saldo_Antes", "Valor_Rateado_Neste_Mes", "Valor_Saldo_Apos", "Status_Evento"],
        alocados,
        "Eventos selecionados pelo motor para preencher o alvo do mês.",
    )
    salvar_xlsx(
        os.path.join(args.saida, "TB_SAIDA_FATURAMENTO_BOLETOS.xlsx"),
        "FATURAMENTO",
        ["ID_Veiculo", "Mes_Ano_Ref", "Tipo_Categoria_Risco", "Qtd_Cotas",
         "Custo_Rateio_Calculado", "Custo_Produtos_Fixos", "Valor_Total_Boleto",
         "Tipo_Pagamento", "Is_Funcionario", "Gera_Boleto"],
        boletos,
        "Base final enriquecida para emissão de boletos.",
    )

    gerados = [b for b in boletos if b["Gera_Boleto"]]
    isentos = [b for b in boletos if not b["Gera_Boleto"]]
    receita = sum(b["Valor_Total_Boleto"] for b in gerados)
    print(f"\nBoletos a gerar: {len(gerados):,}")
    print(f"Isentos (anual + funcionário): {len(isentos):,}")
    print(f"Receita total esperada: R$ {receita:,.2f}")
    if gerados:
        print(f"Ticket médio: R$ {receita/len(gerados):,.2f}")
    print(f"\n3 tabelas TB_SAIDA salvas em {args.saida}/")


if __name__ == "__main__":
    main()
