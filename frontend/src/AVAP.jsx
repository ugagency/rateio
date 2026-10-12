import { useState, useEffect, useCallback } from 'react'

const API = ""
const enc = (m) => encodeURIComponent(m.replace("/", "-"))
const brl = (v) => (typeof v === 'number' ? v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : v)
const num = (v) => (typeof v === 'number' ? v.toLocaleString('pt-BR') : v)
const mesAnterior = () => {
  const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() - 1)
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}
const mascara = (p) => (p ? `${p.slice(0, 3)}****` : "-")

const TABS = { rodar: "Rodar Mês", selecao: "Seleção", lanc: "Lançamentos", resultado: "Resultado", boletos: "Boletos" }
const CRITERIOS = {
  VEICULO: "Veículos ativos (critério vigente)",
  AMBOS: "Veículo e associado ativos",
  ASSOCIADO: "Associados ativos",
  TODOS: "Todas as cotas",
}
const ALERTAS = {
  A1: "Protocolo atípico", A2: "Custo menor ou igual a zero", A3: "Sem participação e custo baixo",
  A4: "Concentração acima de 10% do total", A5: "Indenização integral", A6: "Data de finalização mudou",
  A7: "Custo diferente de reparo menos participação",
}

async function pedir(url, opts) {
  const r = await fetch(`${API}${url}`, opts)
  const j = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : "Falha na requisição")
  return j
}
const post = (url, body) => pedir(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })

export default function AVAP() {
  const [tab, setTab] = useState("rodar")
  const [mes, setMes] = useState(mesAnterior())
  const [sel, setSel] = useState(null)
  const [res, setRes] = useState(null)
  const [erro, setErro] = useState("")
  const [busy, setBusy] = useState("")
  const [criterio, setCriterio] = useState("VEICULO")

  const rodar = async (fn, rotulo) => {
    setBusy(rotulo); setErro("")
    try { return await fn() } catch (e) { setErro(e.message); return null } finally { setBusy("") }
  }

  const onSelecionado = (s, novoMes) => {
    setSel(s); setRes(null)
    if (novoMes) setMes(novoMes)
    setTab("selecao")
  }

  const demo = () => rodar(async () => {
    const s = await pedir("/avap/demo-setembro", { method: "POST" })
    onSelecionado(s, "09/2026")
  }, "Carregando o fechamento de 09/2026 (leitura de 39 mil veículos)")

  const calcular = () => rodar(async () => {
    const r = await post(`/avap/${enc(mes)}/calcular`, { criterio })
    setRes(r); setTab("resultado")
  }, "Calculando o rateio")

  const atualizarSelecao = (s) => { setSel(s); setRes(null) }

  return (
    <div className="bg-slate-900 text-slate-200 min-h-[calc(100vh-44px)]">
      <header className="border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center flex-wrap gap-2">
          <div>
            <div className="text-xs uppercase tracking-widest text-emerald-400">Motor de Rateio · Associação de proteção veicular</div>
            <h1 className="text-2xl font-bold text-white">AVAP: Rateio em pote único</h1>
          </div>
          <div className="text-right text-xs text-slate-500">
            {sel ? <>Competência {mes} · {sel.origem}</> : "Nenhum fechamento carregado"}
            <div>LC 213/2025 · Res. CNSP 491/2026</div>
          </div>
        </div>
        <nav className="max-w-7xl mx-auto px-6 pb-4 flex gap-2 flex-wrap items-center">
          {Object.entries(TABS).map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`px-4 py-2 rounded text-sm font-semibold ${tab === k ? "bg-emerald-500 text-slate-900" : "bg-slate-700 text-slate-200"}`}>
              {l}
            </button>
          ))}
          <span className="ml-auto flex gap-2 items-center">
            <button onClick={demo} disabled={!!busy}
              title="Carrega os arquivos reais de 09/2026 que estão no servidor"
              className="px-4 py-1.5 bg-amber-400 text-slate-900 font-bold rounded text-sm disabled:opacity-50">
              Demonstração 09/2026
            </button>
          </span>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {erro && <div className="mb-4 bg-red-900/40 border border-red-700 text-red-200 px-4 py-2 rounded">{erro}</div>}
        {busy && <div className="mb-4 bg-slate-800 border border-slate-600 text-slate-200 px-4 py-2 rounded animate-pulse">{busy}…</div>}
        {tab === "rodar" && <RodarMes mes={mes} setMes={setMes} rodar={rodar} onSelecionado={onSelecionado} busy={!!busy} />}
        {tab === "selecao" && <Selecao mes={mes} sel={sel} rodar={rodar} onAtualizar={atualizarSelecao} irParaLanc={() => setTab("lanc")} irParaRodar={() => setTab("rodar")} />}
        {tab === "lanc" && <Lancamentos mes={mes} sel={sel} rodar={rodar} onAtualizar={atualizarSelecao}
          irParaResultado={() => setTab("resultado")} irParaRodar={() => setTab("rodar")} />}
        {tab === "resultado" && <Resultado mes={mes} sel={sel} res={res} criterio={criterio} setCriterio={setCriterio} calcular={calcular} busy={!!busy} irParaRodar={() => setTab("rodar")} />}
        {tab === "boletos" && <Boletos mes={mes} res={res} />}
      </main>
    </div>
  )
}

