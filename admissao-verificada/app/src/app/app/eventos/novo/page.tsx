"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { criarEventoSchema } from "@/lib/schemas/evento";
import { MARCADORES_SECAO } from "@/lib/dominio";

// Cadastro de evento do mes (client). Valida no cliente para feedback imediato;
// a validacao autoritativa (protocolo duplicado, valor, marcador) e do servidor.
export default function NovoEventoPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    competencia: "",
    marcador_secao: MARCADORES_SECAO[0] as string,
    tipo: "INTEGRAL" as "INTEGRAL" | "PARCIAL",
    protocolo: "",
    motivo: "",
    placa: "",
    data_comunicacao: "",
    valor_rateado: "",
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

    // Converte valor_rateado para numero antes de validar.
    const payload = {
      ...form,
      valor_rateado: parseFloat(form.valor_rateado),
    };

    const local = criarEventoSchema.safeParse(payload);
    if (!local.success) {
      setErro(local.error.issues[0]?.message ?? "dados invalidos");
      return;
    }

    setSalvando(true);
    const resp = await fetch("/api/eventos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setSalvando(false);

    if (resp.status === 201) {
      router.push("/app/eventos");
      router.refresh();
      return;
    }
    if (resp.status === 409) {
      setErro("Protocolo ja cadastrado nesta competencia");
      return;
    }
    const body = await resp.json().catch(() => ({}));
    setErro(body.error ?? "nao foi possivel salvar");
  }

  return (
    <section style={{ maxWidth: 480 }}>
      <h1>Novo evento do mes</h1>
      <form onSubmit={salvar}>
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
          Marcador de secao
          <select
            value={form.marcador_secao}
            onChange={setcampo("marcador_secao")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          >
            {MARCADORES_SECAO.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Tipo
          <select
            value={form.tipo}
            onChange={setcampo("tipo")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          >
            <option value="INTEGRAL">INTEGRAL</option>
            <option value="PARCIAL">PARCIAL</option>
          </select>
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Protocolo
          <input
            type="text"
            value={form.protocolo}
            onChange={setcampo("protocolo")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Motivo (opcional)
          <input
            type="text"
            value={form.motivo}
            onChange={setcampo("motivo")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Placa
          <input
            type="text"
            value={form.placa}
            onChange={setcampo("placa")}
            placeholder="ABC1234"
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Data de comunicacao (YYYY-MM-DD)
          <input
            type="date"
            value={form.data_comunicacao}
            onChange={setcampo("data_comunicacao")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        <label style={{ display: "block", margin: "8px 0" }}>
          Valor rateado (R$)
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={form.valor_rateado}
            onChange={setcampo("valor_rateado")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        {erro && <p style={{ color: "crimson" }}>{erro}</p>}
        <button type="submit" disabled={salvando}>
          {salvando ? "Salvando..." : "Salvar"}
        </button>
      </form>
    </section>
  );
}
