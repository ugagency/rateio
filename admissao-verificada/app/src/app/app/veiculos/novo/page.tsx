"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { criarVeiculoSchema } from "@/lib/schemas/veiculo";
import { SEGMENTOS } from "@/lib/dominio";
import { COBERTURAS_TERCEIROS } from "@/lib/dominio";

// Cadastro de veiculo (client). Valida no cliente para feedback imediato; a
// validacao autoritativa (placa, duplicidade, cota) e do route handler.
// A cota simulada e obtida via GET /api/veiculos/simular-cota ao sair do campo
// FIPE, sem bloquear o submit (SPEC-003 secao 6.2).
export default function NovoVeiculoPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    associado_id: "",
    placa: "",
    segmento: "" as (typeof SEGMENTOS)[number] | "",
    fipe_valor: "",
    cobertura_terceiros: "" as (typeof COBERTURAS_TERCEIROS)[number] | "",
  });
  const [cotaSimulada, setCotaSimulada] = useState<number | null>(null);
  const [faixaSimulada, setFaixaSimulada] = useState<string | null>(null);
  const [simulando, setSimulando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  function setCampo<K extends keyof typeof form>(campo: K) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [campo]: e.target.value }));
  }

  // Ao sair do campo FIPE, solicita a cota prevista sem bloquear o submit.
  async function simularCota() {
    const fipe = Number(form.fipe_valor);
    if (!form.fipe_valor || isNaN(fipe) || fipe <= 0) {
      setCotaSimulada(null);
      setFaixaSimulada(null);
      return;
    }
    setSimulando(true);
    try {
      const resp = await fetch(
        `/api/veiculos/simular-cota?fipe_valor=${encodeURIComponent(fipe)}`,
      );
      if (resp.ok) {
        const body = await resp.json();
        setCotaSimulada(body.cota);
        setFaixaSimulada(body.faixa_aplicada);
      } else {
        setCotaSimulada(null);
        setFaixaSimulada(null);
      }
    } finally {
      setSimulando(false);
    }
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    const payload = {
      associado_id: form.associado_id,
      placa: form.placa,
      segmento: form.segmento,
      fipe_valor: Number(form.fipe_valor),
      cobertura_terceiros: form.cobertura_terceiros,
    };

    const local = criarVeiculoSchema.safeParse(payload);
    if (!local.success) {
      setErro(local.error.issues[0]?.message ?? "dados invalidos");
      return;
    }

    setSalvando(true);
    const resp = await fetch("/api/veiculos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setSalvando(false);

    if (resp.status === 201) {
      router.push("/app/veiculos");
      router.refresh();
      return;
    }
    if (resp.status === 409) {
      setErro("Placa ja cadastrada nesta associacao.");
      return;
    }
    if (resp.status === 404) {
      setErro("Associado nao encontrado na associacao.");
      return;
    }
    if (resp.status === 500) {
      const body = await resp.json().catch(() => ({}));
      setErro(
        body.error ??
          "Erro interno. Verifique se a tabela de faixas de cota esta configurada.",
      );
      return;
    }
    const body = await resp.json().catch(() => ({}));
    setErro(body.error ?? "Nao foi possivel salvar.");
  }

  return (
    <section style={{ maxWidth: 480 }}>
      <h1>Novo veiculo</h1>
      <form onSubmit={salvar}>
        {/* Associado */}
        <label style={{ display: "block", margin: "8px 0" }}>
          ID do associado
          <input
            type="text"
            value={form.associado_id}
            onChange={setCampo("associado_id")}
            placeholder="UUID do associado"
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        {/* Placa */}
        <label style={{ display: "block", margin: "8px 0" }}>
          Placa
          <input
            type="text"
            value={form.placa}
            onChange={setCampo("placa")}
            placeholder="ABC1234 ou ABC1D23"
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        {/* Segmento */}
        <label style={{ display: "block", margin: "8px 0" }}>
          Segmento
          <select
            value={form.segmento}
            onChange={setCampo("segmento")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          >
            <option value="">Selecione...</option>
            {SEGMENTOS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>

        {/* Valor FIPE */}
        <label style={{ display: "block", margin: "8px 0" }}>
          Valor FIPE (R$)
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={form.fipe_valor}
            onChange={setCampo("fipe_valor")}
            onBlur={simularCota}
            placeholder="Ex.: 85000"
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
          {simulando && (
            <span style={{ fontSize: 12, color: "#666" }}>Calculando cota...</span>
          )}
          {!simulando && cotaSimulada !== null && (
            <span style={{ fontSize: 12, color: "#0f766e" }}>
              Cota prevista:{" "}
              {cotaSimulada.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              {faixaSimulada ? ` (faixa ${faixaSimulada})` : ""}
            </span>
          )}
        </label>

        {/* Cobertura de terceiros */}
        <label style={{ display: "block", margin: "8px 0" }}>
          Cobertura de terceiros
          <select
            value={form.cobertura_terceiros}
            onChange={setCampo("cobertura_terceiros")}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          >
            <option value="">Selecione...</option>
            {COBERTURAS_TERCEIROS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        {erro && <p style={{ color: "crimson" }}>{erro}</p>}

        <button type="submit" disabled={salvando} style={{ marginTop: 8 }}>
          {salvando ? "Salvando..." : "Salvar"}
        </button>
      </form>
    </section>
  );
}