function Vazio({ texto, acao, rotulo }) {
  return (
    <div className="text-center py-16">
      <p className="text-slate-300 mb-4">{texto}</p>
      {acao && <button onClick={acao} className="px-5 py-2 bg-emerald-500 text-slate-900 font-bold rounded">{rotulo}</button>}
    </div>
  )
}

function Card({ label, value, sub, tone = "slate" }) {
  const cores = { slate: "text-white", green: "text-emerald-400", amber: "text-amber-300", red: "text-red-400" }
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <div className="text-xs uppercase tracking-wider text-slate-400">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${cores[tone]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}

// ─────────────────────────── Rodar Mês ───────────────────────────

function RodarMes({ mes, setMes, rodar, onSelecionado, busy }) {
  const [veic, setVeic] = useState({ file: null, info: null })
  const [ev, setEv] = useState({ file: null, info: null })
  const [dataFech, setDataFech] = useState("")

  const escolher = async (slot, file, set) => {
    if (!file) { set({ file: null, info: null }); return }
    set({ file, info: { carregando: true } })
    const fd = new FormData(); fd.append("arquivo", file); fd.append("slot", slot)
    try { set({ file, info: await pedir("/avap/inspecionar-arquivo", { method: "POST", body: fd }) }) }
    catch (e) { set({ file, info: { valido: false, erro: e.message } }) }
  }

  const pronto = veic.info?.valido && ev.info?.valido && /^\d{2}\/\d{4}$/.test(mes)
  const processar = () => rodar(async () => {
    const fd = new FormData()
    fd.append("veiculos", veic.file); fd.append("eventos", ev.file); fd.append("mes_ano_ref", mes)
    if (dataFech) fd.append("data_fechamento", dataFech)
    onSelecionado(await pedir("/avap/selecionar", { method: "POST", body: fd }), mes)
  }, "Lendo as exportações do SGA e montando a seleção")

  return (
    <div className="max-w-3xl">
      <h2 className="text-xl font-bold text-white mb-1">Carregar as exportações do SGA</h2>
      <p className="text-slate-400 text-sm mb-6">
        Cada arquivo é conferido com o rodapé do próprio SGA assim que é escolhido. Se a contagem ou a soma não bater, o arquivo é recusado.
      </p>
      <div className="space-y-4">
        <Slot titulo="1. Base de veículos e cotas" dica="Relatório de veículos do SGA (peso da cota lido do próprio rótulo)"
          slot={veic} onPick={(f) => escolher("VEICULOS", f, setVeic)}
          resumo={(r) => `${num(r.veiculos)} veículos · ${num(r.cotas)} cotas`} />
        <Slot titulo="2. Relatório de eventos (fila do fechamento)" dica="Exportação de eventos do SGA com a coluna Valor Rateado"
          slot={ev} onPick={(f) => escolher("EVENTOS", f, setEv)}
          resumo={(r) => `${num(r.eventos)} eventos · ${num(r.na_fila)} na fila do SGA (R$ ${brl(r.custo_na_fila)})`} />
      </div>
      <div className="flex gap-4 mt-6 items-end flex-wrap">
        <label className="text-sm">
          <div className="text-slate-400 mb-1">Competência</div>
          <input value={mes} onChange={(e) => setMes(e.target.value)} placeholder="MM/AAAA"
            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white w-32" />
        </label>
        <label className="text-sm">
          <div className="text-slate-400 mb-1">Data de corte (opcional)</div>
          <input type="date" value={dataFech} onChange={(e) => setDataFech(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white" />
        </label>
        <button onClick={processar} disabled={!pronto || busy}
          className="px-6 py-2 bg-emerald-500 text-slate-900 font-bold rounded disabled:opacity-40">
          Montar seleção
        </button>
      </div>
    </div>
  )
}

function Slot({ titulo, dica, slot, onPick, resumo }) {
  const i = slot.info
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <div className="font-semibold text-white">{titulo}</div>
      <div className="text-xs text-slate-400 mb-2">{dica}</div>
      <input type="file" accept=".xlsx" onChange={(e) => onPick(e.target.files[0])}
        className="text-sm text-slate-300 file:mr-3 file:px-3 file:py-1.5 file:rounded file:border-0 file:bg-slate-600 file:text-white" />
      {i?.carregando && <div className="text-xs text-slate-400 mt-2">Conferindo com o rodapé…</div>}
      {i && !i.carregando && (i.valido
        ? <div className="text-xs mt-2 text-emerald-400">Conferido com o rodapé do SGA: {resumo(i.resumo)}</div>
        : <div className="text-xs mt-2 text-red-400">{i.erro}</div>)}
    </div>
  )
}

// ─────────────────────────── Seleção ───────────────────────────

function Selecao({ mes, sel, rodar, onAtualizar, irParaLanc, irParaRodar }) {
  const [just, setJust] = useState("")
  const [itens, setItens] = useState({ total: 0, items: [] })
  useEffect(() => {
    if (!sel) return
    pedir(`/avap/${enc(mes)}/eventos?page_size=15`).then(setItens).catch(() => {})
  }, [sel, mes])
  if (!sel) return <Vazio texto="Nenhum fechamento carregado." acao={irParaRodar} rotulo="Carregar arquivos" />

  const porProt = {}
  sel.alertas.forEach((a) => { (porProt[a.protocolo] ||= []).push(a.codigo) })
  const decidir = (lista, decisao) => rodar(async () => {
    onAtualizar(await post(`/avap/${enc(mes)}/decidir`, {
      decisoes: lista.map((p) => ({ protocolo: p, decisao, justificativa: just.trim() })),
    }))
    setJust("")
  }, "Registrando a decisão")

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card label="Eventos lidos" value={num(sel.total_eventos_lidos)} />
        <Card label="Selecionados" value={num(sel.selecionados)} sub={`R$ ${brl(sel.custo_selecionado)}`} tone="green" />
        <Card label="Aguardando decisão" value={num(sel.pendencias.length)} tone={sel.pendencias.length ? "amber" : "green"} sub="alertas sem decisão do operador" />
        <Card label="Homologável" value={sel.homologavel ? "Sim" : "Não"} tone={sel.homologavel ? "green" : "red"} sub={`${sel.decisoes} decisões registradas`} />
      </div>

      {sel.pendencias.length > 0 && (
        <section className="bg-slate-800 border border-amber-700/60 rounded-lg p-4 mb-6">
          <h3 className="font-bold text-amber-300 mb-1">Eventos que precisam de decisão</h3>
          <p className="text-xs text-slate-400 mb-3">
            São eventos da fila do SGA que dispararam alerta. O motor não decide sozinho: cada escolha exige justificativa e fica na trilha de auditoria.
          </p>
          <div className="flex gap-2 mb-3 flex-wrap">
            <input value={just} onChange={(e) => setJust(e.target.value)} placeholder="Justificativa (obrigatória)"
              className="flex-1 min-w-64 px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white text-sm" />
            <button disabled={just.trim().length < 3} onClick={() => decidir(sel.pendencias, "INCLUIR")}
              className="px-4 py-2 bg-emerald-500 text-slate-900 font-bold rounded text-sm disabled:opacity-40">Incluir todos</button>
            <button disabled={just.trim().length < 3} onClick={() => decidir(sel.pendencias, "EXCLUIR")}
              className="px-4 py-2 bg-slate-600 text-white font-bold rounded text-sm disabled:opacity-40">Excluir todos</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-slate-400 uppercase">
                <tr><th className="text-left p-2">Protocolo</th><th className="text-left p-2">Motivo</th><th className="text-right p-2">Custo</th><th className="text-left p-2">Alertas</th><th className="p-2" /></tr>
              </thead>
              <tbody>
                {sel.eventos_pendentes.map((e) => (
                  <tr key={e.protocolo} className="border-t border-slate-700">
                    <td className="p-2 font-mono">{e.protocolo}</td>
                    <td className="p-2">{e.motivo}</td>
                    <td className="p-2 text-right">R$ {brl(e.custo_evento)}</td>
                    <td className="p-2 text-xs text-amber-300">{(porProt[e.protocolo] || []).map((c) => `${c} ${ALERTAS[c] || ""}`).join(" · ")}</td>
                    <td className="p-2 text-right whitespace-nowrap">
                      <button disabled={just.trim().length < 3} onClick={() => decidir([e.protocolo], "INCLUIR")} className="px-2 py-1 text-xs bg-emerald-600 rounded mr-1 disabled:opacity-40">Incluir</button>
                      <button disabled={just.trim().length < 3} onClick={() => decidir([e.protocolo], "EXCLUIR")} className="px-2 py-1 text-xs bg-slate-600 rounded disabled:opacity-40">Excluir</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {sel.bloqueios.length > 0 && (
        <div className="mb-6 bg-red-900/40 border border-red-700 text-red-200 px-4 py-2 rounded text-sm">
          Bloqueio: protocolos duplicados com valores diferentes no SGA ({sel.bloqueios.join(", ")}). Corrija a exportação.
        </div>
      )}

      <section className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
        <h3 className="font-bold text-white mb-3">Maiores eventos selecionados ({num(itens.total)} no total)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-400 uppercase">
              <tr><th className="text-left p-2">Protocolo</th><th className="text-left p-2">Motivo</th><th className="text-left p-2">Finalização</th><th className="text-right p-2">Custo</th><th className="text-left p-2">Origem</th><th className="text-left p-2">Alertas</th></tr>
            </thead>
            <tbody>
              {itens.items.map((e) => (
                <tr key={e.protocolo} className="border-t border-slate-700">
                  <td className="p-2 font-mono">{e.protocolo}</td><td className="p-2">{e.motivo}</td>
                  <td className="p-2">{e.data_finalizacao ? e.data_finalizacao.split("-").reverse().join("/") : "-"}</td>
                  <td className="p-2 text-right">R$ {brl(e.custo_evento)}</td>
                  <td className="p-2 text-xs">{e.origem === "REGRA" ? "Fila do SGA" : "Decisão do operador"}</td>
                  <td className="p-2 text-xs text-amber-300">{e.alertas.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {sel.auditoria.length > 0 && (
        <details className="mb-6 text-xs text-slate-400">
          <summary className="cursor-pointer text-slate-300">Trilha de auditoria ({sel.auditoria.length}{sel.auditoria.length === 50 ? "+" : ""} registros)</summary>
          <ul className="mt-2 space-y-1 font-mono">{sel.auditoria.map((a, i) => <li key={i}>{a}</li>)}</ul>
        </details>
      )}

      <button onClick={irParaLanc} disabled={!sel.homologavel}
        className="px-6 py-2 bg-emerald-500 text-slate-900 font-bold rounded disabled:opacity-40">
        Seguir para os lançamentos
      </button>
    </div>
  )
}

// ─────────────────────────── Lançamentos ───────────────────────────

const SUGESTOES = ["RASTREAMENTO", "E-SAUDE", "INADIMPLÊNCIA", "RECEITA COM VENDAS DE SALVADOS", "RECEBIDOS (recuperação de inadimplência)"]

function Lancamentos({ mes, sel, rodar, onAtualizar, irParaResultado, irParaRodar }) {
  const [linhas, setLinhas] = useState(null)
  useEffect(() => {
    if (!sel) return
    pedir(`/avap/${enc(mes)}/lancamentos`).then((l) => setLinhas(l.map((x) => ({ descricao: x.descricao, valor: String(x.valor) }))))
  }, [sel, mes])
  if (!sel) return <Vazio texto="Nenhum fechamento carregado." acao={irParaRodar} rotulo="Carregar arquivos" />
  if (!linhas) return null

  const set = (i, k, v) => setLinhas(linhas.map((l, j) => (j === i ? { ...l, [k]: v } : l)))
  const valor = (l) => parseFloat(String(l.valor).replace(/\./g, "").replace(",", ".")) || parseFloat(l.valor) || 0
  const total = linhas.reduce((a, l) => a + valor(l), 0)
  const salvar = () => rodar(async () => {
    onAtualizar(await post(`/avap/${enc(mes)}/lancamentos`, {
      lancamentos: linhas.filter((l) => l.descricao.trim().length > 1 && valor(l) !== 0).map((l) => ({ descricao: l.descricao, valor: valor(l) })),
    }))
    irParaResultado()
  }, "Salvando os lançamentos")

  return (
    <div className="max-w-3xl">
      <h2 className="text-xl font-bold text-white mb-1">Linhas de soma e dedução</h2>
      <p className="text-slate-400 text-sm mb-4">
        Entram no numerador junto com o custo dos eventos. Valor positivo soma, valor negativo deduz. O código contábil é reconhecido pela descrição.
      </p>
      <div className="space-y-2 mb-3">
        {linhas.map((l, i) => (
          <div key={i} className="flex gap-2">
            <input list="sugestoes" value={l.descricao} onChange={(e) => set(i, "descricao", e.target.value)} placeholder="Descrição"
              className="flex-1 px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white text-sm" />
            <input value={l.valor} onChange={(e) => set(i, "valor", e.target.value)} placeholder="0,00"
              className={`w-40 px-3 py-2 bg-slate-800 border border-slate-600 rounded text-sm text-right ${valor(l) < 0 ? "text-red-300" : "text-emerald-300"}`} />
            <button onClick={() => setLinhas(linhas.filter((_, j) => j !== i))} className="px-3 bg-slate-700 rounded text-sm">Remover</button>
          </div>
        ))}
        <datalist id="sugestoes">{SUGESTOES.map((s) => <option key={s} value={s} />)}</datalist>
      </div>
      <div className="flex gap-3 items-center flex-wrap">
        <button onClick={() => setLinhas([...linhas, { descricao: "", valor: "" }])} className="px-4 py-2 bg-slate-700 rounded text-sm">Adicionar linha</button>
        <span className="text-sm text-slate-400">Saldo das linhas: <b className={total < 0 ? "text-red-300" : "text-emerald-300"}>R$ {brl(total)}</b></span>
        <button onClick={salvar} className="ml-auto px-6 py-2 bg-emerald-500 text-slate-900 font-bold rounded">Salvar e ir ao resultado</button>
      </div>
    </div>
  )
}

// ─────────────────────────── Resultado ───────────────────────────

function Resultado({ mes, sel, res, criterio, setCriterio, calcular, busy, irParaRodar }) {
  if (!sel) return <Vazio texto="Nenhum fechamento carregado." acao={irParaRodar} rotulo="Carregar arquivos" />
  return (
    <div>
      <section className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
        <div className="flex gap-4 items-end flex-wrap">
          <label className="text-sm">
            <div className="text-slate-400 mb-1">Quem entra no denominador (cotas)</div>
            <select value={criterio} onChange={(e) => setCriterio(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white">
              {Object.entries(CRITERIOS).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select>
          </label>
          <button onClick={calcular} disabled={busy || !sel.homologavel}
            className="px-6 py-2 bg-emerald-500 text-slate-900 font-bold rounded disabled:opacity-40">
            {res ? "Recalcular" : "Calcular rateio"}
          </button>
          {!sel.homologavel && <span className="text-sm text-amber-300">Resolva as pendências na aba Seleção.</span>}
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Este critério ainda aguarda confirmação da AVAP. O valor por cota abaixo é uma estimativa e muda de acordo com ele.
        </p>
      </section>

      {!res ? <Vazio texto={`Rateio de ${mes} ainda não calculado.`} /> : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Card label="Custo dos eventos" value={`R$ ${brl(res.custo_eventos)}`} sub={`${num(sel.selecionados)} eventos`} />
            <Card label="Linhas de soma" value={`+ R$ ${brl(res.somas)}`} tone="green" />
            <Card label="Linhas de dedução" value={`- R$ ${brl(res.deducoes)}`} tone="red" />
            <Card label="Total a ratear" value={`R$ ${brl(res.numerador)}`} tone="amber" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <Card label="Cotas no denominador" value={num(res.total_cotas)} sub={`${num(res.veiculos_elegiveis)} veículos`} />
            <Card label="Valor por cota" value={`R$ ${brl(res.valor_cota)}`} tone="green" sub={CRITERIOS[res.criterio]} />
            <Card label="Boletos" value={num(res.total_boletos)} sub={`R$ ${brl(res.total_rateio)} somados`} />
            <Card label="Diferença de arredondamento" value={`R$ ${brl(res.diferenca_arredondamento)}`} sub="reportada, nunca redistribuída" tone={res.aprovado ? "green" : "red"} />
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <section className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="font-bold text-white mb-2">Valor por cota em cada critério</h3>
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(res.comparativo_criterios).map(([k, v]) => (
                    <tr key={k} className={`border-t border-slate-700 ${k === res.criterio ? "text-emerald-300 font-semibold" : ""}`}>
                      <td className="p-2">{CRITERIOS[k]}</td><td className="p-2 text-right">R$ {brl(v)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
            <section className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="font-bold text-white mb-2">Veículos fora do denominador</h3>
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(res.veiculos_fora).map(([k, v]) => (
                    <tr key={k} className="border-t border-slate-700"><td className="p-2">{k.replaceAll("_", " ").toLowerCase()}</td><td className="p-2 text-right">{num(v)}</td></tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>

          <section className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
            <h3 className="font-bold text-white mb-2">Composição do total a ratear</h3>
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-t border-slate-700"><td className="p-2">Eventos selecionados</td><td className="p-2 text-right">R$ {brl(res.custo_eventos)}</td></tr>
                {res.lancamentos.map((l, i) => (
                  <tr key={i} className="border-t border-slate-700">
                    <td className="p-2">{l.descricao} <span className="text-xs text-slate-500">{l.codigo}</span></td>
                    <td className={`p-2 text-right ${l.tipo === "DEDUCAO" ? "text-red-300" : "text-emerald-300"}`}>{l.tipo === "DEDUCAO" ? "-" : "+"} R$ {brl(l.valor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <div className="flex gap-3 flex-wrap text-xs">
            {Object.entries(res.invariantes).map(([k, ok]) => (
              <span key={k} className={`px-3 py-1 rounded ${ok ? "bg-emerald-900/50 text-emerald-300" : "bg-red-900/50 text-red-300"}`}>
                {ok ? "OK" : "FALHA"}: {k.replaceAll("_", " ")}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ─────────────────────────── Boletos ───────────────────────────

function Boletos({ mes, res }) {
  const [q, setQ] = useState("")
  const [page, setPage] = useState(1)
  const [data, setData] = useState({ total: 0, soma_rateio: 0, items: [] })
  const [ocultar, setOcultar] = useState(true)
  const PS = 20
  const carregar = useCallback(() => {
    if (!res) return
    pedir(`/avap/${enc(mes)}/boletos?q=${encodeURIComponent(q)}&page=${page}&page_size=${PS}`).then(setData).catch(() => {})
  }, [mes, res, q, page])
  useEffect(carregar, [carregar])
  if (!res) return <Vazio texto="Calcule o rateio para gerar os boletos." />

  const paginas = Math.max(1, Math.ceil(data.total / PS))
  return (
    <div>
      <div className="flex gap-3 mb-4 items-center flex-wrap">
        <input value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} placeholder="Buscar por placa ou matrícula"
          className="px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white text-sm w-64" />
        <label className="text-sm text-slate-300 flex items-center gap-2">
          <input type="checkbox" checked={ocultar} onChange={(e) => setOcultar(e.target.checked)} /> Ocultar placas na tela
        </label>
        <span className="text-sm text-slate-400">{num(data.total)} boletos · R$ {brl(data.soma_rateio)}</span>
        <a href={`${API}/avap/${enc(mes)}/boletos.csv`} className="ml-auto px-4 py-2 bg-slate-700 rounded text-sm text-white">Baixar CSV</a>
      </div>
      <div className="overflow-x-auto bg-slate-800 border border-slate-700 rounded-lg">
        <table className="w-full text-sm">
          <thead className="text-xs text-slate-400 uppercase">
            <tr><th className="text-left p-2">Placa</th><th className="text-left p-2">Matrícula</th><th className="text-right p-2">Peso da cota</th><th className="text-right p-2">Contribuição do rateio</th><th className="text-right p-2">Total do boleto</th></tr>
          </thead>
          <tbody>
            {data.items.map((b, i) => (
              <tr key={i} className="border-t border-slate-700">
                <td className="p-2 font-mono">{ocultar ? mascara(b.placa) : (b.placa || "-")}</td>
                <td className="p-2">{ocultar ? "****" : (b.matricula ?? "-")}</td>
                <td className="p-2 text-right">{brl(b.peso_cota)}</td>
                <td className="p-2 text-right">R$ {brl(b.contribuicao_rateio)}</td>
                <td className="p-2 text-right font-semibold">R$ {brl(b.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex gap-3 items-center justify-end mt-3 text-sm">
        <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 bg-slate-700 rounded disabled:opacity-40">Anterior</button>
        <span>Página {page} de {num(paginas)}</span>
        <button disabled={page >= paginas} onClick={() => setPage(page + 1)} className="px-3 py-1 bg-slate-700 rounded disabled:opacity-40">Próxima</button>
      </div>
    </div>
  )
}
