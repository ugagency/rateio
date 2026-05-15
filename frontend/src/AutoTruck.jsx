import { useState, useEffect, useCallback } from 'react'

const API = ""
const MES_PADRAO = "12/2025"
const enc = (m) => encodeURIComponent(m)
const brl = (v) => (typeof v === 'number' ? v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : v)

const TABS = {
  visao: "Visão Geral",
  segmentos: "Segmentos",
  eventos: "Eventos",
  potes: "Potes Fixos",
  boletos: "Boletos",
  auditoria: "Auditoria",
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

  useEffect(() => { carregar() }, [carregar])

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
            <input value={mes} onChange={e => setMes(e.target.value)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-white text-sm w-24"
              placeholder="MM/AAAA" />
            <button onClick={calcular} disabled={carregando}
              className="px-4 py-1.5 bg-cyan-500 text-slate-900 font-bold rounded text-sm disabled:opacity-50">
              {carregando ? "Calculando…" : "Calcular / Recalcular"}
            </button>
          </span>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {erro && <div className="mb-4 bg-red-900/40 border border-red-700 text-red-200 px-4 py-2 rounded">{erro}</div>}
        {!res ? (
          <div className="text-center py-20">
            <h2 className="text-3xl font-bold text-white mb-4">Nenhum rateio AutoTruck para {mes}</h2>
            <p className="text-slate-300 mb-6">Bases separadas LEVES / MOTOS (variável) e PESADOS (pote fixo de casco caminhão).</p>
            <button onClick={calcular} disabled={carregando}
              className="px-6 py-3 bg-cyan-500 text-slate-900 font-bold rounded-lg disabled:opacity-50">
              {carregando ? "Calculando…" : "Calcular Rateio"}
            </button>
          </div>
        ) : (
          <>
            {tab === "visao" && <Visao res={res} />}
            {tab === "segmentos" && <Segmentos mes={mes} />}
            {tab === "eventos" && <Eventos mes={mes} />}
            {tab === "potes" && <Potes mes={mes} />}
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
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card label="Veículos elegíveis" value={`${c.total_veiculos_elegiveis} / ${c.total_veiculos}`} sub="modelo purista (ativo + adimplente)" />
        <Card label="Cotas LEVES / MOTOS" value={`${brl(c.total_cotas_leves)} / ${brl(c.total_cotas_motos)}`} />
        <Card label="Custo a ratear LEVES" value={`R$ ${brl(c.custo_a_ratear_leves)}`} sub={`bruto ${brl(c.bruto_leves)} − terceiros ${brl(c.recuperacao_terceiros_leves)}`} />
        <Card label="Custo a ratear MOTOS" value={`R$ ${brl(c.custo_a_ratear_motos)}`} sub={`bruto ${brl(c.bruto_motos)} − terceiros ${brl(c.recuperacao_terceiros_motos)}`} />
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
            <Row k="Recup. terceiros" v={-s.recuperacao_terceiros} />
            <Row k="Custo a ratear" v={s.custo_a_ratear} bold />
            {s.modo === "RATEIO_VARIAVEL" && <Row k="Cotas ativas" v={s.cotas_ativas} plain />}
            {s.modo === "POTE_FIXO" && <Row k="Arrecadado" v={s.arrecadado} />}
            {s.modo === "POTE_FIXO" && <Row k="Reserva/Déficit" v={s.reserva_ou_deficit} bold />}
          </dl>
          <div className={`mt-3 text-xs px-2 py-1 rounded ${s.faixa_estabilizacao === "OK" ? "bg-emerald-900/40 text-emerald-300" : "bg-amber-900/40 text-amber-300"}`}>
            {s.alerta_volatilidade && "⚠ "}{s.sugestao}
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

function Eventos({ mes }) {
  const [seg, setSeg] = useState("")
  const data = useFetch(`${API}/autotruck/${enc(mes)}/eventos${seg ? `?segmento=${seg}` : ""}`)
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
        <span className="ml-auto text-sm text-slate-400 self-center">{data?.total ?? 0} eventos (FIFO)</span>
      </div>
      <div className="bg-slate-800 rounded-xl border border-slate-700 max-h-[520px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-700 text-left">
            <tr>
              <th className="px-3 py-2">#FIFO</th><th className="px-3 py-2">Protocolo</th><th className="px-3 py-2">Seg</th>
              <th className="px-3 py-2">Envolv.</th><th className="px-3 py-2">Data aviso</th><th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2 text-right">Custo a ratear</th><th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 300).map((e, i) => (
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
