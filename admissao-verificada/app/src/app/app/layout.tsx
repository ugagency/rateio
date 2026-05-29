import type { ReactNode } from "react";
import Link from "next/link";

// Shell das rotas autenticadas (/app/*). Navegação mínima do MVP.
export default function AppLayout({ children }: { children: ReactNode }) {
  const itens = [
    { href: "/app/associados", rotulo: "Associados" },
    { href: "/app/veiculos", rotulo: "Veículos" },
    { href: "/app/vistorias", rotulo: "Vistorias" },
    { href: "/app/situacoes-boleto", rotulo: "Boletos" },
    { href: "/app/eventos", rotulo: "Eventos" },
    { href: "/app/exportacao", rotulo: "Exportação" },
  ];
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <nav style={{ width: 200, background: "#0f172a", color: "#fff", padding: 16 }}>
        <strong>Admissão</strong>
        <ul style={{ listStyle: "none", padding: 0, marginTop: 16 }}>
          {itens.map((i) => (
            <li key={i.href} style={{ margin: "8px 0" }}>
              <Link href={i.href} style={{ color: "#cbd5e1", textDecoration: "none" }}>
                {i.rotulo}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <main style={{ flex: 1, padding: 24 }}>{children}</main>
    </div>
  );
}
