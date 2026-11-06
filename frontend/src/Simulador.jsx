import { useState } from 'react'
import './Simulador.css'

// Simulador rápido da Fenaprove, em três passos: 1) dados do contato, 2) quatro perguntas com faixas,
// 3) versão simplificada do rateio. Mesma fórmula do pote único da AVAP:
// valor da cota = (eventos + somas - deduções) / cotas dos veículos ativos. Aqui somas e deduções valem zero.
// Cada faixa vale pelo seu ponto médio, então o resultado é uma estimativa, e a tela diz isso.
// O contato vai ao backend (/avap/simulador/lead) já no passo 1, e a mesma linha é atualizada no passo 3.

const brl = (v) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const num = (v) => Math.round(v).toLocaleString('pt-BR')
const R_POR_COTA_FIPE = 5000 // regra da AVAP: 1 cota a cada R$ 5 mil de FIPE

// Faixas: [texto mostrado, valor usado na conta (ponto médio)]. Para mudar as faixas, basta editar aqui.
const VEICULOS = [["Até 1.000", 700], ["1.001 a 3.000", 2000], ["3.001 a 5.000", 4000], ["5.001 a 10.000", 7500],
  ["10.001 a 20.000", 15000], ["20.001 a 40.000", 30000], ["Mais de 40.000", 50000]]
const FIPE = [["Até R$ 30 mil", 25000], ["R$ 30 a 60 mil", 45000], ["R$ 60 a 100 mil", 80000],
  ["R$ 100 a 200 mil", 150000], ["Acima de R$ 200 mil", 250000]]
const EVENTOS = [["Até 10", 6], ["11 a 25", 18], ["26 a 50", 38], ["51 a 100", 75], ["101 a 200", 150], ["Mais de 200", 250]]
const CUSTO = [["Até R$ 5 mil", 3000], ["R$ 5 a 10 mil", 7500], ["R$ 10 a 20 mil", 15000],
  ["R$ 20 a 40 mil", 30000], ["Acima de R$ 40 mil", 50000]]

const PERGUNTAS = [
  { k: "veiculos", titulo: "Quantos veículos ativos a associação tem?", faixas: VEICULOS },
  { k: "fipe", titulo: "Qual o valor médio dos veículos (tabela FIPE)?", dica: "Usamos 1 cota a cada R$ 5 mil de FIPE, a regra da AVAP.", faixas: FIPE },
  { k: "eventos", titulo: "Quantos eventos entraram no rateio no último mês?", faixas: EVENTOS },
  { k: "custo", titulo: "Qual o custo médio de cada evento?", faixas: CUSTO },
]

const MODELOS = [
  "Pote único (todos dividem o mesmo total)",
  "Por categoria ou segmento (leves, motos, pesados)",
  "Potes separados que se somam",
  "Valor fixo por veículo",
  "Não sei dizer",
]
const CARGOS = ["Presidente ou diretor", "Gestor", "Financeiro", "Operacional", "Outro"]
const SISTEMAS = ["SGA (Hinova)", "Outro sistema", "Planilha", "Não sei"]
const QUEM_FAZ = ["Equipe interna em planilha", "Sistema", "Empresa terceirizada", "Não sei"]

const CONTATO_VAZIO = {
  nome: "", whatsapp: "", email: "", associacao: "", cargo: "", sistema_gestao: "",
  rateio_hoje: "", modelo: null, quer_versao: null, consentimento: false,
}
const SEL_VAZIA = { veiculos: null, fipe: null, eventos: null, custo: null }

const novoId = () => "L" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10)

function guardarPendente(lead) {
  try {
    const fila = JSON.parse(localStorage.getItem("mut_leads_pendentes") || "[]")
    fila.push(lead)
    localStorage.setItem("mut_leads_pendentes", JSON.stringify(fila))
    return true
  } catch { return false }
}
async function enviar(lead) {
  const r = await fetch("/avap/simulador/lead", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(lead),
  })
  if (!r.ok) {
    const j = await r.json().catch(() => ({}))
    const e = new Error(typeof j.detail === 'string' ? j.detail : "Falha ao registrar")
    e.validacao = r.status === 422
    throw e
  }
  return r.json()
}
// Reenvia o que ficou guardado neste computador. O servidor atualiza pela mesma id, então a ordem não estraga nada.
async function reenviarPendentes() {
  let fila
  try { fila = JSON.parse(localStorage.getItem("mut_leads_pendentes") || "[]") } catch { return }
  const sobra = []
  for (const l of fila) { try { await enviar(l) } catch { sobra.push(l) } }
  try { localStorage.setItem("mut_leads_pendentes", JSON.stringify(sobra)) } catch { /* sem armazenamento */ }
}

