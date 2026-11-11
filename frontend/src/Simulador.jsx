import { useState } from 'react'
import './Simulador.css'

// Simulador rápido da Fenaprove, em três passos: 1) dados do contato (e-mail é o principal; WhatsApp só se o visitante quiser),
// 2) perguntas com faixas ou número exato, 3) versão simplificada do rateio. Mesma fórmula do pote único:
// valor da cota = (eventos + somas - deduções) / cotas dos veículos ativos. Aqui somas e deduções valem zero.
// O número principal é o rateio por veículo por mês (eventos / veículos), que não depende da regra de cota.
// A regra de cota muda só o valor da cota, e por isso é perguntada: cada associação usa uma régua diferente.
// O contato vai ao backend (/avap/simulador/lead) já no passo 1, e a mesma linha é atualizada no passo 3.

// Mesmo endereço de API das outras telas: vazio em desenvolvimento (proxy do Vite), URL do backend em produção.
const API = import.meta.env.VITE_API_URL ?? ""

const brl = (v) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const num = (v) => Math.round(v).toLocaleString('pt-BR')
const pct = (v) => (v * 100).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) + "%"

// Referências gerais para as sugestões. Média ponderada de duas associações com frota e eventos conhecidos:
// AVAP (carros, ago e set/2026: 126,5 eventos por mês para 22.530 veículos, R$ 13.869 por evento) e
// ELLO (motos, 2025: 78,8 eventos por mês para 12.300 motos, R$ 11.627 por evento). Para ajustar, basta editar aqui.
const PCT_EVENTOS = 0.0059 // eventos por mês, em % da frota (faixa observada: 0,5% a 0,8%)
const CUSTO_SUGERIDO = 13000 // custo médio por evento, em R$
const COTAS_POR_VEICULO_REF = 10.3 // AVAP: 231.556 cotas para 22.530 veículos ativos
const REF_SUGESTAO = "média de duas associações reais, uma de carros e uma de motos"

// Faixas: [texto mostrado, valor usado na conta (ponto médio)]. Para mudar as faixas, basta editar aqui.
const VEICULOS = [["Até 1.000", 700], ["1.001 a 3.000", 2000], ["3.001 a 5.000", 4000], ["5.001 a 10.000", 7500],
  ["10.001 a 20.000", 15000], ["20.001 a 40.000", 30000], ["Mais de 40.000", 50000]]
const EVENTOS = [["Até 50", 40], ["51 a 100", 75], ["101 a 200", 150], ["201 a 400", 300], ["401 a 800", 600], ["Mais de 800", 1000]]
const CUSTO = [["Até R$ 5 mil", 3000], ["R$ 5 a 10 mil", 7500], ["R$ 10 a 20 mil", 15000],
  ["R$ 20 a 40 mil", 30000], ["Acima de R$ 40 mil", 50000]]

// Perguntas da simulação (quatro). Veículos e cotas aceitam faixa ou número exato; eventos e custo trazem uma sugestão.
// O total de cotas é opcional: sem ele, usamos a referência da AVAP e a tela avisa.
const PERGUNTAS = [
  { k: "veiculos", titulo: "Quantos veículos ativos a associação tem?", faixas: VEICULOS,
    livre: { rotulo: "Ou digite o número exato de veículos ativos", exemplo: "ex.: 22.530", max: 1000000, inteiro: true } },
  { k: "eventos", titulo: "Quantos eventos entraram no rateio no último mês?", faixas: EVENTOS, sug: true,
    dica: "Conte só os eventos do próprio associado. Eventos de terceiro não entram no rateio.",
    livre: { rotulo: "Ou digite o número exato de eventos", exemplo: "ex.: 137", max: 100000, inteiro: true } },
  { k: "custo", titulo: "Qual o custo médio de cada evento?", faixas: CUSTO, sug: true,
    dica: "Custo do evento é o valor do reparo menos a participação do associado.",
    livre: { rotulo: "Ou digite o custo médio exato (R$)", exemplo: "ex.: 23.500", max: 10000000 } },
  { k: "cotas", titulo: "Quantas cotas somam os veículos ativos? (opcional)", opcional: true,
    dica: "Aparece no relatório de cotas do sistema de gestão. Sem esse número, usamos a referência da AVAP, de cerca de 10 cotas por veículo.",
    livre: { rotulo: "Total de cotas da associação", exemplo: "ex.: 231.556", max: 100000000, inteiro: true } },
]
// Campo opcional da tela de resultado: quanto cada veículo paga hoje de rateio (não é pergunta da simulação).
const HOJE = { k: "hoje", livre: { rotulo: "Valor médio por veículo (R$)", exemplo: "ex.: 85", max: 100000 } }

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
const SEL_VAZIA = { veiculos: null, eventos: null, custo: null }
const EXATO_VAZIO = { veiculos: "", eventos: "", custo: "", cotas: "", hoje: "" }

