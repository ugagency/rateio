import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";

// Lista de veiculos (server component). A RLS restringe ao tenant do operador.
export default async function VeiculosPage() {
  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase
    .from("veiculos")
    .select(
      "id, associado_id, placa, segmento, fipe_valor, cobertura_terceiros, cota, status, criado_em",
    )
    .order("placa", { ascending: true });

  return (
    <section>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Veiculos</h1>
        <Link href="/app/veiculos/novo">+ Novo veiculo</Link>
      </header>

      {error && <p style={{ color: "crimson" }}>Erro ao carregar: {error.message}</p>}

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
            <th>Placa</th>
            <th>Segmento</th>
            <th>FIPE (R$)</th>
            <th>Cota</th>
            <th>Cobertura</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {(data ?? []).map((v) => (
            <tr key={v.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{v.placa}</td>
              <td>{v.segmento}</td>
              <td>{Number(v.fipe_valor).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</td>
              <td>{Number(v.cota).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</td>
              <td>{v.cobertura_terceiros}</td>
              <td>{v.status}</td>
            </tr>
          ))}
          {(data ?? []).length === 0 && (
            <tr>
              <td colSpan={6} style={{ padding: 16, color: "#666" }}>
                Nenhum veiculo cadastrado.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
