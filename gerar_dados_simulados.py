import json, os, random
from datetime import datetime, timedelta

OUT_DIR = "/home/ronaldim/Mut"
os.makedirs(OUT_DIR, exist_ok=True)
random.seed(42)
TOTAL_VEICULOS = 10000
DISTRIBUICAO = {"ROUBO_FURTO": 0.024, "MOTO_FIP": 0.940, "VENTURE_1": 0.032, "VENTURE_2": 0.0017}
veiculos = []
cotas_map = {"ROUBO_FURTO": range(1,11), "MOTO_FIP": range(1,7), "VENTURE_1": range(3,15), "VENTURE_2": range(10,27)}
for cat, frac in DISTRIBUICAO.items():
    n = max(1, int(TOTAL_VEICULOS * frac))
    for i in range(n):
        veiculos.append({"ID_Veiculo": f"VEI-{len(veiculos)+1:06d}", "Status_Ativo": True,
            "Data_Quebra": (datetime(2025,5,1) + timedelta(days=random.randint(-365,0))).strftime("%Y-%m-%d"),
            "Tipo_Categoria_Risco": cat, "Qtd_Cotas": random.choice(cotas_map[cat]),
            "Tipo_Pagamento": random.choice(["MENSAL"]*85+["ANUAL"]*15), "Is_Funcionario": random.random()<0.01})
for i in range(50):
    veiculos.append({"ID_Veiculo": f"VEI-{len(veiculos)+1:06d}", "Status_Ativo": True,
        "Data_Quebra": (datetime(2025,5,1) + timedelta(days=random.randint(-365,0))).strftime("%Y-%m-%d"),
        "Tipo_Categoria_Risco": random.choice(["ROUBO_FURTO","MOTO_FIP"]),
        "Qtd_Cotas": random.randint(1,5), "Tipo_Pagamento": "MENSAL", "Is_Funcionario": True})
eventos = []
data_base = datetime(2025,4,1)
for i in range(500):
    data_ocor = data_base + timedelta(days=random.randint(0,58))
    valor = random.uniform(200, 50000)
    eventos.append({"ID_Evento": f"EV-{i+1:04d}",
        "Data_Ocorrencia_Evento": f"{data_ocor.year:04d}-{data_ocor.month:02d}-{data_ocor.day:02d}",
        "Valor_Total_Evento": round(valor,2), "Valor_Saldo_Pendente": round(valor,2),
        "Faixa_Sim": random.choice(["BAIXO","MEDIO","ALTO"])})
servicos = []
for v in veiculos:
    servicos.append({"ID_Veiculo": v["ID_Veiculo"], "Taxa_Administrativa": 8.90,
        "Valor_Assistencia_24h": random.choice([0,12.50,12.50,19.90]),
        "Valor_Outros_Produtos": random.choice([0,0,0,5.90,9.90])})
stats = {}
for c in DISTRIBUICAO:
    vs = [v for v in veiculos if v["Tipo_Categoria_Risco"]==c and not v["Is_Funcionario"]]
    stats[c] = {"veiculos": len(vs), "cotas": sum(v["Qtd_Cotas"] for v in vs)}
total_cotas = sum(v["Qtd_Cotas"] for v in veiculos if not v["Is_Funcionario"])
alvo = (total_cotas*14 +
    sum(v["Qtd_Cotas"] for v in veiculos if v["Tipo_Categoria_Risco"] in ["MOTO_FIP","VENTURE_1","VENTURE_2"] and not v["Is_Funcionario"])*4 +
    sum(v["Qtd_Cotas"] for v in veiculos if v["Tipo_Categoria_Risco"] in ["VENTURE_1","VENTURE_2"] and not v["Is_Funcionario"])*18 +
    sum(v["Qtd_Cotas"] for v in veiculos if v["Tipo_Categoria_Risco"]=="VENTURE_2" and not v["Is_Funcionario"])*18)
output = {"veiculos": veiculos, "eventos": eventos, "servicos": servicos,
    "estatisticas": {"total_veiculos": len(veiculos), "total_cotas": total_cotas, "alvo_esperado": round(alvo,2), "por_tipo": stats},
    "mes_ref": "05/2025"}
with open(f"{OUT_DIR}/dados_simulados.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False)
print(f"Dados gerados: {len(veiculos)} veículos, {len(eventos)} eventos")
print(f"Cotas elegíveis: {total_cotas:,.0f}")
print(f"Alvo esperado: R$ {alvo:,.2f}")
