#!/usr/bin/env python3
"""
Roda o motor de rateio sobre os dados simulados e gera as 3 tabelas de SAÍDA em xlsx.
"""
import json
import os
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_DIR = "/home/ronaldim/Mut"
SAIDA_DIR = "/home/ronaldim/Mut/outputs"
os.makedirs(SAIDA_DIR, exist_ok=True)

with open(f"{OUT_DIR}/dados_simulados.json", encoding="utf-8") as f:
    d = json.load(f)

veiculos = d["veiculos"]
eventos  = d["eventos"]
servicos = {s["ID_Veiculo"]: s for s in d["servicos"]}
mes_ref = d["mes_ref"]

# ============================================================
# REGRAS DO MOTOR
# ============================================================
TABELA_COTA = {"ROUBO_FURTO": 14, "MOTO_FIP": 18, "VENTURE_1": 36, "VENTURE_2": 54}
DEGRAUS = [
    ("p1_roubo_furto", 14, ["ROUBO_FURTO", "MOTO_FIP", "VENTURE_1", "VENTURE_2"]),
    ("p2_moto_fip",     4, ["MOTO_FIP", "VENTURE_1", "VENTURE_2"]),
    ("p3_venture_1",   18, ["VENTURE_1", "VENTURE_2"]),
    ("p4_venture_2",   18, ["VENTURE_2"]),
]

# 1) Elegíveis (excluindo funcionários — premissa MVP)
elegiveis = [v for v in veiculos if v["Status_Ativo"] and not v["Is_Funcionario"]]

# 2) Calcula potinhos
cotas_por_tipo = defaultdict(float)
for v in elegiveis:
    cotas_por_tipo[v["Tipo_Categoria_Risco"]] += v["Qtd_Cotas"]

potinhos_resultado = []
alvo_total = 0
for nome, degrau, tipos in DEGRAUS:
    base_cotas = sum(cotas_por_tipo[t] for t in tipos)
    valor = round(base_cotas * degrau, 2)
    alvo_total += valor
    potinhos_resultado.append({
        "potinho": nome, "degrau": degrau, "base_cotas": round(base_cotas, 2), "valor_R$": valor
    })

print("Alvo calculado:", round(alvo_total, 2))

# 3) Aloca eventos: data ASC → valor DESC → ID
eventos_ordenados = sorted(eventos, key=lambda e: (e["Data_Ocorrencia_Evento"], -e["Valor_Saldo_Pendente"], e["ID_Evento"]))
restante = alvo_total
alocados = []
for e in eventos_ordenados:
    if restante <= 0.005:
        break
    usar = round(min(e["Valor_Saldo_Pendente"], restante), 2)
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

# 4) Gera boletos
boletos = []
for v in veiculos:
    rateio = v["Qtd_Cotas"] * TABELA_COTA[v["Tipo_Categoria_Risco"]] if not v["Is_Funcionario"] else 0
    sv = servicos[v["ID_Veiculo"]]
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

# 5) Consolidado
consolidado = {
    "Mes_Ano_Ref": mes_ref,
    "Total_Cotas_Apuradas": round(sum(cotas_por_tipo.values()), 1),
    "Total_Veiculos_Elegiveis": len(elegiveis),
    "Valor_Alvo_Total": round(alvo_total, 2),
    "Valor_P1_Roubo_Furto": potinhos_resultado[0]["valor_R$"],
    "Valor_P2_Moto_FIP":    potinhos_resultado[1]["valor_R$"],
    "Valor_P3_Venture_1":   potinhos_resultado[2]["valor_R$"],
    "Valor_P4_Venture_2":   potinhos_resultado[3]["valor_R$"],
    "Eventos_Alocados":     len(alocados),
    "Eventos_Liquidados":   sum(1 for a in alocados if a["Status_Evento"]=="LIQUIDADO"),
    "Eventos_Parciais":     sum(1 for a in alocados if a["Status_Evento"]=="SALDO_RESTANTE"),
    "Saldo_Para_Proximo_Mes": round(sum(a["Valor_Saldo_Apos"] for a in alocados), 2),
    "Diferenca_Alvo_vs_Alocado": round(alvo_total - sum(a["Valor_Rateado_Neste_Mes"] for a in alocados), 2),
}
print("Consolidado:", json.dumps(consolidado, indent=2, ensure_ascii=False))

# Validação cruzada
soma_boletos = sum(b["Custo_Rateio_Calculado"] for b in boletos if not b["Is_Funcionario"])
print(f"\nSoma rateios em boletos (não-funcionário): R$ {soma_boletos:,.2f}")
print(f"Alvo via potinhos:                          R$ {alvo_total:,.2f}")
print(f"Diferença:                                  R$ {soma_boletos - alvo_total:,.2f}  (deve ser 0)")

# Formatação xlsx
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
    for c in range(1, len(headers)+1):
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

salvar_xlsx(
    f"{SAIDA_DIR}/TB_SAIDA_CONSOLIDADO_ALVO_MES.xlsx",
    "CONSOLIDADO",
    list(consolidado.keys()),
    [consolidado],
    "Retrato consolidado do fechamento do mês — 1 linha por mês de referência.",
)

salvar_xlsx(
    f"{SAIDA_DIR}/TB_SAIDA_EVENTOS_RATEADOS.xlsx",
    "EVENTOS_RATEADOS",
    ["Mes_Ano_Ref","ID_Evento","Data_Ocorrencia_Evento","Valor_Total_Evento","Valor_Saldo_Antes","Valor_Rateado_Neste_Mes","Valor_Saldo_Apos","Status_Evento"],
    alocados,
    "Eventos selecionados pelo motor para preencher o alvo do mês.",
)

salvar_xlsx(
    f"{SAIDA_DIR}/TB_SAIDA_FATURAMENTO_BOLETOS.xlsx",
    "FATURAMENTO",
    ["ID_Veiculo","Mes_Ano_Ref","Tipo_Categoria_Risco","Qtd_Cotas","Custo_Rateio_Calculado","Custo_Produtos_Fixos","Valor_Total_Boleto","Tipo_Pagamento","Is_Funcionario","Gera_Boleto"],
    boletos,
    "Base final enriquecida para emissão de boletos.",
)

gerados = [b for b in boletos if b["Gera_Boleto"]]
isentos = [b for b in boletos if not b["Gera_Boleto"]]
receita = sum(b["Valor_Total_Boleto"] for b in gerados)
print(f"\nBoletos a gerar: {len(gerados):,}")
print(f"Isentos (anual + funcionário): {len(isentos):,}")
print(f"Receita total esperada: R$ {receita:,.2f}")
print(f"Ticket médio: R$ {receita/len(gerados):,.2f}")
print(f"\n3 tabelas TB_SAIDA salvas em {SAIDA_DIR}/")