function calcular(s) {
  if (PERGUNTAS.some(({ k }) => s[k] === null)) return null
  const veiculos = VEICULOS[s.veiculos][1]
  const cotasPorVeiculo = FIPE[s.fipe][1] / R_POR_COTA_FIPE
  const cotasTotal = veiculos * cotasPorVeiculo
  const eventosQtd = EVENTOS[s.eventos][1]
  const eventosValor = eventosQtd * CUSTO[s.custo][1]
  const valorCota = eventosValor / cotasTotal
  return { veiculos, cotasPorVeiculo, cotasTotal, eventosQtd, eventosValor, valorCota, rateioMedio: cotasPorVeiculo * valorCota }
}

export default function Simulador({ equipe = false }) {
  const [passo, setPasso] = useState("contato")
  const [id, setId] = useState(novoId)
  const [c, setC] = useState(CONTATO_VAZIO)
  const [s, setS] = useState(SEL_VAZIA)
  const [erro, setErro] = useState("")
  const [aviso, setAviso] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [leads, setLeads] = useState(null)
  const r = calcular(s)
  const setc = (k) => (e) => { setErro(""); setC({ ...c, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }) }
  const escolherC = (k, valor) => { setErro(""); setC({ ...c, [k]: valor }) }
  const escolherS = (k, i) => { setErro(""); setS({ ...s, [k]: i }) }

  const montarLead = (etapa, simulacao = {}) => ({
    id, etapa, nome: c.nome.trim(), whatsapp: c.whatsapp.trim(), email: c.email.trim(),
    associacao: c.associacao.trim(), cargo: c.cargo, sistema_gestao: c.sistema_gestao,
    rateio_hoje: c.rateio_hoje, modelo_rateio: c.modelo === null ? "" : MODELOS[c.modelo],
    quer_versao: c.quer_versao === true, consentimento: c.consentimento, simulacao,
  })

  // Grava (ou atualiza) o contato. Sem conexão com o servidor, guarda neste computador e reenvia depois.
  const salvar = async (lead) => {
    try {
      await enviar(lead)
      setAviso("")
      reenviarPendentes()
    } catch (e) {
      if (e.validacao) throw e
      setAviso(guardarPendente(lead)
        ? "Sem conexão com o servidor: o contato ficou guardado neste computador e será enviado na próxima vez."
        : "Não foi possível registrar o contato. Anote os dados manualmente.")
    }
  }

  const continuar = async () => {
    if (c.nome.trim().length < 2) return setErro("Informe seu nome.")
    if (c.whatsapp.replace(/\D/g, "").length < 10) return setErro("Informe o WhatsApp com DDD.")
    if (c.quer_versao === null) return setErro("Diga se quer receber a versão simplificada do rateio da sua associação.")
    if (!c.consentimento) return setErro("Para continuar, marque a autorização de contato.")
    setErro(""); setEnviando(true)
    try { await salvar(montarLead("contato")) } catch (e) { setEnviando(false); return setErro(e.message) }
    setEnviando(false); setPasso("simulacao")
  }

  const simular = () => {
    if (!r) return setErro("Responda as quatro perguntas para simular.")
    setErro(""); setPasso("resultado")
    salvar(montarLead("resultado", {
      faixa_veiculos: VEICULOS[s.veiculos][0], faixa_fipe: FIPE[s.fipe][0],
      faixa_eventos: EVENTOS[s.eventos][0], faixa_custo: CUSTO[s.custo][0],
      veiculos_ativos: r.veiculos, cotas_total: Math.round(r.cotasTotal), eventos_qtd: r.eventosQtd,
      eventos_valor: r.eventosValor.toFixed(2), valor_cota: r.valorCota.toFixed(4),
    })).catch((e) => setErro(e.message))
  }

  const novoAtendimento = () => {
    setC(CONTATO_VAZIO); setS(SEL_VAZIA); setId(novoId()); setErro(""); setAviso(""); setPasso("contato")
  }
  const verLeads = async () => {
    try { setLeads(await (await fetch("/avap/simulador/leads")).json()) } catch { setLeads({ erro: true }) }
  }

  return (
    <div className="mut-sim">
      <header className="mut-hero">
        <div className="max-w-5xl mx-auto px-6 py-6">
          {/* Logo: trocar o texto abaixo por <img src="/logo-mutualiza.svg" alt="Mutualiza" /> quando o arquivo oficial chegar */}
          <div className="mut-eyebrow">Mutualiza · Simulador rápido · Fenaprove 2026</div>
          <h1 className="mut-title mt-1">Quanto daria o rateio da sua associação</h1>
          <div className="flex gap-2 mt-4 text-xs">
            {[["contato", "1. Seus dados"], ["simulacao", "2. Simulação"], ["resultado", "3. Resultado"]].map(([k, l]) => (
              <span key={k} className="mut-passo" data-ativo={passo === k}>{l}</span>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {erro && <div className="mut-erro mb-4">{erro}</div>}

        {passo === "contato" && (
          <div className="space-y-6 max-w-4xl">
            <p className="mut-intro">Primeiro, alguns dados para a gente saber com quem está falando. Depois é só escolher faixas, sem digitar números.</p>
            <Grupo titulo="Seus dados">
              <Campo rotulo="Nome" obrig><Txt value={c.nome} onChange={setc("nome")} /></Campo>
              <Campo rotulo="WhatsApp com DDD" obrig><Txt value={c.whatsapp} onChange={setc("whatsapp")} placeholder="(31) 9...." inputMode="tel" /></Campo>
              <Campo rotulo="E-mail (opcional)"><Txt value={c.email} onChange={setc("email")} inputMode="email" /></Campo>
              <Campo rotulo="Associação"><Txt value={c.associacao} onChange={setc("associacao")} /></Campo>
              <Campo rotulo="Cargo"><Sel value={c.cargo} onChange={setc("cargo")} opcoes={CARGOS} /></Campo>
              <Campo rotulo="Sistema de gestão"><Sel value={c.sistema_gestao} onChange={setc("sistema_gestao")} opcoes={SISTEMAS} /></Campo>
            </Grupo>
            <Grupo titulo="Como a associação faz o rateio hoje?">
              <div className="md:col-span-3 space-y-4">
                <Opcoes opcoes={MODELOS} valor={c.modelo} onChange={(i) => escolherC("modelo", i)} />
                <Campo rotulo="Quem faz o rateio hoje"><Sel value={c.rateio_hoje} onChange={setc("rateio_hoje")} opcoes={QUEM_FAZ} /></Campo>
              </div>
            </Grupo>
            <Grupo titulo="Quer receber uma versão simplificada do rateio da sua associação?" obrig>
              <div className="md:col-span-3">
                <Opcoes opcoes={["Sim, quero receber no WhatsApp", "Agora não"]}
                  valor={c.quer_versao === null ? null : (c.quer_versao ? 0 : 1)}
                  onChange={(i) => escolherC("quer_versao", i === 0)} />
              </div>
            </Grupo>
            <label className="mut-consentimento flex gap-3 items-start">
              <input type="checkbox" className="mt-1" checked={c.consentimento} onChange={setc("consentimento")} />
              <span>Autorizo o contato sobre este resultado e a guarda destes dados para esse fim. Posso pedir a exclusão a qualquer momento.</span>
            </label>
            <button onClick={continuar} disabled={enviando} className="mut-botao">{enviando ? "Registrando…" : "Continuar para a simulação"}</button>
          </div>
        )}

        {passo === "simulacao" && (
          <div className="space-y-6">
            <p className="mut-intro">Quatro perguntas, é só tocar na faixa mais próxima da realidade da associação.</p>
            {PERGUNTAS.map(({ k, titulo, dica, faixas }) => (
              <Grupo key={k} titulo={titulo} obrig>
                <div className="md:col-span-3 space-y-2">
                  <Opcoes opcoes={faixas.map(([l]) => l)} valor={s[k]} onChange={(i) => escolherS(k, i)} />
                  {dica && <span className="mut-dica">{dica}</span>}
                </div>
              </Grupo>
            ))}
            {aviso && <div className="mut-aviso">{aviso}</div>}
            <div className="flex gap-3">
              <button onClick={simular} disabled={!r} className="mut-botao">Simular o rateio</button>
              <button onClick={() => { setErro(""); setPasso("contato") }} className="mut-botao-sec">Voltar</button>
            </div>
          </div>
        )}

        {passo === "resultado" && r && (
          <div className="space-y-6">
            <div className="mut-destaque">
              <div className="mut-eyebrow">Valor estimado por cota</div>
              <div className="mut-destaque-valor">{brl(r.valorCota)}</div>
              <div className="mut-destaque-sub">
                {brl(r.eventosValor)} de eventos dividido por {num(r.cotasTotal)} cotas de cerca de {num(r.veiculos)} veículos ativos
              </div>
            </div>
            <div className="grid md:grid-cols-4 gap-3">
              <Card rotulo="Eventos do mês (estimado)" valor={brl(r.eventosValor)} sub={`${num(r.eventosQtd)} eventos no mês`} />
              <Card rotulo="Veículos ativos" valor={VEICULOS[s.veiculos][0]} sub="faixa informada" />
              <Card rotulo="Cotas estimadas" valor={num(r.cotasTotal)} sub={`${r.cotasPorVeiculo.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} cotas por veículo`} />
              <Card rotulo="Rateio do veículo médio" valor={brl(r.rateioMedio)} sub="por mês" />
            </div>
            <div className="mut-nota">
              {c.modelo !== null && c.modelo !== 0
                ? "Sua associação usa outro modelo de rateio. Além do pote único, temos motores para potes que se somam e para rateio por segmento, adaptáveis à regra de cada associação."
                : "Este é o modelo do motor que você acabou de ver na demonstração. Também temos motores para potes que se somam e para rateio por segmento, adaptáveis à regra de cada associação."}
            </div>
            <p className="mut-fino">
              Simulação com faixas e premissas aproximadas, não é um fechamento. No rateio real, o motor lê as exportações do SGA evento a evento,
              com trilha de auditoria, e fecha sem diferença contra o rateio homologado.
            </p>
            <div className="mut-nota">
              {c.quer_versao
                ? `Vamos enviar esta versão simplificada para o WhatsApp ${c.whatsapp}. Se quiser, também rodamos o rateio com as exportações reais da associação.`
                : "Você preferiu não receber a versão simplificada agora. Se mudar de ideia, é só falar com a equipe no estande."}
            </div>
            {aviso && <div className="mut-aviso">{aviso}</div>}
            <div className="flex gap-3 flex-wrap">
              <button onClick={novoAtendimento} className="mut-botao">Encerrar e iniciar novo atendimento</button>
              <button onClick={() => { setErro(""); setPasso("simulacao") }} className="mut-botao-sec">Ajustar respostas</button>
            </div>
          </div>
        )}

        {equipe && (
          <div className="mut-equipe mt-16 pt-4 flex gap-4 items-center flex-wrap">
            <button onClick={verLeads}>Ver contatos registrados</button>
            {leads && !leads.erro && <span>{leads.total} {leads.total === 1 ? "contato" : "contatos"} (quentes {leads.quente}, mornos {leads.morno}, frios {leads.frio}), {leads.com_simulacao} com simulação concluída. Arquivo: {leads.arquivo}</span>}
            {leads?.erro && <span>Servidor indisponível.</span>}
            <a href="/avap/simulador/leads.csv">Baixar planilha</a>
          </div>
        )}
      </main>
    </div>
  )
}

function Grupo({ titulo, obrig, children }) {
  return (
    <section className="mut-cartao">
      <h3>{titulo}{obrig && <span className="mut-obrig"> *</span>}</h3>
      <div className="grid md:grid-cols-3 gap-4">{children}</div>
    </section>
  )
}
function Campo({ rotulo, dica, obrig, children }) {
  return (
    <label className="block">
      <span className="mut-rotulo">{rotulo}{obrig && <span className="mut-obrig"> *</span>}</span>
      {children}
      {dica && <span className="mut-dica">{dica}</span>}
    </label>
  )
}
// Seletor de uma opção entre várias, em botões grandes (bom para tablet). valor é o índice escolhido ou null.
function Opcoes({ opcoes, valor, onChange }) {
  return (
    <div className="flex flex-wrap gap-2" role="radiogroup">
      {opcoes.map((o, i) => (
        <button key={o} type="button" role="radio" aria-checked={valor === i} onClick={() => onChange(i)}
          className="mut-opcao">{o}</button>
      ))}
    </div>
  )
}
const estiloInput = "mut-campo"
function Txt(props) { return <input className={estiloInput} {...props} /> }
function Sel({ value, onChange, opcoes }) {
  return (
    <select value={value} onChange={onChange} className={estiloInput}>
      <option value="">Selecione</option>
      {opcoes.map((o) => <option key={o}>{o}</option>)}
    </select>
  )
}
function Card({ rotulo, valor, sub }) {
  return (
    <div className="mut-cartao">
      <div className="mut-indicador-rotulo">{rotulo}</div>
      <div className="mut-indicador-valor">{valor}</div>
      {sub && <div className="mut-indicador-sub">{sub}</div>}
    </div>
  )
}
