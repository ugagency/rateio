import json
import os

# Le os dados gerados
with open("/home/ronaldim/Mut/dados_simulados.json", encoding="utf-8") as f:
    dados = json.load(f)

dados_min = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
mes_ref = dados["mes_ref"]
stats = dados["estatisticas"]

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Motor de Rateio — Demo Investidores</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
body{{font-family:'Inter',system-ui,sans-serif;background:#0f172a;color:#e2e8f0}}
.pot{{transition:all 600ms cubic-bezier(.4,0,.2,1)}}
.pot-ativo{{box-shadow:0 0 0 3px #fbbf24,0 10px 40px rgba(251,191,36,.3);transform:translateY(-4px)}}
.liquid{{background:linear-gradient(180deg,rgba(34,197,94,.85) 0%,rgba(22,163,74,1) 100%);transition:height 1200ms cubic-bezier(.16,1,.3,1)}}
.tab-active{{background:#fbbf24;color:#0f172a}}.tab-idle{{background:#1e293b;color:#cbd5e1}}.tab-idle:hover{{background:#334155}}
.num{{font-variant-numeric:tabular-nums;font-feature-settings:'tnum'}}
.scroll-area{{max-height:420px;overflow:auto;border:1px solid #334155;border-radius:8px}}
.badge{{padding:2px 8px;border-radius:9999px;font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}}
.nota-mvp{{background:rgba(251,191,36,.08);border-left:3px solid #fbbf24;padding:12px;border-radius:4px}}
</style>
</head>
<body>
<header class="border-b border-slate-700 bg-slate-900">
<div class="max-w-7xl mx-auto px-6 py-6">
<h1 class="text-2xl font-bold text-white">Motor de Rateio &amp; Faturamento — Demo MVP</h1>
<p class="text-xs text-slate-400">Sistema Alternativo ao SGA | 10k veículos | Mes ref. <span id="mesRef">{mes_ref}</span></p>
</div>
<nav class="max-w-7xl mx-auto px-6 pb-4 flex gap-2 flex-wrap">
<button data-tab="overview" class="tab-btn px-4 py-2 rounded text-sm font-semibold tab-active">1. Visão Geral</button>
<button data-tab="entrada" class="tab-btn px-4 py-2 rounded text-sm font-semibold tab-idle">2. Dados Entrada</button>
<button data-tab="potinhos" class="tab-btn px-4 py-2 rounded text-sm font-semibold tab-idle">3. Motor — Potinhos</button>
<button data-tab="eventos" class="tab-btn px-4 py-2 rounded text-sm font-semibold tab-idle">4. Alocação Eventos</button>
<button data-tab="boletos" class="tab-btn px-4 py-2 rounded text-sm font-semibold tab-idle">5. Boletos</button>
<button data-tab="auditoria" class="tab-btn px-4 py-2 rounded text-sm font-semibold tab-idle">6. Auditoria</button>
</nav>
</header>
<main class="max-w-7xl mx-auto px-6 py-8">
<section id="tab-overview" class="tab-content">
<div class="bg-slate-800 rounded-2xl p-10 mb-8 border border-slate-700">
<h2 class="text-4xl font-bold text-white mb-4">O motor de rateio que move R$ {stats[alvo_esperado]:,.2f}/mês, em segundos.</h2>
<p class="text-slate-300 text-lg">10.000 veículos · 500 eventos · proporção real da ELLO · roda no navegador sem servidor.</p>
</div>
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
<div class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-xs text-slate-400">Veículos ativos</div><div class="text-3xl font-bold text-white mt-2 num" id="kpi-veiculos"></div></div>
<div class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-xs text-slate-400">Total cotas</div><div class="text-3xl font-bold text-white mt-2 num" id="kpi-cotas"></div></div>
<div class="bg-slate-800 rounded-xl p-6 border border-amber-700"><div class="text-xs text-amber-400">Alvo do mês</div><div class="text-3xl font-bold text-amber-300 mt-2 num" id="kpi-alvo"></div></div>
<div class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-xs text-slate-400">Eventos</div><div class="text-3xl font-bold text-white mt-2 num" id="kpi-eventos"></div></div>
</div>
<div class="nota-mvp text-sm text-slate-300"><strong class="text-amber-300">Premissas MVP:</strong> funcionários fora do rateio; plano anual entra no alvo sem boleto; rateio parcial habilitado.</div>
</section>
<section id="tab-entrada" class="tab-content hidden">
<h2 class="text-2xl font-bold text-white mb-4">Dados de Entrada</h2>
<div id="origem-detalhe" class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-center text-slate-500 py-12">Selecione uma tabela.</div></div>
</section>
<section id="tab-potinhos" class="tab-content hidden">
<div class="flex justify-between mb-6">
<h2 class="text-2xl font-bold text-white">Motor: Os 4 Potinhos</h2>
<div class="flex gap-2">
<button id="btn-pot-reset" class="px-4 py-2 bg-slate-700 rounded text-sm">Reiniciar</button>
<button id="btn-pot-run" class="px-5 py-2 bg-amber-500 rounded text-sm font-bold text-slate-900">▶ Executar Esteira</button>
</div>
</div>
<div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6" id="potes-grid"></div>
<div class="bg-slate-800 rounded-xl p-6 border border-amber-700">
<div class="text-5xl font-black text-amber-300 num" id="alvo-display">R$ 0,00</div>
<div class="mt-4 h-3 bg-slate-900 rounded-full overflow-hidden"><div id="alvo-bar" class="h-full bg-gradient-to-r from-emerald-500 to-amber-400" style="width:0%;transition:width 1s"></div></div>
</div>
</section>
<section id="tab-eventos" class="tab-content hidden">
<h2 class="text-2xl font-bold text-white mb-4">Alocação de Eventos</h2>
<div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
<div class="bg-slate-800 rounded-xl p-4 border border-slate-700"><div class="text-xs text-slate-400">Alvo</div><div class="text-2xl font-bold text-amber-300 num" id="ev-alvo"></div></div>
<div class="bg-slate-800 rounded-xl p-4 border border-emerald-700"><div class="text-xs text-emerald-400">Rateado</div><div class="text-2xl font-bold text-emerald-300 num" id="ev-rateado">R$ 0,00</div></div>
<div class="bg-slate-800 rounded-xl p-4 border border-slate-700"><div class="text-xs text-slate-400">Falta</div><div class="text-2xl font-bold text-white num" id="ev-falta"></div></div>
</div>
<div class="h-4 bg-slate-900 rounded-full overflow-hidden mb-6"><div id="ev-bar" class="h-full bg-gradient-to-r from-emerald-500 to-rose-400" style="width:0%;transition:width .6s"></div></div>
<div class="grid grid-cols-2 gap-4"><div class="bg-slate-800 rounded-xl p-4 border border-slate-700"><div class="text-sm font-semibold mb-2">Fila</div><div id="ev-fila-list" class="scroll-area p-2"></div></div>
<div class="bg-slate-800 rounded-xl p-4 border border-emerald-700"><div class="text-sm font-semibold text-emerald-300 mb-2">Alocados</div><div id="ev-rateado-list" class="scroll-area p-2"></div></div></div>
</section>
<section id="tab-boletos" class="tab-content hidden"><h2 class="text-2xl font-bold text-white mb-4">Boletos Gerados</h2>
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
<div class="bg-slate-800 rounded-xl p-5"><div class="text-xs text-slate-400">Gerados</div><div class="text-xl font-bold text-white num" id="bol-qtd"></div></div>
<div class="bg-slate-800 rounded-xl p-5"><div class="text-xs text-slate-400">Isentos</div><div class="text-xl font-bold text-amber-300 num" id="bol-isentos"></div></div>
<div class="bg-slate-800 rounded-xl p-5"><div class="text-xs text-slate-400">Receita</div><div class="text-xl font-bold text-emerald-300 num" id="bol-receita"></div></div>
<div class="bg-slate-800 rounded-xl p-5"><div class="text-xs text-slate-400">Ticket médio</div><div class="text-xl font-bold text-white num" id="bol-ticket"></div></div>
</div>
<div class="bg-slate-800 rounded-xl p-5 border border-slate-700"><div id="boletos-tabela" class="scroll-area"></div></div>
</section>
<section id="tab-auditoria" class="tab-content hidden"><h2 class="text-2xl font-bold text-white mb-4">Auditoria</h2>
<div class="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
<label>Buscar veículo:</label>
<input id="audit-input" type="text" placeholder="VEI-000123" class="ml-2 px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm">
<button id="audit-rand" class="ml-2 px-3 py-2 bg-slate-700 rounded text-xs">Sortear</button>
</div>
<div id="audit-out" class="text-sm text-slate-400"></div>
</section>
</main>
<script id="dados-json" type="application/json">__DADOS__</script>
<script>
const DADOS=JSON.parse(document.getElementById("dados-json").textContent);
const veiculos=DADOS.veiculos,eventos=DADOS.eventos,servicos=DADOS.servicos;
const svcByVeiculo=Object.fromEntries(servicos.map(s=>[s.ID_Veiculo,s]));
const fmtBRL=v=>"R$ "+(v||0).toLocaleString("pt-BR",{{minimumFractionDigits:2,maximumFractionDigits:2}});
const fmtNum=v=>(v||0).toLocaleString("pt-BR",{{maximumFractionDigits:1}});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const POTINHOS=[{{i:1,nome:"Roubo & Furto",degrau:14,base:["ROUBO_FURTO","MOTO_FIP","VENTURE_1","VENTURE_2"],cor:"from-slate-600 to-slate-700"}},{{i:2,nome:"Moto FIP",degrau:4,base:["MOTO_FIP","VENTURE_1","VENTURE_2"],cor:"from-blue-700 to-blue-800"}},{{i:3,nome:"Venture 1",degrau:18,base:["VENTURE_1","VENTURE_2"],cor:"from-amber-600 to-amber-700"}},{{i:4,nome:"Venture 2",degrau:18,base:["VENTURE_2"],cor:"from-rose-600 to-rose-700"}}];
const TAB_COTA={{ROUBO_FURTO:14,MOTO_FIP:18,VENTURE_1:36,VENTURE_2:54}};
document.getElementById("kpi-veiculos").textContent=(DADOS.estatisticas.total_veiculos||0).toLocaleString("pt-BR");
document.getElementById("kpi-cotas").textContent=fmtNum(DADOS.estatisticas.total_cotas);
document.getElementById("kpi-alvo").textContent=fmtBRL(DADOS.estatisticas.alvo_esperado);
document.getElementById("kpi-eventos").textContent=(eventos.length||0).toLocaleString("pt-BR");
function calcularPotinhos(){{
const elegiveis=veiculos.filter(v=>v.Status_Ativo&&!v.Is_Funcionario);
const cotasTipo={{}};for(const v of elegiveis)cotasTipo[v.Tipo_Categoria_Risco]=(cotasTipo[v.Tipo_Categoria_Risco]||0)+v.Qtd_Cotas;
const potes=POTINHOS.map(p=>{{const c=p.base.reduce((a,t)=>a+(cotasTipo[t]||0),0);return{{...p,cotasBase:c,valor:c*p.degrau,corBase:cotasTipo}}}});
return{{potes,alvo:potes.reduce((a,p)=>a+p.valor,0),cotasPorTipo:cotasTipo}};
}}
function renderPotes(potes,ativoIdx=-1,alvoAcum=0){{
document.getElementById("potes-grid").innerHTML=potes.map((p,i)=>`<div class="pot bg-gradient-to-br ${{p.cor}} rounded-xl p-5 border border-slate-700 ${{i===ativoIdx?'pot-ativo':''}}"><div class="text-xs text-white/70">Potinho ${{p.i}}</div><div class="text-white font-bold">${{p.nome}}</div><div class="mt-3 bg-black/30 rounded h-24 flex items-end overflow-hidden"><div class="liquid w-full" style="height:${{i<ativoIdx||i===ativoIdx?100:0}}%"></div></div><div class="mt-3 text-xs"><div>Base: <b>${{fmtNum(p.cotasBase)}}</b> cotas</div><div>Alvo: <b>${{fmtBRL(p.valor)}}</b></div></div></div>`).join("");
document.getElementById("alvo-display").textContent=fmtBRL(alvoAcum);
const tot=potes.reduce((a,p)=>a+p.valor,0);
document.getElementById("alvo-bar").style.width= Math.min(100,(alvoAcum/tot)*100)+"%";
}}
async function executarPotinhos(){{
const r=calcularPotinhos();
renderPotes(r.potes,-1,0);
let acum=0;
for(let i=0;i<r.potes.length;i++){{
renderPotes(r.potes,i,acum);
await sleep(900);
acum+=r.potes[i].valor;
renderPotes(r.potes,i,acum);
await sleep(400);
}}
}}
async function alocarEventos(){{
const r=calcularPotinhos();
const alvo=r.alvo;
document.getElementById("ev-alvo").textContent=fmtBRL(alvo);
document.getElementById("ev-falta").textContent=fmtBRL(alvo);
const ordem=[...eventos].sort((a,b)=>{{if(a.Data_Ocorrencia_Evento!==b.Data_Ocorrencia_Evento)return a.Data_Ocorrencia_Evento<b.Data_Ocorrencia_Evento?-1:1;return b.Valor_Saldo_Pendente-a.Valor_Saldo_Pendente;}});
let restante=alvo;const alocados=[],filasIds={{}};
document.getElementById("ev-fila-list").innerHTML="";
document.getElementById("ev-rateado-list").innerHTML="";
for(const e of ordem){{
if(restante<=0.005)break;
const usar=Math.round(Math.min(e.Valor_Saldo_Pendente,restante)*100)/100;
const parcial=usar<e.Valor_Saldo_Pendente-0.005;
alocados.push({{...e,Valor_Rateado_Neste_Mes:usar,Status_Evento:parcial?"SALDO_RESTANTE":"LIQUIDADO",Saldo_Apos:Math.round((e.Valor_Saldo_Pendente-usar)*100)/100}});
filasIds[e.ID_Evento]=parcial?"PARCIAL":"TOTAL";
restante-=usar;
const acum=alvo-restante;
document.getElementById("ev-rateado").textContent=fmtBRL(acum);
document.getElementById("ev-falta").textContent=fmtBRL(Math.max(0,alvo-acum));
document.getElementById("ev-bar").style.width=Math.min(100,(acum/alvo)*100)+"%";
document.getElementById("ev-fila-list").innerHTML=ordem.slice(0,60).map(ev=>`<div class="ev-fila border rounded p-2 text-xs mb-1" style="background:${{filasIds[ev.ID_Evento]==="TOTAL"?"#064e3b":filasIds[ev.ID_Evento]==="PARCIAL"?"#78350f":"#1e293b"}}"><div class="flex justify-between"><span class="font-bold text-white">${{ev.ID_Evento}}</span><span class="badge bg-black/40 text-white">${{filasIds[ev.ID_Evento]||"FILA"}}</span></div><div class="text-slate-300 mt-1">${{ev.Data_Ocorrencia_Evento}} · <b>${{fmtBRL(ev.Valor_Saldo_Pendente)}}</b></div></div>`).join("");
document.getElementById("ev-rateado-list").innerHTML=alocados.slice(-30).map(a=>`<div class="border rounded p-2 text-xs mb-1" style="background:${{a.Status_Evento==="LIQUIDADO"?"#064e3b":"#78350f"}}"><div class="flex justify-between"><span class="font-bold text-white">${{a.ID_Evento}}</span><span class="badge bg-black/40 text-white">${{a.Status_Evento}}</span></div><div class="text-slate-300 mt-1">${{fmtBRL(a.Valor_Rateado_Neste_Mes)}}</div></div>`).join("");
await sleep(100);
}}
}}
function renderBoletos(){{
const boletos=veiculos.map(v=>{{
const rateio=v.Qtd_Cotas*(TAB_COTA[v.Tipo_Categoria_Risco]||0);
const sv=svcByVeiculo[v.ID_Veiculo]||{{Taxa_Administrativa:0,Valor_Assistencia_24h:0,Valor_Outros_Produtos:0}};
const fixos=sv.Taxa_Administrativa+sv.Valor_Assistencia_24h+sv.Valor_Outros_Produtos;
return{{...v,Custo_Rateio:rateio,Custo_Fixos:fixos,Valor_Total_Boleto:rateio+fixos,Gera_Boleto:!v.Is_Funcionario&&v.Tipo_Pagamento!=="ANUAL"}};
}});
const gerados=boletos.filter(b=>b.Gera_Boleto);
const isentos=boletos.length-gerados.length;
const receita=gerados.reduce((a,b)=>a+b.Valor_Total_Boleto,0);
document.getElementById("bol-qtd").textContent=gerados.length.toLocaleString("pt-BR");
document.getElementById("bol-isentos").textContent=isentos.toLocaleString("pt-BR");
document.getElementById("bol-receita").textContent=fmtBRL(receita);
document.getElementById("bol-ticket").textContent=fmtBRL(receita/gerados.length);
document.getElementById("boletos-tabela").innerHTML=gerados.slice(0,50).map(b=>`<div class="flex justify-between border-b border-slate-700 py-1 text-sm"><span class="text-slate-200">${{b.ID_Veiculo}}</span><span class="text-slate-300">${{b.Tipo_Categoria_Risco}} · ${{b.Qtd_Cotas}} cotas</span><span class="text-white font-bold num">${{fmtBRL(b.Valor_Total_Boleto)}}</span></div>`).join("");
}}
function renderAudit(id){{
const v=veiculos.find(x=>x.ID_Veiculo===id);
if(!v){{document.getElementById("audit-out").innerHTML="Não encontrado";return;}}
const sv=svcByVeiculo[v.ID_Veiculo]||{{Taxa_Administrativa:0,Valor_Assistencia_24h:0,Valor_Outros_Produtos:0}};
const rateio=v.Qtd_Cotas*(TAB_COTA[v.Tipo_Categoria_Risco]||0);
const fixos=sv.Taxa_Administrativa+sv.Valor_Assistencia_24h+sv.Valor_Outros_Produtos;
document.getElementById("audit-out").innerHTML=`<div class="bg-slate-800 rounded-xl p-6 border border-slate-700"><div class="text-xl font-bold text-white">${{v.ID_Veiculo}} <span class="text-sm text-slate-400">${{v.Tipo_Categoria_Risco}} · ${{v.Qtd_Cotas}} cotas · ${{v.Tipo_Pagamento}}</span></div><div class="mt-4 grid grid-cols-3 gap-4 text-sm"><div><div class="text-slate-400">Rateio</div><div class="text-white">${{fmtBRL(rateio)}}</div></div><div><div class="text-slate-400">Fixos</div><div class="text-white">${{fmtBRL(fixos)}}</div></div><div><div class="text-slate-400">Total</div><div class="text-emerald-300 font-bold">${{fmtBRL(rateio+fixos)}}</div></div></div></div>`;
}}
document.querySelectorAll(".tab-btn").forEach(t=>t.addEventListener("click",()=>{{
document.querySelectorAll(".tab-content").forEach(c=>c.classList.add("hidden"));
document.querySelectorAll(".tab-btn").forEach(b=>{{b.classList.remove("tab-active");b.classList.add("tab-idle");}});
document.getElementById("tab-"+t.dataset.tab).classList.remove("hidden");
t.classList.add("tab-active");t.classList.remove("tab-idle");
if(t.dataset.tab==="potinhos")executarPotinhos().then(()=>{{document.getElementById("btn-pot-reset").onclick=()=>{{const r=calcularPotinhos();renderPotes(r.potes,-1,0);}};}});
if(t.dataset.tab==="eventos")alocarEventos();
if(t.dataset.tab==="boletos")renderBoletos();
}}));
document.getElementById("btn-pot-run").addEventListener("click",executarPotinhos);
document.getElementById("audit-rand").addEventListener("click",()=>{{const v=veiculos[Math.floor(Math.random()*veiculos.length)];document.getElementById("audit-input").value=v.ID_Veiculo;renderAudit(v.ID_Veiculo);}});
document.getElementById("audit-input").addEventListener("input",e=>{{const v=e.target.value.trim();if(v.length>=6)renderAudit(v);}});
</script>
</body>
</html>"""

# Salva
os.makedirs(os.path.dirname(DEST), exist_ok=True)
with open(DEST, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML gerado: {{os.path.getsize(DEST)/1024/1024:.2f}} MB em {{DEST}}')