// Valor digitado no campo livre, já validado pelos limites da pergunta, ou null.
function exatoValido(k, texto) {
  const p = [...PERGUNTAS, HOJE].find((q) => q.k === k)
  if (texto === undefined) return null
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

// Valor numérico de veículos (exato digitado, senão ponto médio da faixa), sem sugestão.
function baseDe(k, s, exato) {
  const n = exatoValido(k, exato[k])
  if (n !== null) return n
  return s[k] !== null ? PERGUNTAS.find((q) => q.k === k).faixas[s[k]][1] : null
}
// Sugestão para eventos (percentual da frota) e custo médio. null se ainda não dá (eventos dependem dos veículos).
function sugestaoDe(k, s, exato = EXATO_VAZIO) {
  if (k === "custo") return CUSTO_SUGERIDO
  if (k === "eventos") {
    const veic = baseDe("veiculos", s, exato)
    return veic === null ? null : Math.max(1, Math.round(veic * PCT_EVENTOS))
  }
  return null
}
// Valor usado na conta: o número exato digitado, senão o ponto médio da faixa, senão a sugestão.
function valorDe(k, s, exato) {
  const n = exatoValido(k, exato[k])
  if (n !== null) return n
  if (s[k] !== null) return PERGUNTAS.find((q) => q.k === k).faixas[s[k]][1]
  return sugestaoDe(k, s, exato)
}
// A sugestão está valendo quando a pergunta tem sugestão e o visitante não escolheu faixa nem digitou número.
const usandoSugestao = (k, s, exato) =>
  PERGUNTAS.find((q) => q.k === k)?.sug && s[k] === null && !exato[k].trim() && sugestaoDe(k, s, exato) !== null
function calcular(s, exato = EXATO_VAZIO) {
  const v = Object.fromEntries(["veiculos", "eventos", "custo"].map((k) => [k, valorDe(k, s, exato)]))
  if (Object.values(v).some((x) => x === null)) return null
  const veiculos = v.veiculos
  const cotasInformadas = exatoValido("cotas", exato.cotas)
  const cotasTotal = cotasInformadas ?? veiculos * COTAS_POR_VEICULO_REF
  const eventosQtd = v.eventos
  const eventosValor = eventosQtd * v.custo
  const hoje = exatoValido("hoje", exato.hoje)
  return {
    veiculos, cotasTotal, cotasInformadas: cotasInformadas !== null, cotasPorVeiculo: cotasTotal / veiculos,
    eventosQtd, eventosValor, valorCota: eventosValor / cotasTotal, rateioMedio: eventosValor / veiculos, hoje,
  }
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
    const emReais = k === "custo"
    const n = exatoValido(k, exato[k])
    if (n !== null) return emReais ? `exato: ${brl(n)}` : `exato: ${num(n)}`
    if (usandoSugestao(k, s, exato)) {
      const sg = sugestaoDe(k, s, exato)
      return emReais ? `sugestão: ${brl(sg)}` : `sugestão: ${num(sg)}`
    }
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
    if (!r) return setErro("Responda todas as perguntas obrigatórias para simular.")
    setErro(""); setPasso("resultado")
    // cotas_informadas e rateio_veiculo ainda não têm coluna própria no CSV de leads; seguem no objeto
    // para quando o backend passar a gravá-los (hoje o backend ignora chaves que não conhece).
    salvar(montarLead("resultado", {
      cotas_informadas: r.cotasInformadas ? "sim" : "não",
      rateio_veiculo: r.rateioMedio.toFixed(2),
      faixa_veiculos: faixaTexto("veiculos"),
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
            <p className="mut-intro">Quatro perguntas: toque na faixa mais próxima ou digite o número exato. Em eventos e custo médio deixamos uma sugestão tirada de fechamentos reais. Se você souber o número da sua associação, use o seu.</p>
            {PERGUNTAS.map(({ k, titulo, dica, faixas, escolha, livre, sug, opcional }) => (
              <Grupo key={k} titulo={titulo} obrig={!opcional}>
                <div className="md:col-span-3 space-y-2">
                  {(escolha || faixas) && (
                    <Opcoes opcoes={escolha ?? faixas.map(([l]) => l)} valor={s[k]} onChange={(i) => escolherS(k, i)}
                      extra={sug && sugestaoDe(k, s, exato) !== null ? {
                        rotulo: k === "custo" ? `Sugestão: ${brl(sugestaoDe(k, s, exato))}` : `Sugestão: ${num(sugestaoDe(k, s, exato))} eventos`,
                        ativo: usandoSugestao(k, s, exato), onClick: () => usarSugestao(k),
                      } : null} />
                  )}
                  {dica && <span className="mut-dica">{dica}</span>}
                  {sug && k === "eventos" && (
                    <span className="mut-dica">
                      {sugestaoDe(k, s, exato) === null
                        ? "Informe os veículos para ver a sugestão de eventos."
                        : `Sugestão: ${pct(PCT_EVENTOS)} dos veículos entram em evento por mês (faixa observada de 0,5% a 0,8%), cerca de ${num(sugestaoDe(k, s, exato))} eventos.`}
                    </span>
                  )}
                  {sug && k === "custo" && (
                    <span className="mut-dica">
                      {`Sugestão: ${brl(CUSTO_SUGERIDO)} por evento (${REF_SUGESTAO}).`}
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
              <div className="mut-eyebrow">Rateio estimado por veículo, por mês</div>
              <div className="mut-destaque-valor">{brl(r.rateioMedio)}</div>
              <div className="mut-destaque-sub">
                {brl(r.eventosValor)} de eventos dividido entre cerca de {num(r.veiculos)} veículos ativos. É o número para comparar com a parte de rateio do boleto.
              </div>
              <div className="mut-destaque-sub">
                Valor só do rateio dos eventos: não inclui taxa de administração, assistência 24h, produtos e benefícios nem contribuição de estabilização.
              </div>
            </div>
            <section className="mut-cartao">
              <h3>Quer comparar com o que a associação cobra hoje?</h3>
              <label className="mut-livre">
                <span className="mut-rotulo">Quanto cada veículo paga de rateio por mês, em média (R$)</span>
                <input className="mut-campo" inputMode="decimal" placeholder={HOJE.livre.exemplo} value={exato.hoje}
                  onChange={(e) => setExato({ ...exato, hoje: e.target.value })}
                  aria-invalid={Boolean(exato.hoje.trim()) && exatoValido("hoje", exato.hoje) === null} />
              </label>
              <span className="mut-dica">Só a parte do rateio, sem taxa de administração e assistência.</span>
            </section>
            {r.hoje !== null && (
              <div className="mut-nota">
                {`Hoje cada veículo paga cerca de ${brl(r.hoje)} de rateio. A estimativa dá ${brl(r.rateioMedio)}, `}
                {Math.abs(r.rateioMedio - r.hoje) / r.hoje < 0.05
                  ? "praticamente o mesmo valor."
                  : `${pct(Math.abs(r.rateioMedio - r.hoje) / r.hoje)} ${r.rateioMedio > r.hoje ? "acima" : "abaixo"} do que a associação cobra.`}
                {" A diferença costuma vir das linhas que a simulação não considera (inadimplência, salvados, rastreamento e outras) e de quais eventos entram no mês. No rateio real, o motor mostra cada uma delas."}
              </div>
            )}
            <div className="grid md:grid-cols-4 gap-3">
              <Card rotulo="Eventos do mês (estimado)" valor={brl(r.eventosValor)} sub={`${num(r.eventosQtd)} eventos de ${brl(r.eventosValor / r.eventosQtd)} em média`} />
              <Card rotulo="Veículos ativos" valor={num(r.veiculos)} sub={exatoValido("veiculos", exato.veiculos) !== null ? "número informado" : "ponto médio da faixa"} />
              <Card rotulo="Cotas estimadas" valor={num(r.cotasTotal)} sub={`${r.cotasPorVeiculo.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} cotas por veículo`} />
              <Card rotulo="Valor da cota" valor={brl(r.valorCota)} sub={r.cotasInformadas ? "com o total de cotas informado" : "com a referência da AVAP"} />
            </div>
            <div className="mut-nota">
              {r.cotasInformadas
                ? "O valor da cota usa o total de cotas que você informou, então segue a régua da sua associação."
                : "O valor da cota usa a referência da AVAP (1 cota a cada R$ 5 mil de FIPE, cerca de 10 cotas por veículo). Cada associação tem a sua régua: com cotas maiores, o valor da cota sobe. Para ver o valor na sua régua, volte e informe o total de cotas."}
              {" O número para comparar entre associações é o rateio por veículo."}
            </div>
            {(usandoSugestao("eventos", s, exato) || usandoSugestao("custo", s, exato)) && (
              <div className="mut-nota">
                {(() => {
                  const itens = [usandoSugestao("eventos", s, exato) && `a quantidade de eventos (${pct(PCT_EVENTOS)} dos veículos por mês)`,
                    usandoSugestao("custo", s, exato) && `o custo médio por evento (${brl(CUSTO_SUGERIDO)})`].filter(Boolean)
                  return `Nesta simulação ${itens.join(" e ")} ${itens.length > 1 ? "vieram" : "veio"} da referência (${REF_SUGESTAO}), não de dados da sua associação. Com os números reais, o resultado muda.`
                })()}
              </div>
            )}
            <div className="mut-nota">
              {c.modelo !== null && c.modelo !== 0
                ? "Sua associação usa outro modelo de rateio. Além do pote único, temos motores para potes que se somam e para rateio por segmento, adaptáveis à regra de cada associação."
                : "Este é o modelo do motor que você acabou de ver na demonstração. Também temos motores para potes que se somam e para rateio por segmento, adaptáveis à regra de cada associação."}
            </div>
            <p className="mut-fino">
              Simulação com faixas e premissas aproximadas, não é um fechamento, e não inclui taxa de administração nem demais itens do boleto. No rateio real, o motor lê as exportações do SGA evento a evento,
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
