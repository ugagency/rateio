import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { competenciaParaExibicao } from "@/lib/competencia";

// Lista de situacoes de boleto (server component). A RLS restringe ao tenant
// do operador logado. Exibe as 50 situacoes mais recentes por padrao.
export default async function SituacoesBoletoPage() {
  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase
    .from("situacoes_boleto")
    .select(
      "id, veiculo_id, competencia, situacao, registrado_em, veiculos(placa, segmento)",
    )
    .order("competencia", { ascending: false })
    .order("registrado_em", { ascending: false })
    .limit(50);

  return (
    <section>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Situacoes de boleto</h1>
        <Link href="/app/situacoes-boleto/novo">+ Nova situacao</Link>
      </header>

      {error && <p style={{ color: "crimson" }}>Erro ao carregar: {error.message}</p>}

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
            <th>Placa</th>
            <th>Segmento</th>
            <th>Competencia</th>
            <th>Situacao</th>
            <th>Registrado em</th>
          </tr>
        </thead>
        <tbody>
          {(data ?? []).map((r) => {
            const veiculo = Array.isArray(r.veiculos) ? r.veiculos[0] : r.veiculos;
            return (
              <tr key={r.id} style={{ borderBottom: "1px solid #eee" }}>
                <td>{veiculo?.placa ?? r.veiculo_id}</td>
                <td>{veiculo?.segmento ?? "-"}</td>
                <td>{competenciaParaExibicao(r.competencia as string)}</td>
                <td>{r.situacao}</td>
                <td>{new Date(r.registrado_em as string).toLocaleDateString("pt-BR")}</td>
              </tr>
            );
          })}
          {(data ?? []).length === 0 && !error && (
            <tr>
              <td colSpan={5} style={{ padding: 16, color: "#666" }}>
                Nenhuma situacao de boleto registrada.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
