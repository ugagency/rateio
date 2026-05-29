import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";

// Painel de vistorias (server component). A RLS restringe ao tenant do
// operador logado. Exibe lista com status, veículo e script utilizado.

type VistoriaRow = {
  id: string;
  status: string;
  iniciado_em: string;
  finalizado_em: string | null;
  veiculos: { placa: string; segmento: string } | null;
  scripts_vistoria: { tipo: string; descricao: string | null } | null;
};

export default async function VistoriasPage() {
  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase
    .from("vistorias")
    .select(
      `id, status, iniciado_em, finalizado_em,
       veiculos (placa, segmento),
       scripts_vistoria (tipo, descricao)`,
    )
    .order("iniciado_em", { ascending: false })
    .limit(100);

  const rotulos: Record<string, string> = {
    a_realizar: "A realizar",
    finalizada: "Finalizada",
    expirada: "Expirada",
  };

  return (
    <section>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Vistorias</h1>
        <Link href="/app/vistorias/nova">+ Iniciar vistoria</Link>
      </header>

      {error && <p style={{ color: "crimson" }}>Erro ao carregar: {error.message}</p>}

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
            <th style={{ padding: "8px 4px" }}>Placa</th>
            <th style={{ padding: "8px 4px" }}>Segmento</th>
            <th style={{ padding: "8px 4px" }}>Tipo de script</th>
            <th style={{ padding: "8px 4px" }}>Status</th>
            <th style={{ padding: "8px 4px" }}>Iniciado em</th>
            <th style={{ padding: "8px 4px" }}>Finalizado em</th>
            <th style={{ padding: "8px 4px" }}>Acoes</th>
          </tr>
        </thead>
        <tbody>
          {(data as VistoriaRow[] ?? []).map((v) => (
            <tr key={v.id} style={{ borderBottom: "1px solid #eee" }}>
              <td style={{ padding: "8px 4px" }}>{v.veiculos?.placa ?? "-"}</td>
              <td style={{ padding: "8px 4px" }}>{v.veiculos?.segmento ?? "-"}</td>
              <td style={{ padding: "8px 4px" }}>{v.scripts_vistoria?.tipo ?? "-"}</td>
              <td style={{ padding: "8px 4px" }}>{rotulos[v.status] ?? v.status}</td>
              <td style={{ padding: "8px 4px" }}>
                {new Date(v.iniciado_em).toLocaleString("pt-BR")}
              </td>
              <td style={{ padding: "8px 4px" }}>
                {v.finalizado_em ? new Date(v.finalizado_em).toLocaleString("pt-BR") : "-"}
              </td>
              <td style={{ padding: "8px 4px" }}>
                <Link href={`/app/vistorias/${v.id}`}>Ver detalhes</Link>
              </td>
            </tr>
          ))}
          {(data ?? []).length === 0 && (
            <tr>
              <td colSpan={7} style={{ padding: 16, color: "#666" }}>
                Nenhuma vistoria registrada.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
