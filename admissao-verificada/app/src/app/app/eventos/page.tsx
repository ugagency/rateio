import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { competenciaParaExibicao } from "@/lib/competencia";

// Lista de eventos do mes (server component). A RLS restringe ao tenant do
// operador logado. Exibe os 50 eventos mais recentes por padrao.
export default async function EventosPage() {
  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase
    .from("eventos_mes")
    .select(
      "id, competencia, marcador_secao, tipo, protocolo, placa, data_comunicacao, valor_rateado, status",
    )
    .eq("status", "ativo")
    .order("competencia", { ascending: false })
    .order("data_comunicacao", { ascending: true })
    .limit(50);

  return (
    <section>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Eventos do mes</h1>
        <Link href="/app/eventos/novo">+ Novo evento</Link>
      </header>

      {error && <p style={{ color: "crimson" }}>Erro ao carregar: {error.message}</p>}

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
            <th>Protocolo</th>
            <th>Placa</th>
            <th>Marcador de secao</th>
            <th>Tipo</th>
            <th>Data de comunicacao</th>
            <th>Competencia</th>
            <th>Valor rateado (R$)</th>
          </tr>
        </thead>
        <tbody>
          {(data ?? []).map((ev) => (
            <tr key={ev.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{ev.protocolo}</td>
              <td>{ev.placa}</td>
              <td>{ev.marcador_secao}</td>
              <td>{ev.tipo}</td>
              <td>
                {new Date(ev.data_comunicacao as string).toLocaleDateString("pt-BR", {
                  timeZone: "UTC",
                })}
              </td>
              <td>{competenciaParaExibicao(ev.competencia as string)}</td>
              <td style={{ textAlign: "right" }}>
                {Number(ev.valor_rateado).toLocaleString("pt-BR", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </td>
            </tr>
          ))}
          {(data ?? []).length === 0 && !error && (
            <tr>
              <td colSpan={7} style={{ padding: 16, color: "#666" }}>
                Nenhum evento cadastrado.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
