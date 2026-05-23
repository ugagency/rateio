import { useState, useEffect, useCallback } from 'react'

const API = ""
const mesAnteriorPadrao = () => {
  const d = new Date()
  d.setDate(1); d.setMonth(d.getMonth() - 1)
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}
const MES_PADRAO = mesAnteriorPadrao()
const enc = (m) => encodeURIComponent(m)
const brl = (v) => (typeof v === 'number' ? v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : v)

const TABS = {
  visao: "Visão Geral",
  segmentos: "Segmentos",
  eventos: "Eventos",
  ajuste: "Ajuste",
  boletos: "Boletos",
  auditoria: "Auditoria",
  rodarmes: "Rodar Mês",
}

export default function AutoTruck() {
  const [tab, setTab] = useState("visao")
  const [mes, setMes] = useState(MES_PADRAO)
  const [res, setRes] = useState(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(false)

  const carregar = useCallback(() => {
    fetch(`${API}/autotruck/${enc(mes)}`)
      .then(r => (r.ok ? r.json() : Promise.reject(r)))
      .then(setRes)
      .catch(() => setRes(null))
  }, [mes])

  // App começa ZERADO: nada é carregado no mount. As telas só populam após o
  // usuário disparar o rateio (Calcular/Recalcular, PoC Remonta, Processar
  // planilhas). Por isso NÃO há auto-load aqui.

  // Trocar o mês também zera as telas — evita mostrar dados de um mês sob o
  // rótulo de outro. Só recarrega ao clicar num botão-gatilho.
  const trocarMes = (novo) => { setMes(novo); setRes(null); setErro("") }

  const calcular = () => {
    setCarregando(true); setErro("")
    fetch(`${API}/autotruck/calcular`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mes_ano_ref: mes, force: true }),
    })
      .then(r => (r.ok ? r.json() : Promise.reject(r)))
      .then(d => { setRes(d); setTab("visao") })
      .catch(() => setErro("Falha ao calcular o rateio AutoTruck."))
      .finally(() => setCarregando(false))
  }

  const carregarPocRemonta = () => {
    setCarregando(true); setErro("")
    fetch(`${API}/autotruck/poc-remonta?mes_ano_ref=04/2026`, { method: "POST" })
      .then(r => (r.ok ? r.json() : r.json().then(j => Promise.reject(j))))
      .then(d => { setMes("04/2026"); setRes(d.resultado); setTab("visao") })
      .catch(e => setErro(`PoC Remonta: ${e?.detail || "falha ao carregar"}`))
      .finally(() => setCarregando(false))
  }

  return (
    <div className="bg-slate-900 text-slate-200 min-h-[calc(100vh-44px)]">
      <header className="border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <div className="text-xs uppercase tracking-widest text-cyan-400">Motor de Rateio · Modelo Elo Ajustado</div>
            <h1 className="text-2xl font-bold text-white">AutoTruck — Rateio Segmentado</h1>
          </div>
          <div className="text-right text-xs text-slate-500">LC 213/2024 · D+5</div>
        </div>
        <nav className="max-w-7xl mx-auto px-6 pb-4 flex gap-2 flex-wrap items-center">
          {Object.entries(TABS).map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`px-4 py-2 rounded text-sm font-semibold ${tab === k ? "bg-cyan-500 text-slate-900" : "bg-slate-700 text-slate-200"}`}>
              {l}
            </button>
          ))}
          <span className="ml-auto flex gap-2 items-center">
            <input value={mes} onChange={e => trocarMes(e.target.value)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-white text-sm w-24"
              placeholder="MM/AAAA" />
            <button onClick={calcular} disabled={carregando}
              title="Recalcula sobre os dados já carregados no servidor para este mês (não usa os arquivos da aba Rodar Mês)"
              className="px-4 py-1.5 bg-cyan-500 text-slate-900 font-bold rounded text-sm disabled:opacity-50">
              {carregando ? "Calculando…" : "Calcular / Recalcular"}
            </button>
            <button onClick={carregarPocRemonta} disabled={carregando}
              title="Carrega Remonta/BASE + Rateio_POC e roda o motor em 04/2026"
              className="px-4 py-1.5 bg-amber-400 text-slate-900 font-bold rounded text-sm disabled:opacity-50">
              PoC Remonta
            </button>
          </span>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {erro && <div className="mb-4 bg-red-900/40 border border-red-700 text-red-200 px-4 py-2 rounded">{erro}</div>}
        {/* RodarMes vive num ÚNICO lugar estável da árvore — independente de `res` —
            senão a transição res null→objeto após "Processar" remonta o componente
            e zera os arquivos escolhidos + os <input> nativos. */}
        {tab === "rodarmes" ? (
          <RodarMes mes={mes} setMes={setMes} onCalculado={carregar} onRodado={() => { carregar(); setTab("visao") }} />
        ) : !res ? (
          <div className="text-center py-20">
            <h2 className="text-3xl font-bold text-white mb-4">Nenhum rateio AutoTruck para {mes}</h2>
            <p className="text-slate-300 mb-6">Bases separadas LEVES / MOTOS (variável) e PESADOS (pote fixo de casco caminhão).</p>
            <div className="flex gap-3 justify-center">
              <button onClick={calcular} disabled={carregando}
                className="px-6 py-3 bg-cyan-500 text-slate-900 font-bold rounded-lg disabled:opacity-50">
                {carregando ? "Calculando…" : "Calcular Rateio"}
              </button>
              <button onClick={carregarPocRemonta} disabled={carregando}
                className="px-6 py-3 bg-amber-400 text-slate-900 font-bold rounded-lg disabled:opacity-50">
                Carregar PoC Remonta (04/2026)
              </button>
            </div>
          </div>
        ) : (
          <>
            {tab === "visao" && <Visao res={res} />}
            {tab === "segmentos" && <Segmentos mes={mes} />}
            {tab === "eventos" && <Eventos mes={mes} />}
            {tab === "ajuste" && <Ajuste mes={mes} onAplicado={carregar} />}
            {tab === "boletos" && <Boletos mes={mes} />}
            {tab === "auditoria" && <Auditoria mes={mes} />}
          </>
        )}
      </main>
    </div>
  )
}

