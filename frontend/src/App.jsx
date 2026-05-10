import { useState, useEffect } from 'react'

const API = ""

function App() {
  const [tab, setTab] = useState("overview")
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json()).then(console.log).catch(console.error)
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      <header className="border-b border-slate-700 bg-slate-900">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <div className="text-xs uppercase tracking-widest text-slate-400">Demo MVP - Motor de Rateio</div>
            <h1 className="text-2xl font-bold text-white">Rateio & Faturamento</h1>
          </div>
          <div className="text-right text-xs text-slate-500">Mutualiza - LC 213/2025</div>
        </div>
        <nav className="max-w-7xl mx-auto px-6 pb-4 flex gap-2 flex-wrap">
          {["overview","potinhos","eventos","boletos","auditoria"].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded text-sm font-semibold ${tab===t ? "bg-amber-500 text-slate-900" : "bg-slate-700 text-slate-200"}`}>
              {{overview:"Visao Geral",potinhos:"Potinhos",eventos:"Eventos",boletos:"Boletos",auditoria:"Auditoria"}[t]}
            </button>
          ))}
        </nav>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">
        {tab === "overview" && <Overview />}
        {tab === "potinhos" && <Potinhos />}
        {tab === "eventos" && <Eventos />}
        {tab === "boletos" && <Boletos />}
        {tab === "auditoria" && <Auditoria />}
      </main>
    </div>
  )
}

function Overview() {
  const [consol, setConsol] = useState(null)
  useEffect(() => {
    const m = new Date().toISOString().slice(0,7)
    fetch(`${API}/rateio/${m}`)
      .then(r => r.json())
      .then(d => setConsol(d))
      .catch(e => console.error("No rateio yet:", e))
  }, [])
  
  if (!consol) return (
    <div className="text-center py-20">
      <h2 className="text-3xl font-bold text-white mb-4">Nenhum rateio calculado ainda</h2>
      <p className="text-slate-300 mb-6">Clique no botao abaixo para calcular o rateio do mes.</p>
      <button onClick={() => {
        fetch(`${API}/rateio/calcular`, {method:"POST"})
          .then(r => r.json()).then(d => {alert("Rateio calculado!"); window.location.reload()})
          .catch(e => alert("Erro: " + e.message))
      }} className="px-6 py-3 bg-amber-500 text-slate-900 font-bold rounded-lg hover:bg-amber-400">
        Calcular Rateio
      </button>
    </div>
  )

  return (
    <div>
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-10 mb-8 border border-slate-700">
        <h2 className="text-3xl font-bold text-white mb-4">Alvo do mes: R$ {consol.valor_alvo_total?.toLocaleString('pt-BR')}</h2>
        <p className="text-slate-300">{consol.total_veiculos_elegiveis} veiculos · {consol.total_cotas_apuradas?.toLocaleString('pt-BR')} cotas</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          {l:"Veiculos", v:consol.total_veiculos_elegiveis},
          {l:"Cotas", v:consol.total_cotas_apuradas?.toLocaleString('pt-BR')},
          {l:"Alvo R$", v:consol.valor_alvo_total?.toLocaleString('pt-BR')},
          {l:"Eventos", v:consol.eventos_alocados},
        ].map((c,i) => (
          <div key={i} className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="text-xs text-slate-400">{c.l}</div>
            <div className="text-3xl font-bold mt-2">{c.v}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Potinhos() {
  const [consol, setConsol] = useState(null)
  useEffect(() => {
    const m = new Date().toISOString().slice(0,7)
    fetch(`${API}/rateio/${m}`).then(r => r.json()).then(setConsol).catch(() => {})
  }, [])
  
  const pots = consol?.valor_distribuido ? [
    {i:1,n:"P1 Roubo/Furto", v:consol.valor_distribuido.p1 || 0, d:14},
    {i:2,n:"P2 Moto FIP", v:consol.valor_distribuido.p2 || 0, d:4},
    {i:3,n:"P3 Venture 1", v:consol.valor_distribuido.p3 || 0, d:18},
    {i:4,n:"P4 Venture 2", v:consol.valor_distribuido.p4 || 0, d:18},
  ] : [{n:"...",v:0}]

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-4">Motor: 4 Potinhos</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
        {pots.map((p,i) => (
          <div key={i} className="bg-slate-800 rounded-xl p-5 border border-slate-700">
            <div className="text-xs text-amber-400">Potinho {p.n}</div>
            <div className="text-2xl text-white font-black mt-2">
              R$ {typeof p.v === 'number' ? p.v.toLocaleString('pt-BR') : p.v}
            </div>
            <div className="mt-3 bg-black/30 rounded h-24 flex items-end overflow-hidden">
              <div className="w-full bg-emerald-500 transition-all" style={{height: '80%'}}></div>
            </div>
            <div className="mt-3 text-xs text-slate-300">Degrau: R$ {p.d}/cota</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Eventos() {
  const [events, setEvents] = useState([])
  useEffect(() => {
    const m = new Date().toISOString().slice(0,7)
    fetch(`${API}/rateio/${m}/eventos`).then(r => r.json()).then(setEvents).catch(() => {})
  }, [])
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-4">Eventos Rateados</h2>
      <div className="bg-slate-800 rounded-xl border border-slate-700 max-h-[500px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-700">
            <tr><th className="px-3 py-2 text-left">ID</th><th className="px-3 py-2 text-left">Data</th><th className="px-3 py-2 text-right">Valor</th><th className="px-3 py-2 text-left">Status</th></tr>
          </thead>
          <tbody>
            {events.map((e,i) => (
              <tr key={i} className="border-t border-slate-600">
                <td className="px-3 py-1.5">{e.id_evento}</td>
                <td className="px-3 py-1.5">{e.data_ocorrencia_evento}</td>
                <td className="px-3 py-1.5 text-right">R$ {e.valor_rateado_neste_mes?.toLocaleString('pt-BR')}</td>
                <td className="px-3 py-1.5">{e.status_evento}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Boletos() {
  const [boletos, setBoletos] = useState([])
  const [filt, setFilt] = useState("")
  useEffect(() => {
    const m = new Date().toISOString().slice(0,7)
    fetch(`${API}/boletos/${m}`).then(r => r.json()).then(d => setBoletos(d.items || d)).catch(() => {})
  }, [])
  const filtered = boletos.filter(b => !filt || b.id_veiculo?.includes(filt))
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-4">Boletos</h2>
      <input className="px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white mb-4"
        placeholder="Filtrar por ID do veiculo..." value={filt} onChange={e => setFilt(e.target.value)} />
      <div className="bg-slate-800 rounded-xl border border-slate-700 max-h-[500px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-700">
            <tr><th className="px-3 py-2 text-left">ID</th><th className="px-3 py-2 text-left">Categoria</th><th className="px-3 py-2 text-right">Cotas</th><th className="px-3 py-2 text-right">Total</th><th className="px-3 py-2 text-left">Boleto</th></tr>
          </thead>
          <tbody>
            {filtered.slice(0,50).map((b,i) => (
              <tr key={i} className="border-t border-slate-600">
                <td className="px-3 py-1.5">{b.id_veiculo}</td>
                <td className="px-3 py-1.5">{b.tipo_categoria_risco}</td>
                <td className="px-3 py-1.5 text-right">{b.qtd_cotas}</td>
                <td className="px-3 py-1.5 text-right">R$ {b.valor_total_boleto?.toLocaleString('pt-BR')}</td>
                <td className="px-3 py-1.5">{b.gera_boleto ? "Sim" : "Nao"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Auditoria() {
  const [vid, setVid] = useState("")
  const [extrato, setExtrato] = useState(null)
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-4">Auditoria</h2>
      <input className="px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white mr-2"
        placeholder="VEI-000001" value={vid} onChange={e => setVid(e.target.value)} />
      <button onClick={() => {
        const m = new Date().toISOString().slice(0,7)
        fetch(`${API}/veiculos/${vid}/extrato/${m}`).then(r => r.json()).then(setExtrato).catch(() => {})
      }} className="px-4 py-2 bg-slate-700 rounded text-xs">Buscar</button>
      {extrato && (
        <div className="mt-4 bg-slate-800 p-6 rounded-xl">
          <div className="text-xl font-bold">{vid}</div>
          <div className="mt-3 grid grid-cols-3 gap-4">
            <div><div className="text-slate-400">Rateio</div><div>R$ {extrato.custo_rateio?.toLocaleString('pt-BR')}</div></div>
            <div><div className="text-slate-400">Fixos</div><div>R$ {extrato.custo_produtos_fixos?.toLocaleString('pt-BR')}</div></div>
            <div><div className="text-slate-400">Total</div><div className="font-bold text-emerald-300">R$ {extrato.valor_total_boleto?.toLocaleString('pt-BR')}</div></div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
