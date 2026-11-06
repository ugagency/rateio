import './Mutualiza.css'

// Ícones do menu lateral (traço simples, herdam a cor do texto)
const ICONES = {
  ello: <><rect x="5" y="3" width="14" height="18" rx="3" /><path d="M8.5 8h7M8.5 12.5h.01M12 12.5h.01M15.5 12.5h.01M8.5 16.5h.01M12 16.5h.01M15.5 16.5h.01" /></>,
  autotruck: <><path d="M3 7h11v9H3zM14 10h4l3 3v3h-7" /><circle cx="7.5" cy="17.5" r="1.8" /><circle cx="17.5" cy="17.5" r="1.8" /></>,
  avap: <><path d="M12 3l9 5-9 5-9-5 9-5z" /><path d="M3 13l9 5 9-5" /></>,
  fenauto: <><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" /><path d="M9 12l2 2 4-4" /></>,
  simulador: <><path d="M4 7h10M18 7h2M4 17h2M10 17h10" /><circle cx="16" cy="7" r="2" /><circle cx="8" cy="17" r="2" /></>,
}
const ROTULOS = { ello: "ELLO", autotruck: "AutoTruck", avap: "AVAP", fenauto: "Fenaprove", simulador: "Simulador" }

export default function Menu({ produtos, produto, onEscolher }) {
  return (
    <aside className="mut-rail">
      {/* Logo: trocar o "M" por <img src="/logo-mutualiza.svg" alt="Mutualiza" /> quando houver o arquivo oficial. */}
      <div className="mut-rail-logo" aria-hidden="true">M</div>
      <nav aria-label="Produtos" className="mut-rail-nav">
        {produtos.map(([k, nome]) => (
          <button key={k} type="button" onClick={() => onEscolher(k)} title={nome} aria-label={nome}
            aria-current={produto === k ? "page" : undefined} className="mut-rail-item">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
              strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{ICONES[k]}</svg>
            <span>{ROTULOS[k] || nome}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}
