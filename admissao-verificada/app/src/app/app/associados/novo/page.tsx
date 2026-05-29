"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { criarAssociadoSchema } from "@/lib/schemas/associado";

// Cadastro de associado (client). Valida no cliente para feedback imediato; a
// validação autoritativa (CPF, duplicidade) é do route handler.
export default function NovoAssociadoPage() {
  const router = useRouter();
  const [form, setForm] = useState({ nome: "", cpf: "", email: "", telefone: "" });
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  function set(campo: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [campo]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    const local = criarAssociadoSchema.safeParse(form);
    if (!local.success) {
      setErro(local.error.issues[0]?.message ?? "dados inválidos");
      return;
    }
    setSalvando(true);
    const resp = await fetch("/api/associados", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSalvando(false);
    if (resp.status === 201) {
      router.push("/app/associados");
      router.refresh();
      return;
    }
    if (resp.status === 409) {
      setErro("CPF já cadastrado na associação");
      return;
    }
    const body = await resp.json().catch(() => ({}));
    setErro(body.error ?? "não foi possível salvar");
  }

  return (
    <section style={{ maxWidth: 420 }}>
      <h1>Novo associado</h1>
      <form onSubmit={salvar}>
        {(
          [
            ["nome", "Nome", "text"],
            ["cpf", "CPF", "text"],
            ["email", "E-mail (opcional)", "email"],
            ["telefone", "Telefone (opcional)", "text"],
          ] as const
        ).map(([campo, rotulo, tipo]) => (
          <label key={campo} style={{ display: "block", margin: "8px 0" }}>
            {rotulo}
            <input
              type={tipo}
              value={form[campo]}
              onChange={set(campo)}
              style={{ display: "block", width: "100%", marginTop: 4 }}
            />
          </label>
        ))}
        {erro && <p style={{ color: "crimson" }}>{erro}</p>}
        <button type="submit" disabled={salvando}>
          {salvando ? "Salvando..." : "Salvar"}
        </button>
      </form>
    </section>
  );
}