function Card({ label, value, sub, tone = "slate" }) {
  const tones = { slate: "text-white", ok: "text-emerald-300", warn: "text-amber-300", bad: "text-red-300" }
  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-2xl font-bold mt-2 ${tones[tone]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  )
}

function Visao({ res }) {
  const c = res.consolidado
  return (
    <div>
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 mb-6 border border-slate-700 flex flex-wrap gap-8 justify-between">
        <div>
          <div className="text-xs text-cyan-400 uppercase tracking-widest">Cota LEVES</div>
          <div className="text-4xl font-black text-white">R$ {brl(c.cota_leves)}</div>
        </div>
        <div>
          <div className="text-xs text-cyan-400 uppercase tracking-widest">Cota MOTOS</div>
          <div className="text-4xl font-black text-white">R$ {brl(c.cota_motos)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400 uppercase tracking-widest">Invariante de Auditoria</div>
          <div className={`text-4xl font-black ${c.invariante_ok ? "text-emerald-400" : "text-red-400"}`}>
            {c.invariante_ok ? "OK · Δ 0,00" : `Δ ${brl(c.diferenca_total)}`}
          </div>
        </div>
        <div className="flex items-center">
          <a
            href={`${API}/autotruck/${enc(res.mes_ano_ref)}/export-analitico`}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-5 py-3 font-bold text-white shadow-lg transition-colors"
            title="Exporta a aba ANALITICO no layout do FECHAMENTO, preenchida com os números deste mês. Campos de faturamento (VALOR RECEBIDO, RESUMO, FORNECEDOR) saem em branco com nota de origem."
          >
            ⬇ Exportar ANALITICO (.xlsx)
          </a>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card label="Veículos elegíveis" value={`${c.total_veiculos_elegiveis} / ${c.total_veiculos}`} sub="modelo purista (ativo + adimplente)" />
        <Card label="Cotas LEVES / MOTOS" value={`${brl(c.total_cotas_leves)} / ${brl(c.total_cotas_motos)}`} />
        <Card label="Custo a ratear LEVES" value={`R$ ${brl(c.custo_a_ratear_leves)}`} sub={`integral+parcial (terceiro não abate · pote ${brl(c.recuperacao_terceiros_leves)})`} />
        <Card label="Custo a ratear MOTOS" value={`R$ ${brl(c.custo_a_ratear_motos)}`} sub={`integral+parcial (terceiro não abate · pote ${brl(c.recuperacao_terceiros_motos)})`} />
        <Card label="Estabilização trimestral" value={c.alerta_variacao_trimestral ? "⚠ Variação > ±5%" : "OK · dentro de ±5%"} tone={c.alerta_variacao_trimestral ? "warn" : "ok"} sub="cota vs média dos últimos 3 meses" />
        <Card label="Eventos alocados" value={c.eventos_alocados} sub={`${c.eventos_postergados} postergados`} />
        <Card label="Reclassif. regra 75%" value={c.eventos_reclassificados_75pct} sub="parcial → integral (perda total)" />
        <Card label="Pote Caminhão (reserva)" value={`R$ ${brl(c.pote_caminhao_reserva)}`} tone={c.pote_caminhao_reserva >= 0 ? "ok" : "bad"} sub={`arrec ${brl(c.pote_caminhao_arrecadado)} · custo ${brl(c.pote_caminhao_custo)}`} />
        <Card label="Pote Terceiros (reserva)" value={`R$ ${brl(c.pote_terceiros_reserva)}`} tone={c.pote_terceiros_reserva >= 0 ? "ok" : "bad"} sub={`arrec ${brl(c.pote_terceiros_arrecadado)} · custo ${brl(c.pote_terceiros_custo)}`} />
      </div>
    </div>
  )
}

function useFetch(url) {
  const [d, setD] = useState(null)
  useEffect(() => { fetch(url).then(r => (r.ok ? r.json() : Promise.reject(r))).then(setD).catch(() => setD(null)) }, [url])
  return d
}

function Segmentos({ mes }) {
  const segs = useFetch(`${API}/autotruck/${enc(mes)}/segmentos`)
  if (!segs) return <p className="text-slate-400">Sem dados.</p>
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {segs.map(s => (
        <div key={s.segmento} className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <div className="flex justify-between items-baseline">
            <div className="text-xl font-bold text-white">{s.segmento}</div>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-cyan-300">{s.modo}</span>
          </div>
          {s.modo === "RATEIO_VARIAVEL" ? (
            <div className="text-3xl font-black text-cyan-300 mt-2">R$ {brl(s.valor_cota)}<span className="text-sm text-slate-400"> /cota</span></div>
          ) : (
            <div className="text-2xl font-black text-amber-300 mt-2">Pote fixo</div>
          )}
          <dl className="mt-4 text-sm space-y-1">
            <Row k="Integrais" v={s.custo_integrais} />
            <Row k="Parciais" v={s.custo_parciais} />
            <Row k="Salvados liq." v={-s.deducao_salvados} />
            <Row k="Custo a ratear" v={s.custo_a_ratear} bold />
            {s.modo === "RATEIO_VARIAVEL" && <Row k="Cotas ativas" v={s.cotas_ativas} plain />}
            {s.modo === "RATEIO_VARIAVEL" && <Row k="Média 3M (estab.)" v={s.media_cota_3m} />}
            {s.modo === "RATEIO_VARIAVEL" && (
              <div className="flex justify-between border-t border-slate-700/60 pt-1">
                <dt className="text-slate-400">Variação vs média</dt>
                <dd className={s.alerta_variacao_trimestral ? "font-bold text-amber-300" : "text-slate-200"}>
                  {(s.variacao_vs_media * 100).toFixed(1)}%
                </dd>
              </div>
            )}
            <Row k="Terceiros (pote, não abate)" v={s.recuperacao_terceiros} />
            {s.modo === "POTE_FIXO" && <Row k="Arrecadado" v={s.arrecadado} />}
            {s.modo === "POTE_FIXO" && <Row k="Reserva/Déficit" v={s.reserva_ou_deficit} bold />}
          </dl>
          <div className={`mt-3 text-xs px-2 py-1 rounded ${s.faixa_estabilizacao === "OK" && !s.alerta_variacao_trimestral ? "bg-emerald-900/40 text-emerald-300" : "bg-amber-900/40 text-amber-300"}`}>
            {(s.alerta_volatilidade || s.alerta_variacao_trimestral) && "⚠ "}{s.sugestao}
          </div>
        </div>
      ))}
    </div>
  )
}

