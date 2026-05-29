"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { criarSituacaoBoletoSchema } from "@/lib/schemas/situacao-boleto";

// Cadastro de situacao de boleto (client). Valida no cliente para feedback
// imediato; a validacao autoritativa e do servidor.
export default function NovaSituacaoBoletoPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    veiculo_id: "",
    competencia: "",
    situacao: "baixado" as "baixado" | "aberto" | "cancelado",
  });
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  function setcampo<K extends keyof typeof form>(campo: K) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [campo]: e.target.value as (typeof form)[K] }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    const local = criarSituacaoBoletoSchema.safeParse(form);
    if (!local.success) {
      setErro(local.error.issues[0]?.message ?? "dados invalidos");
      return;
    }
    setSalvando(true);
    const resp = await fetch("/api/situacoes-boleto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSalvando(false);
    if (resp.status === 201) {
      router.push("/app/situacoes-boleto");
      router.refresh();
      return;
    }
    if (resp.status === 409) {
      setErro("Ja existe registro de situacao para esse veiculo nessa competencia");
      return;
    }
    if (resp.status === 404) {
      setErro("Veiculo nao encontrado na associacao ou sem acesso");
      return;
    }
    const body = await resp.json().catch(() => ({}));
    setErro(body.error ?? "nao foi possivel salvar");
  }

  return (
    <section style={{ maxWidth: 420 }}>
      <h1>Nova situacao de boleto</h1>
      <form onSubmit={salvar}>
        <label style={{ display: "block", margin: "8px 0" }}>
          ID do veiculo (UUID)
          <input
            type="text"
            value={form.veiculo_id}
            onChange={setcampo("veiculo_id")}
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Competencia (AAAA-MM)
          <input
            type="text"
            value={form.competencia}
            onChange={setcampo("competencia")}
            placeholder="2026-05"
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Situacao
          <select
            value={form.situacao}
            onChange={setcampo("situacao")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          >
            <option value="baixado">Baixado (pago)</option>
            <option value="aberto">Aberto (inadimplente)</option>
            <option value="cancelado">Cancelado</option>
          </select>
        </label>

        {erro && <p style={{ color: "crimson" }}>{erro}</p>}
        <button type="submit" disabled={salvando}>
          {salvando ? "Salvando..." : "Salvar"}
        </button>
      </form>
    </section>
  );
}
