import { useState, useEffect } from 'react'
import AutoTruck from './AutoTruck'
import AVAP from './AVAP'
import Simulador from './Simulador'
import Menu from './Shell'

const API = ""

const mesAnteriorPadrao = () => {
  const d = new Date()
  d.setDate(1); d.setMonth(d.getMonth() - 1)
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}
const MES_PADRAO_ELLO = mesAnteriorPadrao()

function App() {
  const [tab, setTab] = useState("overview")
  const [mes, setMes] = useState(MES_PADRAO_ELLO)
  // Gate de sessão: o dashboard começa em branco a cada carregamento e só
  // passa a exibir dados depois que o usuário roda o rateio nesta sessão.
  const [rodou, setRodou] = useState(false)
  const irParaRodarMes = () => setTab("rodarmes")

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
        <nav className="max-w-7xl mx-auto px-6 pb-4 flex gap-2 flex-wrap items-center">
          {["overview","potinhos","eventos","boletos","auditoria","rodarmes"].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded text-sm font-semibold ${tab===t ? "bg-amber-500 text-slate-900" : "bg-slate-700 text-slate-200"}`}>
              {{overview:"Visao Geral",potinhos:"Potinhos",eventos:"Eventos",boletos:"Boletos",auditoria:"Auditoria",rodarmes:"Rodar Mês"}[t]}
            </button>
          ))}
          <span className="ml-auto flex items-center gap-2">
            <span className="text-xs text-slate-500">Mês</span>
            <input value={mes} onChange={e => setMes(e.target.value)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-white text-sm w-24"
              placeholder="MM/AAAA" />
          </span>
        </nav>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">
        {tab === "overview" && <Overview mes={mes} rodou={rodou} irParaRodarMes={irParaRodarMes} />}
        {tab === "potinhos" && <Potinhos mes={mes} rodou={rodou} irParaRodarMes={irParaRodarMes} />}
        {tab === "eventos" && <Eventos mes={mes} rodou={rodou} irParaRodarMes={irParaRodarMes} />}
        {tab === "boletos" && <Boletos mes={mes} rodou={rodou} irParaRodarMes={irParaRodarMes} />}
        {tab === "auditoria" && <Auditoria mes={mes} rodou={rodou} irParaRodarMes={irParaRodarMes} />}
        {tab === "rodarmes" && <RodarMesELLO mes={mes} setMes={setMes} onRodado={() => { setRodou(true); setTab("overview") }} />}
      </main>
    </div>
  )
}

// Estado inicial em branco do dashboard ELLO: enquanto o usuário não rodou o
// rateio nesta sessão, as abas mostram este aviso em vez de buscar dados.
function TelaVazia({ irParaRodarMes }) {
  return (
    <div className="text-center py-20">
      <h2 className="text-3xl font-bold text-white mb-4">Nenhum rateio nesta sessão</h2>
      <p className="text-slate-300 mb-6">Vá em "Rodar Mês", carregue as planilhas e calcule o rateio para preencher esta tela.</p>
      <button onClick={irParaRodarMes}
        className="px-5 py-2 bg-amber-500 text-slate-900 font-bold rounded">
        Ir para Rodar Mês →
      </button>
    </div>
  )
}

function Overview({ mes, rodou, irParaRodarMes }) {
  const [consol, setConsol] = useState(null)
  useEffect(() => {
    setConsol(null)
    if (!rodou) return
    fetch(`${API}/rateio/${encodeURIComponent(mes)}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => setConsol(d && d.valor_alvo_total !== undefined ? d : null))
      .catch(() => setConsol(null))
  }, [mes, rodou])

  if (!rodou) return <TelaVazia irParaRodarMes={irParaRodarMes} />
  if (!consol) return (
    <div className="text-center py-20">
      <h2 className="text-3xl font-bold text-white mb-4">Nenhum rateio para {mes}</h2>
      <p className="text-slate-300 mb-6">Vá na aba "Rodar Mês" para carregar as planilhas do mês desejado.</p>
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

function Potinhos({ mes, rodou, irParaRodarMes }) {
  const [consol, setConsol] = useState(null)
  useEffect(() => {
    setConsol(null)
    if (!rodou) return
    fetch(`${API}/rateio/${encodeURIComponent(mes)}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => setConsol(d && d.valor_alvo_total !== undefined ? d : null))
      .catch(() => setConsol(null))
  }, [mes, rodou])

  if (!rodou) return <TelaVazia irParaRodarMes={irParaRodarMes} />

  const pots = consol ? [
    { n: "P1 Roubo/Furto", v: consol.valor_p1_roubo_furto || 0, d: 14 },
    { n: "P2 Moto FIP",    v: consol.valor_p2_moto_fip    || 0, d: 4  },
    { n: "P3 Venture 1",   v: consol.valor_p3_venture_1   || 0, d: 18 },
    { n: "P4 Venture 2",   v: consol.valor_p4_venture_2   || 0, d: 18 },
  ] : []
  const total = pots.reduce((a, p) => a + p.v, 0)

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-1">Motor — 4 Potinhos</h2>
      <p className="text-slate-400 text-sm mb-4">
        {consol ? `Mês ${mes} · soma dos 4 potinhos = R$ ${total.toLocaleString('pt-BR')}` : `Sem rateio para ${mes}.`}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
        {pots.map((p, i) => (
          <div key={i} className="bg-slate-800 rounded-xl p-5 border border-slate-700">
            <div className="text-xs text-amber-400">{p.n}</div>
            <div className="text-2xl text-white font-black mt-2">
              R$ {p.v.toLocaleString('pt-BR')}
            </div>
            <div className="mt-3 bg-black/30 rounded h-24 flex items-end overflow-hidden">
              <div className="w-full bg-emerald-500 transition-all"
                style={{ height: total > 0 ? `${Math.max(5, (p.v / total) * 100)}%` : '0%' }} />
            </div>
            <div className="mt-3 text-xs text-slate-300">Degrau: R$ {p.d}/cota</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Eventos({ mes, rodou, irParaRodarMes }) {
  const [data, setData] = useState({ items: [], total: 0 })
  const [erro, setErro] = useState("")
  useEffect(() => {
    setData({ items: [], total: 0 })
    setErro("")
    if (!rodou) return
    fetch(`${API}/rateio/${encodeURIComponent(mes)}/eventos`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(d => setData({ items: Array.isArray(d?.items) ? d.items : [], total: d?.total ?? 0 }))
      .catch(e => setErro(typeof e === "string" ? e : "Falha ao carregar eventos."))
  }, [mes, rodou])

  if (!rodou) return <TelaVazia irParaRodarMes={irParaRodarMes} />
  const items = data.items
  return (
    <div>
      <div className="flex justify-between items-baseline mb-4">
        <h2 className="text-2xl font-bold text-white">Eventos Rateados</h2>
        <span className="text-sm text-slate-400">{data.total} eventos · mês {mes}</span>
      </div>
      {erro && <div className="mb-4 bg-red-900/40 border border-red-700 text-red-200 px-4 py-2 rounded text-sm">{erro}</div>}
      {items.length === 0 && !erro ? (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center text-slate-400">
          Nenhum evento rateado para {mes}. Vá em "Rodar Mês" e calcule o rateio primeiro.
        </div>
      ) : (
        <div className="bg-slate-800 rounded-xl border border-slate-700 max-h-[520px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-700 text-left">
              <tr>
                <th className="px-3 py-2">ID Evento</th>
                <th className="px-3 py-2">Data ocorrência</th>
                <th className="px-3 py-2 text-right">Valor total</th>
                <th className="px-3 py-2 text-right">Saldo antes</th>
                <th className="px-3 py-2 text-right">Rateado neste mês</th>
                <th className="px-3 py-2 text-right">Saldo após</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.slice(0, 500).map((e, i) => (
                <tr key={i} className="border-t border-slate-600">
                  <td className="px-3 py-1.5">{e.id_evento}</td>
                  <td className="px-3 py-1.5">{e.data_ocorrencia}</td>
                  <td className="px-3 py-1.5 text-right">R$ {e.valor_total_evento?.toLocaleString('pt-BR')}</td>
                  <td className="px-3 py-1.5 text-right">R$ {e.valor_saldo_antes?.toLocaleString('pt-BR')}</td>
                  <td className="px-3 py-1.5 text-right">R$ {e.valor_rateado_neste_mes?.toLocaleString('pt-BR')}</td>
                  <td className="px-3 py-1.5 text-right">R$ {e.valor_saldo_apos?.toLocaleString('pt-BR')}</td>
                  <td className={`px-3 py-1.5 ${e.status_evento === 'LIQUIDADO' ? 'text-emerald-300' : 'text-amber-300'}`}>{e.status_evento}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Boletos({ mes, rodou, irParaRodarMes }) {
  const [boletos, setBoletos] = useState([])
  const [filt, setFilt] = useState("")
  useEffect(() => {
    setBoletos([])
    if (!rodou) return
    fetch(`${API}/boletos/${encodeURIComponent(mes)}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(d => setBoletos(Array.isArray(d?.items) ? d.items : (Array.isArray(d) ? d : [])))
      .catch(() => setBoletos([]))
  }, [mes, rodou])

  if (!rodou) return <TelaVazia irParaRodarMes={irParaRodarMes} />
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

function Auditoria({ mes, rodou, irParaRodarMes }) {
  const [vid, setVid] = useState("")
  const [extrato, setExtrato] = useState(null)
  if (!rodou) return <TelaVazia irParaRodarMes={irParaRodarMes} />
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-4">Auditoria · mês {mes}</h2>
      <input className="px-3 py-2 bg-slate-800 border border-slate-600 rounded text-white mr-2"
        placeholder="VEI-000001" value={vid} onChange={e => setVid(e.target.value)} />
      <button onClick={() => {
        if (!vid) return
        fetch(`${API}/veiculos/${vid}/extrato/${encodeURIComponent(mes)}`)
          .then(r => r.ok ? r.json() : null).then(setExtrato).catch(() => setExtrato(null))
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

const slotInicialELLO = () => ({ file: null, status: "vazio", tipo: null, erro: null })

function RodarMesELLO({ mes, setMes, onRodado }) {
  const [veiculos, setVeiculos] = useState(slotInicialELLO())
  const [eventos, setEventos] = useState(slotInicialELLO())
  const [servicos, setServicos] = useState(slotInicialELLO())
  const [busy, setBusy] = useState(false)
  const [resp, setResp] = useState(null)
  const [erro, setErro] = useState("")

  const brl = (v) => typeof v === 'number' ? v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : v

  const inspecionar = async (file, slot, setSlot) => {
    if (!file) { setSlot(slotInicialELLO()); return }
    setSlot({ file, status: "inspecionando", tipo: null, erro: null })
    try {
      const fd = new FormData()
      fd.append("arquivo", file)
      fd.append("slot_esperado", slot)
      const r = await fetch(`${API}/rateio/inspecionar-arquivo`, { method: "POST", body: fd })
      const d = await r.json()
      setSlot({ file, status: d.valido ? "ok" : "erro", tipo: d.tipo_detectado, erro: d.erro })
    } catch (e) {
      setSlot({ file, status: "erro", tipo: null, erro: "Falha na inspeção." })
    }
  }

  const calcular = (e) => {
    e?.preventDefault()
    if (!veiculos.file || !eventos.file || !servicos.file) {
      setErro("Selecione os 3 arquivos: veículos, eventos e serviços.")
      return
    }
    if ([veiculos, eventos, servicos].some(s => s.status === "erro")) {
      setErro("Há arquivos no slot errado. Corrija antes de calcular.")
      return
    }
    setBusy(true); setErro(""); setResp(null)
    const fd = new FormData()
    fd.append("veiculos", veiculos.file)
    fd.append("eventos", eventos.file)
    fd.append("servicos", servicos.file)
    fd.append("mes_ano_ref", mes)
    fetch(`${API}/rateio/rodar-mes`, { method: "POST", body: fd })
      .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject(t)))
      .then(d => setResp(d))
      .catch(t => setErro(typeof t === "string" ? t : "Falha ao processar."))
      .finally(() => setBusy(false))
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-1">Rodar Mês — upload de planilhas (ELLO)</h2>
      <p className="text-slate-400 text-sm mb-4">
        Selecione as 3 planilhas de entrada (Veículos, Eventos, Serviços Fixos).
        Validação acontece já na seleção. O mês de referência vem do header (default: mês anterior).
      </p>

      <form onSubmit={calcular} className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4">
        <FileRowELLO label="Veículos — cadastro elegível" required slot={veiculos}
          onPick={f => inspecionar(f, "VEICULOS", setVeiculos)}
          hint="Colunas: ID_Veiculo, Status_Ativo, Data_Quebra, Tipo_Categoria_Risco, Qtd_Cotas, Tipo_Pagamento, Is_Funcionario" />
        <FileRowELLO label="Eventos — sinistros pendentes" required slot={eventos}
          onPick={f => inspecionar(f, "EVENTOS", setEventos)}
          hint="Colunas: ID_Evento, Data_Ocorrencia_Evento, Valor_Total_Evento, Valor_Saldo_Pendente" />
        <FileRowELLO label="Serviços fixos — produtos por veículo" required slot={servicos}
          onPick={f => inspecionar(f, "SERVICOS", setServicos)}
          hint="Colunas: ID_Veiculo, Taxa_Administrativa, Valor_Assistencia_24h, Valor_Outros_Produtos" />

        <div className="pt-3 border-t border-slate-700">
          <label className="text-sm">
            <span className="text-slate-400 block mb-1">Mês de referência (MM/AAAA — sincroniza com o header)</span>
            <input value={mes} onChange={e => setMes(e.target.value)} placeholder={MES_PADRAO_ELLO}
              className="w-full md:w-48 px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white" />
          </label>
        </div>

        <div className="flex gap-3 items-center pt-3">
          <button type="submit" disabled={busy}
            className="px-5 py-2 bg-amber-500 text-slate-900 font-bold rounded disabled:opacity-50">
            {busy ? "Processando…" : "Calcular Rateio"}
          </button>
          {erro && <div className="text-red-300 text-sm">{erro}</div>}
        </div>
      </form>

      {resp && (
        <div className="mt-6 bg-slate-800 border border-emerald-700/40 rounded-xl p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <div className="text-xs uppercase tracking-widest text-emerald-400">Resultado processado</div>
              <h3 className="text-lg font-bold text-white">Mês {resp.resultado.mes_ano_ref} · {resp.ingestao.veiculos.toLocaleString('pt-BR')} veículos · {resp.ingestao.eventos} eventos</h3>
            </div>
            <button onClick={onRodado} className="px-4 py-1.5 bg-emerald-500 text-slate-900 font-bold rounded text-sm">
              Abrir na Visão Geral →
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <CardELLO label="Alvo do mês" value={`R$ ${brl(resp.resultado.consolidado.valor_alvo_total)}`} tone="ok" />
            <CardELLO label="Veículos elegíveis" value={resp.ingestao.veiculos_elegiveis.toLocaleString('pt-BR')} sub={`de ${resp.ingestao.veiculos.toLocaleString('pt-BR')} cadastrados`} />
            <CardELLO label="Cotas apuradas" value={resp.resultado.consolidado.total_cotas_apuradas?.toLocaleString('pt-BR')} />
            <CardELLO label="Invariante" value={resp.resultado.consolidado.diferenca_alvo_vs_alocado === 0 ? "OK · Δ 0,00" : `Δ ${brl(resp.resultado.consolidado.diferenca_alvo_vs_alocado)}`} tone={resp.resultado.consolidado.diferenca_alvo_vs_alocado === 0 ? "ok" : "bad"} />
            <CardELLO label="P1 Roubo/Furto" value={`R$ ${brl(resp.resultado.consolidado.valor_p1_roubo_furto)}`} />
            <CardELLO label="P2 Moto FIP" value={`R$ ${brl(resp.resultado.consolidado.valor_p2_moto_fip)}`} />
            <CardELLO label="P3 Venture 1" value={`R$ ${brl(resp.resultado.consolidado.valor_p3_venture_1)}`} />
            <CardELLO label="P4 Venture 2" value={`R$ ${brl(resp.resultado.consolidado.valor_p4_venture_2)}`} />
            <CardELLO label="Eventos alocados" value={resp.resultado.consolidado.eventos_alocados} sub={`${resp.resultado.consolidado.eventos_liquidados} liquidados · ${resp.resultado.consolidado.eventos_parciais} parciais`} />
            <CardELLO label="Boletos a emitir" value={resp.resultado.total_boletos_a_emitir} sub={`de ${resp.resultado.total_boletos} total`} />
            <CardELLO label="Receita esperada" value={`R$ ${brl(resp.resultado.receita_total_esperada)}`} />
            <CardELLO label="Saldo p/ próximo mês" value={`R$ ${brl(resp.resultado.consolidado.saldo_para_proximo_mes)}`} />
          </div>
          <details className="mt-4 text-xs text-slate-400">
            <summary className="cursor-pointer hover:text-slate-200">Detalhes da ingestão</summary>
            <pre className="mt-2 p-3 bg-slate-900 rounded overflow-x-auto">{JSON.stringify(resp.ingestao, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  )
}

function FileRowELLO({ label, hint, slot, onPick, required }) {
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
          className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-slate-700 file:text-amber-300 hover:file:bg-slate-600" />
        {hint && !erro && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
        {erro && <p className="text-xs text-red-300 mt-1">{erro}</p>}
      </label>
    </div>
  )
}

function CardELLO({ label, value, sub, tone = "slate" }) {
  const tones = { slate: "text-white", ok: "text-emerald-300", warn: "text-amber-300", bad: "text-red-300" }
  return (
    <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-xl font-bold mt-1 ${tones[tone]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  )
}

// Seletor de produto (novo menu). O componente ELLO `App` e seus filhos
// permanecem inalterados — apenas embrulhados por este wrapper aditivo.
function Root() {
  // ?feira na URL: só a demonstração Fenaprove e o simulador (esconde ELLO, AutoTruck e AVAP real).
  // ?equipe na URL: mostra no simulador o atalho para ver e baixar os contatos.
  const params = new URLSearchParams(window.location.search)
  const feira = params.has("feira")
  const equipe = params.has("equipe")
  const todos = [["ello", "ELLO · Rateio & Faturamento"], ["autotruck", "AutoTruck · Modelo Ello retreinado"], ["avap", "AVAP · Rateio em pote único"], ["fenauto", "Fenaprove · Demonstração"], ["simulador", "Simulador rápido"]]
  const produtos = feira ? todos.filter(([k]) => k === "fenauto" || k === "simulador") : todos
  const [produto, setProduto] = useState(feira ? "fenauto" : "ello")
  return (
    <div className="mut mut-shell">
      <Menu produtos={produtos} produto={produto} onEscolher={setProduto} />
      <div className="mut-conteudo">
        {produto === "ello" ? <App /> : produto === "autotruck" ? <AutoTruck /> : produto === "fenauto" ? <AVAP key="fenauto" fenauto /> : produto === "simulador" ? <Simulador equipe={equipe} /> : <AVAP key="avap" />}
      </div>
    </div>
  )
}

export default Root