function Row({ k, v, bold, plain }) {
  return (
    <div className="flex justify-between border-t border-slate-700/60 pt-1">
      <dt className="text-slate-400">{k}</dt>
      <dd className={bold ? "font-bold text-white" : "text-slate-200"}>{plain ? brl(v) : `R$ ${brl(v)}`}</dd>
    </div>
  )
}

// Tipos das colunas ordenáveis: "num" compara numérico, "str" alfabético.
const COLS_ORDENAVEIS = { data_aviso: "str", tipo_evento: "str", custo_a_ratear: "num" }

function Eventos({ mes }) {
  const [seg, setSeg] = useState("")
  // sortKey === null → ordem natural FIFO (vinda do backend)
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState("asc")
  const data = useFetch(`${API}/autotruck/${enc(mes)}/eventos${seg ? `?segmento=${seg}` : ""}`)
  const items = data?.items || []

  function toggleSort(key) {
    if (sortKey === key) { setSortDir(d => (d === "asc" ? "desc" : "asc")) }
    else { setSortKey(key); setSortDir("asc") }
  }

  let ordenados = items
  if (sortKey) {
    const tipo = COLS_ORDENAVEIS[sortKey]
    const fator = sortDir === "asc" ? 1 : -1
    ordenados = [...items].sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey]
      // valores ausentes vão sempre para o fim, independente da direção
      const na = va === null || va === undefined || va === ""
      const nb = vb === null || vb === undefined || vb === ""
      if (na && nb) return 0
      if (na) return 1
      if (nb) return -1
      const cmp = tipo === "num" ? (va - vb) : String(va).localeCompare(String(vb), "pt-BR")
      return cmp * fator
    })
  }

  // Cabeçalho clicável com indicador de ordenação
  const ThSort = ({ k, children, alinhaDir }) => (
    <th onClick={() => toggleSort(k)} title="Clique para ordenar"
      className={`px-3 py-2 cursor-pointer select-none hover:bg-slate-600 ${alinhaDir ? "text-right" : ""}`}>
      {children}
      <span className="ml-1 text-cyan-400">{sortKey === k ? (sortDir === "asc" ? "▲" : "▼") : "↕"}</span>
    </th>
  )

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {["", "LEVES", "MOTOS", "PESADOS"].map(s => (
          <button key={s || "todos"} onClick={() => setSeg(s)}
            className={`px-3 py-1.5 rounded text-xs font-semibold ${seg === s ? "bg-cyan-500 text-slate-900" : "bg-slate-700 text-slate-300"}`}>
            {s || "Todos"}
          </button>
        ))}
        <span className="ml-auto text-sm text-slate-400 self-center">
          {data?.total ?? 0} eventos {sortKey ? `(ordenado: ${sortKey === "custo_a_ratear" ? "custo" : sortKey === "data_aviso" ? "data" : "tipo"} ${sortDir === "asc" ? "↑" : "↓"})` : "(FIFO)"}
        </span>
      </div>
      <div className="bg-slate-800 rounded-xl border border-slate-700 max-h-[520px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-700 text-left">
            <tr>
              <th className="px-3 py-2">#FIFO</th><th className="px-3 py-2">Protocolo</th><th className="px-3 py-2">Seg</th>
              <th className="px-3 py-2">Envolv.</th>
              <ThSort k="data_aviso">Data aviso</ThSort>
              <ThSort k="tipo_evento">Tipo</ThSort>
              <ThSort k="custo_a_ratear" alinhaDir>Custo a ratear</ThSort>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {ordenados.slice(0, 300).map((e, i) => (
              <tr key={i} className="border-t border-slate-600">
                <td className="px-3 py-1.5">{e.ordem_fifo}</td>
                <td className="px-3 py-1.5">{e.protocolo}</td>
                <td className="px-3 py-1.5">{e.segmento}</td>
                <td className="px-3 py-1.5">{e.envolvimento}</td>
                <td className="px-3 py-1.5">{e.data_aviso}</td>
                <td className="px-3 py-1.5">{e.tipo_evento}{e.reclassificado_75pct && <span className="ml-1 text-amber-400" title="reclassificado pela regra dos 75%">★</span>}</td>
                <td className="px-3 py-1.5 text-right">R$ {brl(e.custo_a_ratear)}</td>
                <td className={`px-3 py-1.5 ${e.status === "POSTERGADO" ? "text-amber-400" : "text-emerald-300"}`}>{e.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Potes({ mes }) {
  const potes = useFetch(`${API}/autotruck/${enc(mes)}/potes`)
  if (!potes) return <p className="text-slate-400">Sem dados.</p>
  return (
    <div>
      <h2 className="text-xl font-bold text-white mb-4">Potes Fixos (não entram na divisão de cotas)</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {potes.map(s => (
          <div key={s.segmento} className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="text-lg font-bold text-white mb-2">Casco {s.segmento}</div>
            <dl className="text-sm space-y-1">
              <Row k="Arrecadado" v={s.arrecadado} />
              <Row k="Custo" v={s.custo_a_ratear} />
              <Row k="Reserva / Déficit" v={s.reserva_ou_deficit} bold />
            </dl>
            <div className={`mt-3 text-xs px-2 py-1 rounded ${s.reserva_ou_deficit >= 0 ? "bg-emerald-900/40 text-emerald-300" : "bg-red-900/40 text-red-300"}`}>{s.sugestao}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Boletos({ mes }) {
  const [seg, setSeg] = useState("")
  const data = useFetch(`${API}/autotruck/${enc(mes)}/boletos?limit=500${seg ? `&segmento=${seg}` : ""}`)
  const items = data?.items || []
  return (
    <div>
      <div className="flex gap-2 mb-4">
        {["", "LEVES", "MOTOS", "PESADOS"].map(s => (
          <button key={s || "todos"} onClick={() => setSeg(s)}
            className={`px-3 py-1.5 rounded text-xs font-semibold ${seg === s ? "bg-cyan-500 text-slate-900" : "bg-slate-700 text-slate-300"}`}>
            {s || "Todos"}
          </button>
        ))}
        <span className="ml-auto text-sm text-slate-400 self-center">{data?.total ?? 0} boletos</span>
      </div>
      <div className="bg-slate-800 rounded-xl border border-slate-700 max-h-[520px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-700 text-left">
            <tr>
              <th className="px-3 py-2">Veículo</th><th className="px-3 py-2">Placa</th><th className="px-3 py-2">Seg</th>
              <th className="px-3 py-2 text-right">FIPE</th><th className="px-3 py-2 text-right">Cotas</th>
              <th className="px-3 py-2 text-right">Rateio</th><th className="px-3 py-2 text-right">Potes</th>
              <th className="px-3 py-2 text-right">Total</th><th className="px-3 py-2">Emite</th>
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 200).map((b, i) => (
              <tr key={i} className="border-t border-slate-600">
                <td className="px-3 py-1.5">{b.id_veiculo}</td>
                <td className="px-3 py-1.5">{b.placa}</td>
                <td className="px-3 py-1.5">{b.segmento}</td>
                <td className="px-3 py-1.5 text-right">{brl(b.valor_fipe)}</td>
                <td className="px-3 py-1.5 text-right">{b.qtd_cotas}{b.cota_especial && <span className="ml-1 text-amber-400" title="cota especial high-end">♦</span>}</td>
                <td className="px-3 py-1.5 text-right">R$ {brl(b.custo_rateio)}</td>
                <td className="px-3 py-1.5 text-right">R$ {brl(b.custo_pote_terceiros + b.custo_pote_caminhao)}</td>
                <td className="px-3 py-1.5 text-right font-semibold text-emerald-300">R$ {brl(b.valor_total_boleto)}</td>
                <td className="px-3 py-1.5">{b.gera_boleto ? "Sim" : "Não"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Auditoria({ mes }) {
  const data = useFetch(`${API}/autotruck/${enc(mes)}/auditoria`)
  const items = data?.items || []
  return (
    <div>
      <h2 className="text-xl font-bold text-white mb-2">Trilha de Auditoria (log imutável · LC 213 / D&O)</h2>
      <p className="text-slate-400 text-sm mb-4">Toda exclusão/inclusão manual de evento exige justificativa técnica e é registrada aqui.</p>
      {items.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center text-slate-400">
          Nenhuma intervenção manual neste fechamento.
        </div>
      ) : (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-700 text-left">
              <tr><th className="px-3 py-2">Ação</th><th className="px-3 py-2">Evento</th><th className="px-3 py-2">Justificativa</th><th className="px-3 py-2">Timestamp</th></tr>
            </thead>
            <tbody>
              {items.map((a, i) => (
                <tr key={i} className="border-t border-slate-600">
                  <td className="px-3 py-1.5 text-amber-300">{a.acao}</td>
                  <td className="px-3 py-1.5">{a.id_evento}</td>
                  <td className="px-3 py-1.5">{a.justificativa}</td>
                  <td className="px-3 py-1.5 text-slate-500">{a.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function RodarMes({ mes, setMes, onRodado, onCalculado }) {
  const [base, setBase] = useState(slotInicial())
  const [rateio, setRateio] = useState(slotInicial())
  const [produtos, setProdutos] = useState(slotInicial())
  const [cotasLeves, setCotasLeves] = useState("")
  const [cotasMotos, setCotasMotos] = useState("")
  // se o usuário digitar manualmente, marcamos para não sobrescrever com auto-fill
  const [cotasLevesManual, setCotasLevesManual] = useState(false)
  const [cotasMotosManual, setCotasMotosManual] = useState(false)
  const [busy, setBusy] = useState(false)
  const [resp, setResp] = useState(null)
  const [erro, setErro] = useState("")

  // inspeção no onChange — valida + (se BASE) auto-preenche cotas
  const inspecionar = async (file, slot, setSlot) => {
    if (!file) { setSlot(slotInicial()); return }
    setSlot({ file, status: "inspecionando", tipo: null, erro: null })
    try {
      const fd = new FormData()
      fd.append("arquivo", file)
      fd.append("slot_esperado", slot)
      const r = await fetch(`${API}/autotruck/inspecionar-arquivo`, { method: "POST", body: fd })
      const d = await r.json()
      setSlot({ file, status: d.valido ? "ok" : "erro", tipo: d.tipo_detectado, erro: d.erro })
      // auto-preenche cotas se BASE válida e usuário ainda não digitou nada
      if (slot === "BASE" && d.valido && d.extras?.cotas_baixadas) {
        const cm = d.extras.cotas_baixadas.MOTOS
        if (cm && !cotasMotosManual) setCotasMotos(String(cm))
        // LEVES não vem da BASE do Rodrigo — deixa o usuário preencher
      }
    } catch (e) {
      setSlot({ file, status: "erro", tipo: null, erro: "Falha na inspeção." })
    }
  }

  const calcular = (e) => {
    e?.preventDefault()
    if (!base.file || !rateio.file) {
      setErro("Selecione pelo menos os arquivos BASE e RATEIO.")
      return
    }
    if (base.status === "erro" || rateio.status === "erro" || produtos.status === "erro") {
      setErro("Há arquivos no slot errado. Corrija antes de calcular.")
      return
    }
    setBusy(true); setErro(""); setResp(null)
    const fd = new FormData()
    fd.append("base", base.file)
    fd.append("rateio", rateio.file)
    if (produtos.file) fd.append("produtos", produtos.file)
    fd.append("mes_ano_ref", mes)
    if (cotasLeves) fd.append("cotas_leves", cotasLeves)
    if (cotasMotos) fd.append("cotas_motos", cotasMotos)
    fetch(`${API}/autotruck/rodar-mes`, { method: "POST", body: fd })
      .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject(t)))
      .then(d => {
        setResp(d)
        // após sucesso, sincroniza o estado do pai (popula as outras abas)
        if (typeof onCalculado === "function") onCalculado()
      })
      .catch(t => setErro(typeof t === "string" ? t : "Falha ao processar."))
      .finally(() => setBusy(false))
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-white mb-1">Rodar Mês — upload de planilhas</h2>
      <p className="text-slate-400 text-sm mb-4">
        Selecione os arquivos do mês (BASE + RATEIO; PRODUTOS opcional) que vieram da AutoTruck.
        Validação acontece já na seleção. Se a BASE trouxer cotas, os overrides preenchem sozinhos.
      </p>

      <form onSubmit={calcular} className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4">
        <FileRow label="BASE — Pagamentos recebidos × pendentes" required slot={base}
          onPick={f => inspecionar(f, "BASE", setBase)}
          hint="Aba 'BASE' com 3 segmentos lado a lado (LEVES/MOTOS/PESADOS), valores por situação de boleto." />
        <FileRow label="RATEIO — Eventos sinistrados do mês" required slot={rateio}
          onPick={f => inspecionar(f, "RATEIO", setRateio)}
          hint="Lista de eventos por seção (PESADOS TERCEIROS, MOTOS ASSOCIADOS, LEVES ASSOCIADOS, etc.) com Valor Rateado." />
        <FileRow label="PRODUTOS — Catálogo fornecedor (opcional)" slot={produtos}
          onPick={f => inspecionar(f, "PRODUTOS", setProdutos)}
          hint="FORNECEDOR/SERVIÇO/PRODUTO/TIPO/QTD/VALOR/TOTAL — usado para fechamento de fornecedores." />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-3 border-t border-slate-700">
          <label className="text-sm">
            <span className="text-slate-400 block mb-1">Mês de referência (MM/AAAA)</span>
            <input value={mes} onChange={e => setMes(e.target.value)} placeholder={MES_PADRAO}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white" />
          </label>
          <label className="text-sm">
            <span className="text-slate-400 block mb-1">Cotas LEVES (override — opc.)</span>
            <input value={cotasLeves}
              onChange={e => { setCotasLeves(e.target.value); setCotasLevesManual(true) }}
              placeholder="quando a BASE não traz"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white" />
          </label>
          <label className="text-sm">
            <span className="text-slate-400 block mb-1">Cotas MOTOS (override — opc.)</span>
            <input value={cotasMotos}
              onChange={e => { setCotasMotos(e.target.value); setCotasMotosManual(true) }}
              placeholder="auto-preenche pela BASE"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white" />
          </label>
        </div>

        <div className="flex gap-3 items-center pt-3">
          <button type="submit" disabled={busy}
            title="Ingere as planilhas selecionadas (BASE + RATEIO + PRODUTOS) e roda o motor sobre elas"
            className="px-5 py-2 bg-cyan-500 text-slate-900 font-bold rounded disabled:opacity-50">
            {busy ? "Processando…" : "Processar planilhas"}
          </button>
          {erro && <div className="text-red-300 text-sm">{erro}</div>}
        </div>
      </form>

      {resp && <RodarMesResultado resp={resp} onAbrir={onRodado} />}
    </div>
  )
}

const slotInicial = () => ({ file: null, status: "vazio", tipo: null, erro: null })

function FileRow({ label, hint, slot, onPick, required }) {
  const { file, status, tipo, erro } = slot
  const badge = {
    vazio:         null,
    inspecionando: <span className="text-xs text-slate-400">inspecionando…</span>,
    ok:            <span className="text-xs text-emerald-300">✓ {file?.name} · detectado: {tipo}</span>,
    erro:          <span className="text-xs text-red-300">✗ {file?.name} · {tipo || "?"}</span>,
  }[status]
  return (
    <div>
      <label className="block">
        <div className="flex justify-between mb-1">
          <span className="text-sm font-semibold text-slate-200">
            {label}{required && <span className="text-red-400 ml-1">*</span>}
          </span>
          {badge}
        </div>
        <input type="file" accept=".xlsx,.xls"
          onChange={e => onPick(e.target.files?.[0] || null)}
          className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-slate-700 file:text-cyan-300 hover:file:bg-slate-600" />
        {hint && !erro && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
        {erro && <p className="text-xs text-red-300 mt-1">{erro}</p>}
      </label>
    </div>
  )
}

function RodarMesResultado({ resp, onAbrir }) {
  const c = resp.resultado.consolidado
  const ing = resp.ingestao
  return (
    <div className="mt-6 bg-slate-800 border border-emerald-700/40 rounded-xl p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-emerald-400">Resultado processado</div>
          <h3 className="text-lg font-bold text-white">Mês {resp.resultado.mes_ano_ref} · {ing.eventos_total} eventos · {ing.veiculos_total.toLocaleString('pt-BR')} veículos sintetizados</h3>
        </div>
        <button onClick={onAbrir} className="px-4 py-1.5 bg-emerald-500 text-slate-900 font-bold rounded text-sm">
          Abrir na Visão Geral →
        </button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card label="Cota LEVES" value={`R$ ${brl(c.cota_leves)}`} sub={`${ing.cotas_leves.toLocaleString('pt-BR')} cotas`} tone="ok" />
        <Card label="Cota MOTOS" value={`R$ ${brl(c.cota_motos)}`} sub={`${ing.cotas_motos.toLocaleString('pt-BR')} cotas`} tone="ok" />
        <Card label="Bruto LEVES" value={`R$ ${brl(c.bruto_leves)}`} sub={`+ terceiros R$ ${brl(c.recuperacao_terceiros_leves)}`} />
        <Card label="Bruto MOTOS" value={`R$ ${brl(c.bruto_motos)}`} sub={`+ terceiros R$ ${brl(c.recuperacao_terceiros_motos)}`} />
        <Card label="Invariante" value={c.invariante_ok ? "OK · Δ 0,00" : `Δ ${brl(c.diferenca_total)}`} tone={c.invariante_ok ? "ok" : "bad"} />
        <Card label="Eventos alocados" value={c.eventos_alocados} sub={`${c.eventos_postergados} postergados`} />
        <Card label="Reclassif. 75%" value={c.eventos_reclassificados_75pct} sub="parcial → integral" />
        <Card label="Pote Terceiros" value={`R$ ${brl(c.pote_terceiros_reserva)}`} tone={c.pote_terceiros_reserva >= 0 ? "ok" : "bad"} sub={`arrec R$ ${brl(c.pote_terceiros_arrecadado)}`} />
      </div>
      <details className="mt-4 text-xs text-slate-400">
        <summary className="cursor-pointer hover:text-slate-200">Detalhes da ingestão (seções, valores recebidos, catálogo)</summary>
        <pre className="mt-2 p-3 bg-slate-900 rounded overflow-x-auto">{JSON.stringify(ing, null, 2)}</pre>
      </details>
    </div>
  )
}

function Ajuste({ mes, onAplicado }) {
  const [alvo, setAlvo] = useState("")
  const [incluirParciais, setIncluirParciais] = useState(false)
  const [sugs, setSugs] = useState(null)
  const [msg, setMsg] = useState("")
  const [busy, setBusy] = useState(false)

  const sugerir = () => {
    setBusy(true); setMsg("")
    fetch(`${API}/autotruck/sugerir-ajuste`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mes_ano_ref: mes,
        alvo_cota: alvo === "" ? null : Number(alvo),
        incluir_parciais: incluirParciais,
      }),
    })
      .then(r => (r.ok ? r.json() : Promise.reject(r)))
      .then(setSugs)
      .catch(() => setMsg("Falha ao gerar sugestão (calcule o rateio primeiro)."))
      .finally(() => setBusy(false))
  }

  const aplicar = (seg, ids) => {
    if (!ids.length) return
    setBusy(true); setMsg("")
    fetch(`${API}/autotruck/aplicar-ajuste`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mes_ano_ref: mes, ids_eventos: ids }),
    })
      .then(r => (r.ok ? r.json() : Promise.reject(r)))
      .then(() => { setMsg(`Ajuste aplicado em ${seg}: ${ids.length} evento(s) postergado(s) (registrado na auditoria).`); setSugs(null); onAplicado && onAplicado() })
      .catch(() => setMsg("Falha ao aplicar o ajuste."))
      .finally(() => setBusy(false))
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-white mb-1">Assistente de Ajuste</h2>
      <p className="text-slate-400 text-sm mb-4">Conjunto mínimo de eventos a postergar para a cota atingir o alvo (estabilização &gt; FIFO; integral recente primeiro — oficina/nota fechada raramente se mexe).</p>
      <div className="flex flex-wrap gap-3 items-center mb-4">
        <label className="text-sm text-slate-400">Alvo da cota R$
          <input value={alvo} onChange={e => setAlvo(e.target.value)} placeholder="auto (média 3M ±5%)"
            className="ml-2 px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-white text-sm w-40" />
        </label>
        <label className="text-sm text-slate-300 flex items-center gap-2">
          <input type="checkbox" checked={incluirParciais} onChange={e => setIncluirParciais(e.target.checked)} />
          incluir parciais
        </label>
        <button onClick={sugerir} disabled={busy}
          className="px-4 py-1.5 bg-cyan-500 text-slate-900 font-bold rounded text-sm disabled:opacity-50">
          {busy ? "…" : "Sugerir"}
        </button>
      </div>
      {msg && <div className="mb-4 bg-slate-800 border border-slate-700 text-slate-200 px-4 py-2 rounded text-sm">{msg}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(sugs || []).map(s => (
          <div key={s.segmento} className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex justify-between items-baseline">
              <div className="text-lg font-bold text-white">{s.segmento}</div>
              <span className={`text-xs px-2 py-0.5 rounded ${s.precisa_ajuste ? (s.atingiu_alvo ? "bg-amber-900/40 text-amber-300" : "bg-red-900/40 text-red-300") : "bg-emerald-900/40 text-emerald-300"}`}>
                {s.precisa_ajuste ? (s.atingiu_alvo ? "ajuste sugerido" : "insuficiente") : "dentro do alvo"}
              </span>
            </div>
            <div className="mt-2 text-sm text-slate-300">
              Cota atual <b className="text-white">R$ {brl(s.cota_atual)}</b> · alvo <b className="text-white">R$ {brl(s.alvo_cota)}</b>
              {s.precisa_ajuste && <> → resultante <b className={s.atingiu_alvo ? "text-emerald-300" : "text-amber-300"}>R$ {brl(s.cota_resultante)}</b></>}
            </div>
            <div className="mt-2 text-xs text-slate-400">{s.mensagem}</div>
            {s.eventos_sugeridos.length > 0 && (
              <>
                <table className="w-full text-sm mt-3">
                  <thead className="text-left text-slate-400">
                    <tr><th className="py-1">Protocolo</th><th>Data aviso</th><th>Tipo</th><th className="text-right">Custo</th></tr>
                  </thead>
                  <tbody>
                    {s.eventos_sugeridos.map((e, i) => (
                      <tr key={i} className="border-t border-slate-700/60">
                        <td className="py-1">{e.protocolo}</td>
                        <td>{e.data_aviso}</td>
                        <td>{e.tipo_evento}</td>
                        <td className="text-right">R$ {brl(e.custo_a_ratear)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button onClick={() => aplicar(s.segmento, s.eventos_sugeridos.map(e => e.id_evento))}
                  disabled={busy}
                  className="mt-3 px-4 py-1.5 bg-amber-500 text-slate-900 font-bold rounded text-sm disabled:opacity-50">
                  Aplicar (postergar {s.eventos_sugeridos.length})
                </button>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
