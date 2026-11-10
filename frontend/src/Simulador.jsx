import { useState } from 'react'
import './Simulador.css'

// Simulador rápido da Fenaprove, em três passos: 1) dados do contato (e-mail é o principal; WhatsApp só se o visitante quiser),
// 2) quatro perguntas com faixas, 3) versão simplificada do rateio. Mesma fórmula do pote único da AVAP:
// valor da cota = (eventos + somas - deduções) / cotas dos veículos ativos. Aqui somas e deduções valem zero.
// Cada faixa vale pelo seu ponto médio, então o resultado é uma estimativa, e a tela diz isso.
// O contato vai ao backend (/avap/simulador/lead) já no passo 1, e a mesma linha é atualizada no passo 3.

// Mesmo endereço de API das outras telas: vazio em desenvolvimento (proxy do Vite), URL do backend em produção.
const API = import.meta.env.VITE_API_URL ?? ""

const brl = (v) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const num = (v) => Math.round(v).toLocaleString('pt-BR')
const R_POR_COTA_FIPE = 5000 // regra da AVAP: 1 cota a cada R$ 5 mil de FIPE

// Faixas: [texto mostrado, valor usado na conta (ponto médio)]. Para mudar as faixas, basta editar aqui.
const VEICULOS = [["Até 1.000", 700], ["1.001 a 3.000", 2000], ["3.001 a 5.000", 4000], ["5.001 a 10.000", 7500],
  ["10.001 a 20.000", 15000], ["20.001 a 40.000", 30000], ["Mais de 40.000", 50000]]
const FIPE = [["Até R$ 30 mil", 25000], ["R$ 30 a 60 mil", 45000], ["R$ 60 a 100 mil", 80000],
  ["R$ 100 a 200 mil", 150000], ["Acima de R$ 200 mil", 250000]]
const EVENTOS = [["Até 50", 40], ["51 a 100", 75], ["101 a 200", 150], ["201 a 400", 300], ["401 a 800", 600], ["Mais de 800", 1000]]
const CUSTO = [["Até R$ 5 mil", 3000], ["R$ 5 a 10 mil", 7500], ["R$ 10 a 20 mil", 15000],
  ["R$ 20 a 40 mil", 30000], ["Acima de R$ 40 mil", 50000]]

// Sugestões, para o visitante não precisar saber o número de cabeça. Valem enquanto ele não escolher faixa nem digitar.
// Eventos: 1,75% da frota por mês (informado pela Mutualiza). Custo médio: R$ 8.000 por evento (referência da AVAP).
// Para ajustar, basta mudar as duas constantes. Na AVAP real (set/2026) foram 103 eventos para 22.530 veículos ativos.
const PCT_EVENTOS = 0.0175
const CUSTO_SUGERIDO = 8000

const PERGUNTAS = [
  { k: "veiculos", titulo: "Quantos veículos ativos a associação tem?", faixas: VEICULOS },
  { k: "fipe", titulo: "Qual o valor médio dos veículos (tabela FIPE)?", dica: "Usamos 1 cota a cada R$ 5 mil de FIPE, a regra da AVAP.", faixas: FIPE },
  { k: "eventos", titulo: "Quantos eventos entraram no rateio no último mês?", faixas: EVENTOS, sug: true,
    livre: { rotulo: "Ou digite o número exato de eventos", exemplo: "ex.: 137", max: 100000, inteiro: true } },
  { k: "custo", titulo: "Qual o custo médio de cada evento?", faixas: CUSTO, sug: true,
    livre: { rotulo: "Ou digite o custo médio exato (R$)", exemplo: "ex.: 23.500", max: 10000000 } },
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
  nome: "", email: "", whatsapp: "", associacao: "", cargo: "", sistema_gestao: "",
  rateio_hoje: "", modelo: null, quer_whatsapp: null, consentimento: false,
}
const SEL_VAZIA = { veiculos: null, fipe: null, eventos: null, custo: null }
const EXATO_VAZIO = { eventos: "", custo: "" }

