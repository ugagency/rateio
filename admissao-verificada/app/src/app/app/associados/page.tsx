import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { mascararCpf } from "@/lib/validators/cpf";

// Lista de associados (server component). A RLS restringe ao tenant do operador.
export default async function AssociadosPage() {
  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase
    .from("associados")
    .select("id, nome, cpf, email, telefone, status, criado_em")
    .eq("status", "ativo")
    .order("nome", { ascending: true });

  return (
    <section>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Associados</h1>
        <Link href="/app/associados/novo">+ Novo associado</Link>
      </header>

      {error && <p style={{ color: "crimson" }}>Erro ao carregar: {error.message}</p>}

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
            <th>Nome</th>
            <th>CPF</th>
            <th>E-mail</th>
            <th>Telefone</th>
          </tr>
        </thead>
        <tbody>
          {(data ?? []).map((a) => (
            <tr key={a.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{a.nome}</td>
              <td>{mascararCpf(a.cpf)}</td>
              <td>{a.email ?? "-"}</td>
              <td>{a.telefone ?? "-"}</td>
            </tr>
          ))}
          {(data ?? []).length === 0 && (
            <tr>
              <td colSpan={4} style={{ padding: 16, color: "#666" }}>
                Nenhum associado cadastrado.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
