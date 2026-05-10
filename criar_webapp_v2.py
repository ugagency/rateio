"""
Gera o web app interativo do Motor de Rateio.
"""
import json
import os

OUT_DIR = "/root/projetos/Mut"
DADOS_JSON = os.path.join(OUT_DIR, "dados_simulados.json")
DEST = os.path.join(OUT_DIR, "MotorRateio_Demo.html")

with open(DADOS_JSON, encoding="utf-8") as f:
    dados = json.load(f)

dados_min = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
mes_ref = dados.get("mes_ref", "05/2025")
stats = dados["estatisticas"]
alvo_esperado = stats["alvo_esperado"]

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Motor de Rateio — Demo Investidores</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
</head>
<body class="bg-slate-900 text-slate-200 font-sans">
<header class="border-b border-slate-700 bg-slate-900">
<div class="max-w-7xl mx-auto px-6 py-6">
<h1 class="text-2xl font-bold text-white">Motor de Rateio &amp; Faturamento — Demo MVP</h1>
<p class="text-xs text-slate-400">Sistema Alternativo ao SGA | Mes ref. {mes_ref}</p>
</div>
<nav class="max-w-7xl mx-auto px-6 pb-4 flex gap-2 flex-wrap">
<button data-tab="overview" class="tab-btn px-4 py-2 rounded text-sm font-semibold bg-amber-500 text-slate-900">1. Visão Geral</button>
<button data-tab="potinhos" class="tab-btn px-4 py-2 rounded text-sm font-semibold bg-slate-700">3. Motor Potinhos</button>
<button data-tab="eventos" class="tab-btn px-4 py-2 rounded text-sm font-semibold bg-slate-700">4. Eventos</button>
<button data-tab="boletos" class="tab-btn px-4 py-2 rounded text-sm font-semibold bg-slate-700">5. Boletos</button>
<button data-tab="auditoria" class="tab-btn px-4 py-2 rounded text-sm font-semibold bg-slate-700">6. Auditoria</button>
</nav>
</header>
<main class="max-w-7xl mx-auto px-6 py-8">
<section id="tab-overview" class="tab-content">
<div class="bg-slate-800 rounded-2xl p-10 mb-8 border border-slate-700">
<h2 class="text-4xl font-bold text-white mb-4">O motor de rateio que move R$ {alvo_esperado:,.2f}/mês, em segundos.</h2>
<p class="text-slate-300 text-lg">{stats["total_veiculos"]:,} veículos · {len(dados["eventos"])} eventos · proporciona real da ELLO</p>
</div>
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
<div class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-xs text-slate-400">Veículos ativos</div><div class="text-3xl font-bold text-white mt-2 num" id="kpi-veiculos">{stats["total_veiculos"]:,}</div></div>
<div class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-xs text-slate-400">Total cotas</div><div class="text-3xl font-bold text-white mt-2 num">{stats["total_cotas"]:,.0f}</div></div>
<div class="bg-slate-800 rounded-xl p-6 border border-amber-700"><div class="text-xs text-amber-400">Alvo do mês</div><div class="text-3xl font-bold text-amber-300 mt-2 num">R$ {alvo_esperado:,.2f}</div></div>
<div class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-xs text-slate-400">Eventos</div><div class="text-3xl font-bold text-white mt-2 num">{len(dados["eventos"]):,}</div></div>
</div>
</section>
<section id="tab-potinhos" class="tab-content hidden">
<h2 class="text-2xl font-bold text-white mb-4">Motor: Os 4 Potinhos</h2>
<button id="btn-pot-run" class="px-5 py-2 bg-amber-500 rounded text-sm font-bold text-slate-900 mb-4">▶ Executar Esteira</button>
<div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6" id="potes-grid"></div>
<div class="bg-slate-800 rounded-xl p-6 border border-amber-700">
<div class="text-3xl font-black text-amber-300 num" id="alvo-display">R$ 0,00</div>
</div>
</section>
<section id="tab-eventos" class="tab-content hidden">
<h2 class="text-2xl font-bold text-white mb-4">Alocação de Eventos</h2>
<button id="btn-ev-run" class="px-5 py-2 bg-amber-500 rounded text-sm font-bold text-slate-900 mb-4">▶ Alocar</button>
<div id="ev-resumo" class="text-sm text-slate-300"></div>
</section>
<section id="tab-boletos" class="tab-content hidden">
<h2 class="text-2xl font-bold text-white mb-4">Boletos</h2>
<div id="bol-resumo" class="text-sm"></div>
</section>
<section id="tab-auditoria" class="tab-content hidden">
<h2 class="text-2xl font-bold text-white mb-4">Auditoria</h2>
<input id="audit-input" type="text" placeholder="VEI-000001" class="px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white mb-4"><button id="audit-rand" class="ml-2 px-3 py-2 bg-slate-700 rounded text-xs">Sortear</button>
<div id="audit-out"></div>
</section>
</main>
<script id="dados-json" type="application/json">__DADOS__</script>
<script>
const D=JSON.parse(document.getElementById("dados-json").textContent);
const veiculos=D.veiculos,eventos=D.eventos,servicos=D.servicos;
const svBy=Object.fromEntries(servicos.map(s=>[s["ID_Veiculo"],s]));
const fBRL=v=>"R$ "+(v||0).toLocaleString("pt-BR",{{minimumFractionDigits:2,maximumFractionDigits:2}});
const TC={{ROUBO_FURTO:14,MOTO_FIP:18,VENTURE_1:36,VENTURE_2:54}};
const POTS=[{{i:1,n:"Roubo & Furto",d:14,b:["ROUBO_FURTO","MOTO_FIP","VENTURE_1","VENTURE_2"],c:"slate"}},{{i:2,n:"Moto FIP",d:4,b:["MOTO_FIP","VENTURE_1","VENTURE_2"],c:"blue"}},{{i:3,n:"Venture 1",d:18,b:["VENTURE_1","VENTURE_2"],c:"amber"}},{{i:4,n:"Venture 2",d:18,b:["VENTURE_2"],c:"rose"}}];
const CMAP={{slate:"from-slate-600",blue:"from-blue-700",amber:"from-amber-600",rose:"from-rose-600"}};
function potinhos(){{
const el=veiculos.filter(v=>v.Status_Ativo&&!v.Is_Funcionario);
const ct={{}};for(const v of el)ct[v.Tipo_Categoria_Risco]=(ct[v.Tipo_Categoria_Risco]||0)+v.Qtd_Cotas;
const pts=POTS.map(p=>{{const c=p.b.reduce((a,t)=>a+(ct[t]||0),0);return{{...p,c,v:c*p.d}}}});
return{{pts,alvo:pts.reduce((a,p)=>a+p.v,0)}};
}}
function runPots(){{
const r=potinhos();
document.getElementById("potes-grid").innerHTML=r.pts.map(p=>`<div class="bg-gradient-to-br ${{CMAP[p.c]}} to-slate-800 rounded-xl p-5"><div class="text-xs text-white/70">Pot ${{p.i}}</div><div class="text-white font-bold">${{p.n}}</div><div class="text-2xl text-white font-black mt-2">$${{fBRL(p.v)}}</div><div class="text-xs">${{p.c}} cotas · +R$${{p.d}}/cota</div></div>`).join("");
document.getElementById("alvo-display").textContent=fBRL(r.alvo);
}}
document.getElementById("btn-pot-run").onclick=runPots;runPots();
function runEventos(){{
const r=potinhos();const alvo=r.alvo;
const sorted=[...eventos].sort((a,b)=>a["Data_Ocorrencia_Evento"]<b["Data_Ocorrencia_Evento"]?-1:b["Valor_Saldo_Pendente"]>a["Valor_Saldo_Pendente"]?1:-1);
let rest=alvo;let count=0;
for(const e of sorted){{if(rest<=0.005)break;const u=Math.min(e["Valor_Saldo_Pendente"],rest);rest-=u;count++;}}
document.getElementById("ev-resumo").innerHTML=`<div class="bg-slate-800 p-6 rounded-xl"><b>${{count}}</b> eventos alocados para preencher alvo de <b>${{fBRL(alvo)}}</b>. Fim da alocação.</div>`;
}}
document.getElementById("btn-ev-run").onclick=runEventos;runEventos();
function renderBoletos(){{
const boletos=veiculos.map(v=>{{const rateio=v["Qtd_Cotas"]*(TC[v["Tipo_Categoria_Risco"]]||0);const sv=svBy[v["ID_Veiculo"]]||{{"Taxa_Administrativa":0,"Valor_Assistencia_24h":0,"Valor_Outros_Produtos":0}};const fixos=sv["Taxa_Administrativa"]+sv["Valor_Assistencia_24h"]+sv["Valor_Outros_Produtos"];const gera=!v["Is_Funcionario"]&&v["Tipo_Pagamento"]!=="ANUAL";return{{...v,rateio,fixos,total:rateio+fixos,gera}};}});
const gerados=boletos.filter(b=>b.gera);
const ngerados=boletos.length-gerados.length;
const receita=gerados.reduce((a,b)=>a+b.total,0);
document.getElementById("bol-resumo").innerHTML=`<div class="bg-slate-800 p-6 rounded-xl"><div class="grid grid-cols-4 gap-4"><div><div class="text-slate-400">Gerados</div><div class="text-xl font-bold text-white">${{gerados.length.toLocaleString("pt-BR")}}</div></div><div><div class="text-slate-400">Isentos</div><div class="text-xl font-bold text-amber-300">${{ngerados.toLocaleString("pt-BR")}}</div></div><div><div class="text-slate-400">Receita</div><div class="text-xl font-bold text-emerald-300">${{fBRL(receita)}}</div></div><div><div class="text-slate-400">Ticket</div><div class="text-xl font-bold text-white">${{fBRL(receita/gerados.length)}}</div></div></div></div>`;
}}
renderBoletos();
function audit(id){{const v=veiculos.find(x=>x["ID_Veiculo"]===id);if(!v){{document.getElementById("audit-out").innerHTML="Não encontrado";return}}const sv=svBy[v["ID_Veiculo"]]||{{"Taxa_Administrativa":0,"Valor_Assistencia_24h":0,"Valor_Outros_Produtos":0}};const rateio=v["Qtd_Cotas"]*(TC[v["Tipo_Categoria_Risco"]]||0);const fixos=sv["Taxa_Administrativa"]+sv["Valor_Assistencia_24h"]+sv["Valor_Outros_Produtos"];document.getElementById("audit-out").innerHTML=`<div class="bg-slate-800 p-6 rounded-xl"><div class="text-xl font-bold text-white">${{v["ID_Veiculo"]}} <span class="text-slate-400">${{v["Tipo_Categoria_Risco"]}} · ${{v["Qtd_Cotas"]}} cotas</span></div><div class="mt-4 grid grid-cols-3 gap-4"><div><div class="text-slate-400">Rateio</div><div class="text-white">${{fBRL(rateio)}}</div></div><div><div class="text-slate-400">Fixos</div><div class="text-white">${{fBRL(fixos)}}</div></div><div><div class="text-slate-400">Total</div><div class="text-emerald-300 font-bold">${{fBRL(rateio+fixos)}}</div></div></div></div>`}}
document.getElementById("audit-rand").onclick=()=>{{const v=veiculos[Math.floor(Math.random()*veiculos.length)];document.getElementById("audit-input").value=v["ID_Veiculo"];audit(v["ID_Veiculo"]);}};
document.getElementById("audit-input").addEventListener("input",e=>{{const v=e.target.value;if(v.length>=6)audit(v);}});
document.querySelectorAll(".tab-btn").forEach(t=>t.addEventListener("click",()=>{{
document.querySelectorAll(".tab-content").forEach(c=>c.classList.add("hidden"));
document.querySelectorAll(".tab-btn").forEach(b=>{{b.classList.remove("bg-amber-500","text-slate-900");b.classList.add("bg-slate-700");}});
document.getElementById("tab-"+t.dataset.tab).classList.remove("hidden");
t.classList.add("bg-amber-500","text-slate-900");t.classList.remove("bg-slate-700");
}}));
</script>
</body>
</html>"""

os.makedirs(os.path.dirname(DEST), exist_ok=True)
with open(DEST, 'w', encoding='utf-8') as f:
    f.write(html)

sz = os.path.getsize(DEST)
print(f"HTML gerado: {DEST} ({sz/1024/1024:.2f} MB)")