// Valor digitado no campo livre, já validado pelos limites da pergunta, ou null.
function exatoValido(k, texto) {
  const p = PERGUNTAS.find((q) => q.k === k)
  const n = lerNumero(texto)
  if (n === null || !p?.livre || n > p.livre.max) return null
  if (p.livre.inteiro && !Number.isInteger(n)) return null
  return n
}

// DDDs em uso no Brasil (Anatel).
const DDDS = new Set([11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38,
  41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68, 69, 71, 73, 74, 75, 77, 79,
  81, 82, 83, 84, 85, 86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99])

// Devolve a mensagem de erro do WhatsApp, ou "" se estiver válido. Aceita com ou sem +55, com ou sem máscara.
function erroWhatsapp(valor) {
  let d = String(valor).replace(/\D/g, "")
  if ((d.length === 12 || d.length === 13) && d.startsWith("55")) d = d.slice(2)
  if (d.length !== 10 && d.length !== 11) return "Informe o WhatsApp com DDD, por exemplo (31) 99999-0000."
  if (!DDDS.has(Number(d.slice(0, 2)))) return "O DDD informado não existe. Confira os dois primeiros números."
  const numero = d.slice(2)
  if (/^(\d)\1+$/.test(numero)) return "Esse número de WhatsApp não parece real. Confira os dígitos."
  if (numero.length === 9 && numero[0] !== "9") return "Celular com 9 dígitos deve começar com 9."
  return ""
}
// E-mail é o contato principal: obrigatório e com formato válido (mesma regra do servidor).
function erroEmail(valor) {
  const v = String(valor).trim()
  if (!v) return "Informe seu e-mail: é por ele que enviamos o resultado."
  return /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)*\.[A-Za-z]{2,}$/.test(v) ? "" : "O e-mail não parece válido. Confira os caracteres e o domínio."
}
// Número digitado no formato brasileiro: "25.000", "25000" ou "25.000,50". Devolve null se não der para ler.
function lerNumero(valor) {
  const v = String(valor).trim().replace(/\s|R\$/g, "")
  if (!v || !/^[\d.,]+$/.test(v)) return null
  const n = Number(v.replace(/\./g, "").replace(",", "."))
  return Number.isFinite(n) && n > 0 ? n : null
}

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
  const r = await fetch(`${API}/avap/simulador/lead`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(lead),
  })
  if (!r.ok) {
    const j = await r.json().catch(() => ({}))
    const e = new Error(typeof j.detail === 'string' ? j.detail : r.status === 422 ? "Confira o e-mail e o WhatsApp informados." : "Falha ao registrar")
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

// Sugestão para a pergunta k, ou null se ainda não dá para sugerir (eventos dependem da faixa de veículos).
function sugestaoDe(k, s) {
  if (k === "custo") return CUSTO_SUGERIDO
  if (k === "eventos" && s.veiculos !== null) return Math.max(1, Math.round(VEICULOS[s.veiculos][1] * PCT_EVENTOS))
  return null
}
// Valor usado na conta para cada pergunta: o número exato digitado, senão o ponto médio da faixa, senão a sugestão.
function valorDe(k, s, exato) {
  const n = exato && k in exato ? exatoValido(k, exato[k]) : null
  if (n !== null) return n
  if (s[k] !== null) return PERGUNTAS.find((q) => q.k === k).faixas[s[k]][1]
  return sugestaoDe(k, s)
}
// A sugestão está valendo quando a pergunta tem sugestão e o visitante não escolheu faixa nem digitou número.
const usandoSugestao = (k, s, exato) => k in exato && s[k] === null && !exato[k].trim() && sugestaoDe(k, s) !== null
function calcular(s, exato = EXATO_VAZIO) {
  const v = Object.fromEntries(PERGUNTAS.map(({ k }) => [k, valorDe(k, s, exato)]))
  if (Object.values(v).some((x) => x === null)) return null
  const veiculos = v.veiculos
  const cotasPorVeiculo = v.fipe / R_POR_COTA_FIPE
  const cotasTotal = veiculos * cotasPorVeiculo
  const eventosQtd = v.eventos
  const eventosValor = eventosQtd * v.custo
  const valorCota = eventosValor / cotasTotal
  return { veiculos, cotasPorVeiculo, cotasTotal, eventosQtd, eventosValor, valorCota, rateioMedio: cotasPorVeiculo * valorCota }
}

export default function Simulador({ equipe = false }) {
  const [passo, setPasso] = useState("contato")
  const [id, setId] = useState(novoId)
  const [c, setC] = useState(CONTATO_VAZIO)
  const [s, setS] = useState(SEL_VAZIA)
  const [exato, setExato] = useState(EXATO_VAZIO)
  const [erro, setErro] = useState("")
  const [aviso, setAviso] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [leads, setLeads] = useState(null)
  const r = calcular(s, exato)
  const setc = (k) => (e) => { setErro(""); setC({ ...c, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }) }
  const escolherC = (k, valor) => { setErro(""); setC({ ...c, [k]: valor }) }
  // Tocar numa faixa limpa o número exato daquela pergunta, e digitar o número exato desmarca a faixa.
  const escolherS = (k, i) => { setErro(""); setS({ ...s, [k]: i }); if (k in exato) setExato({ ...exato, [k]: "" }) }
  const digitarExato = (k, texto) => { setErro(""); setExato({ ...exato, [k]: texto }); if (texto.trim()) setS({ ...s, [k]: null }) }
  // Voltar para a sugestão: limpa faixa e número exato daquela pergunta.
  const usarSugestao = (k) => { setErro(""); setS({ ...s, [k]: null }); setExato({ ...exato, [k]: "" }) }
  // Texto da faixa para o registro do lead: a faixa escolhida ou o número exato digitado.
  const faixaTexto = (k) => {
    const n = k in exato ? exatoValido(k, exato[k]) : null
    if (n !== null) return k === "custo" ? `exato: ${brl(n)}` : `exato: ${num(n)}`
    if (usandoSugestao(k, s, exato)) return k === "custo" ? `sugestão: ${brl(sugestaoDe(k, s))}` : `sugestão: ${num(sugestaoDe(k, s))}`
    return PERGUNTAS.find((q) => q.k === k).faixas[s[k]][0]
  }

  const montarLead = (etapa, simulacao = {}) => ({
    id, etapa, nome: c.nome.trim(), email: c.email.trim(),
    whatsapp: c.quer_whatsapp === true ? c.whatsapp.trim() : "",
    associacao: c.associacao.trim(), cargo: c.cargo, sistema_gestao: c.sistema_gestao,
    rateio_hoje: c.rateio_hoje, modelo_rateio: c.modelo === null ? "" : MODELOS[c.modelo],
    quer_whatsapp: c.quer_whatsapp === true, consentimento: c.consentimento, simulacao,
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
    const eE = erroEmail(c.email)
    if (eE) return setErro(eE)
    if (c.quer_whatsapp === null) return setErro("Diga se quer receber também no WhatsApp.")
    const eW = c.quer_whatsapp ? erroWhatsapp(c.whatsapp) : ""
    if (eW) return setErro(eW)
    if (!c.consentimento) return setErro("Para continuar, marque a autorização de contato.")
    setErro(""); setEnviando(true)
    try { await salvar(montarLead("contato")) } catch (e) { setEnviando(false); return setErro(e.message) }
    setEnviando(false); setPasso("simulacao")
  }

  const simular = () => {
    for (const { k, livre } of PERGUNTAS) {
      if (livre && exato[k].trim() && exatoValido(k, exato[k]) === null)
        return setErro(`Confira o número digitado em "${livre.rotulo.replace(/^Ou digite /, "")}". Use só números${livre.inteiro ? " inteiros" : ""}, até ${num(livre.max)}.`)
    }
    if (!r) return setErro("Responda as quatro perguntas para simular.")
    setErro(""); setPasso("resultado")
    salvar(montarLead("resultado", {
      faixa_veiculos: VEICULOS[s.veiculos][0], faixa_fipe: FIPE[s.fipe][0],
      faixa_eventos: faixaTexto("eventos"), faixa_custo: faixaTexto("custo"),
      veiculos_ativos: r.veiculos, cotas_total: Math.round(r.cotasTotal), eventos_qtd: r.eventosQtd,
      eventos_valor: r.eventosValor.toFixed(2), valor_cota: r.valorCota.toFixed(4),
    })).catch((e) => setErro(e.message))
  }

  const novoAtendimento = () => {
    setC(CONTATO_VAZIO); setS(SEL_VAZIA); setExato(EXATO_VAZIO); setId(novoId()); setErro(""); setAviso(""); setPasso("contato")
  }
  const verLeads = async () => {
    try { setLeads(await (await fetch(`${API}/avap/simulador/leads`)).json()) } catch { setLeads({ erro: true }) }
  }

  return (
    <div className="mut-sim">
      <header className="mut-hero">
        <div className="max-w-5xl mx-auto px-6 py-8 mut-hero-linha">
          <img className="mut-logo" src="/brand/mutualiza-simbolo-claro.png" alt="Mutualiza" />
          <div>
            <div className="mut-eyebrow">Simulador rápido · Fenaprove 2026</div>
            <h1 className="mut-title mt-1">Quanto daria o rateio da sua associação</h1>
            <div className="flex gap-2 mt-4 text-xs">
              {[["contato", "1. Seus dados"], ["simulacao", "2. Simulação"], ["resultado", "3. Resultado"]].map(([k, l]) => (
                <span key={k} className="mut-passo" data-ativo={passo === k}>{l}</span>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {erro && passo === "resultado" && <div className="mut-erro mb-4">{erro}</div>}

        {passo === "contato" && (
          <div className="space-y-6 max-w-4xl">
            <p className="mut-intro">Primeiro, seu e-mail e alguns dados para a gente saber com quem está falando: o resultado chega por e-mail. Depois é só escolher faixas ou, se preferir, digitar os números exatos.</p>
            <Grupo titulo="Seus dados">
              <Campo rotulo="Nome" obrig><Txt value={c.nome} onChange={setc("nome")} /></Campo>
              <Campo rotulo="E-mail" obrig><Txt value={c.email} onChange={setc("email")} inputMode="email" type="email" autoComplete="email"
                placeholder="nome@associacao.com.br" aria-invalid={Boolean(erro) && Boolean(erroEmail(c.email))} /></Campo>
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
            <Grupo titulo="Quer receber também a versão simplificada do rateio da sua associação no WhatsApp?" obrig>
              <div className="md:col-span-3 space-y-3">
                <Opcoes opcoes={["Sim, quero também no WhatsApp", "Não, só por e-mail"]}
                  valor={c.quer_whatsapp === null ? null : (c.quer_whatsapp ? 0 : 1)}
                  onChange={(i) => escolherC("quer_whatsapp", i === 0)} />
                {c.quer_whatsapp === true && (
                  <div className="max-w-sm">
                    <Campo rotulo="WhatsApp com DDD" obrig><Txt value={c.whatsapp} onChange={setc("whatsapp")} placeholder="(31) 9...." inputMode="tel"
                      autoComplete="tel" aria-invalid={Boolean(erro) && Boolean(erroWhatsapp(c.whatsapp))} /></Campo>
                  </div>
                )}
              </div>
            </Grupo>
            <label className="mut-consentimento flex gap-3 items-start">
              <input type="checkbox" className="mt-1" checked={c.consentimento} onChange={setc("consentimento")} />
              <span>Autorizo o envio deste resultado por e-mail (e por WhatsApp, se eu tiver pedido) e a guarda destes dados para esse fim. Posso pedir a exclusão a qualquer momento.</span>
            </label>
            {erro && <div className="mut-erro" role="alert">{erro}</div>}
            <button onClick={continuar} disabled={enviando} className="mut-botao">{enviando ? "Registrando…" : "Continuar para a simulação"}</button>
          </div>
        )}

        {passo === "simulacao" && (
          <div className="space-y-6">
            <p className="mut-intro">Quatro perguntas, é só tocar na faixa mais próxima da realidade da associação. Em eventos e custo médio já deixamos uma sugestão: se você souber o número real, escolha uma faixa ou digite.</p>
            {PERGUNTAS.map(({ k, titulo, dica, faixas, livre, sug }) => (
              <Grupo key={k} titulo={titulo} obrig>
                <div className="md:col-span-3 space-y-2">
                  <Opcoes opcoes={faixas.map(([l]) => l)} valor={s[k]} onChange={(i) => escolherS(k, i)}
                    extra={sug && sugestaoDe(k, s) !== null ? {
                      rotulo: k === "custo" ? `Sugestão: ${brl(sugestaoDe(k, s))}` : `Sugestão: ${num(sugestaoDe(k, s))} eventos`,
                      ativo: usandoSugestao(k, s, exato), onClick: () => usarSugestao(k),
                    } : null} />
                  {dica && <span className="mut-dica">{dica}</span>}
                  {sug && k === "eventos" && (
                    <span className="mut-dica">
                      {sugestaoDe(k, s) === null
                        ? "Responda a quantidade de veículos para ver a sugestão de eventos."
                        : `Sugestão: ${(PCT_EVENTOS * 100).toLocaleString('pt-BR')}% dos veículos da associação entram em evento por mês, em média (${num(VEICULOS[s.veiculos][1])} veículos, cerca de ${num(sugestaoDe(k, s))} eventos). Se você já sabe o número, escolha uma faixa ou digite abaixo.`}
                    </span>
                  )}
                  {sug && k === "custo" && (
                    <span className="mut-dica">
                      {`Sugestão: ${brl(CUSTO_SUGERIDO)} por evento, o custo médio de uma associação de referência. Se você já sabe o custo da sua, escolha uma faixa ou digite abaixo.`}
                    </span>
                  )}
                  {livre && (
                    <label className="mut-livre">
                      <span className="mut-rotulo">{livre.rotulo}</span>
                      <input className="mut-campo" inputMode={livre.inteiro ? "numeric" : "decimal"} placeholder={livre.exemplo}
                        value={exato[k]} onChange={(e) => digitarExato(k, e.target.value)}
                        aria-invalid={Boolean(exato[k].trim()) && exatoValido(k, exato[k]) === null} />
                    </label>
                  )}
                </div>
              </Grupo>
            ))}
            {aviso && <div className="mut-aviso">{aviso}</div>}
            {erro && <div className="mut-erro" role="alert">{erro}</div>}
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
              <Card rotulo="Eventos do mês (estimado)" valor={brl(r.eventosValor)} sub={`${num(r.eventosQtd)} eventos de ${brl(r.eventosValor / r.eventosQtd)} em média`} />
              <Card rotulo="Veículos ativos" valor={VEICULOS[s.veiculos][0]} sub="faixa informada" />
              <Card rotulo="Cotas estimadas" valor={num(r.cotasTotal)} sub={`${r.cotasPorVeiculo.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} cotas por veículo`} />
              <Card rotulo="Rateio do veículo médio" valor={brl(r.rateioMedio)} sub="por mês" />
            </div>
            {(usandoSugestao("eventos", s, exato) || usandoSugestao("custo", s, exato)) && (
              <div className="mut-nota">
                {`Nesta simulação ${[usandoSugestao("eventos", s, exato) && `a quantidade de eventos (${(PCT_EVENTOS * 100).toLocaleString('pt-BR')}% dos veículos por mês)`,
                  usandoSugestao("custo", s, exato) && `o custo médio por evento (${brl(CUSTO_SUGERIDO)})`].filter(Boolean).join(" e ")} vieram da nossa sugestão, não de dados da associação. Com os números reais, o resultado muda.`}
              </div>
            )}
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
              {`Vamos enviar esta versão simplificada para ${c.email.trim()}${c.quer_whatsapp ? ` e para o WhatsApp ${c.whatsapp.trim()}` : ""}. Se quiser, também rodamos o rateio com as exportações reais da associação.`}
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
            <a href={`${API}/avap/simulador/leads.csv`}>Baixar planilha</a>
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
function Opcoes({ opcoes, valor, onChange, extra = null }) {
  return (
    <div className="flex flex-wrap gap-2" role="radiogroup">
      {extra && <button type="button" role="radio" aria-checked={extra.ativo} onClick={extra.onClick}
        className="mut-opcao mut-opcao-sug">{extra.rotulo}</button>}
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
