"use client";

import { useState } from "react";
import { competenciaValida } from "@/lib/competencia";

// Tela de Exportacao (SPEC-007 sec. 8). Permite selecionar uma competencia,
// acionar a geracao dos arquivos BASE.xlsx e RATEIO.xlsx e baixa-los
// diretamente no navegador. O resultado inclui o nome e o hash de cada arquivo.

interface ArquivoResultado {
  nome: string;
  hash: string;
  conteudo: string; // base64
}

interface ResultadoExport {
  competencia: string;
  base: ArquivoResultado;
  rateio: ArquivoResultado;
}

// Converte base64 em Blob para download no navegador.
function base64ParaBlob(base64: string, tipo: string): Blob {
  const binStr = atob(base64);
  const bytes = new Uint8Array(binStr.length);
  for (let i = 0; i < binStr.length; i++) {
    bytes[i] = binStr.charCodeAt(i);
  }
  return new Blob([bytes], { type: tipo });
}

function baixarArquivo(arquivo: ArquivoResultado) {
  const blob = base64ParaBlob(
    arquivo.conteudo,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = arquivo.nome;
  link.click();
  URL.revokeObjectURL(url);
}

export default function ExportacaoPage() {
  const anoAtual = new Date().getFullYear();
  const mesAtual = String(new Date().getMonth() + 1).padStart(2, "0");
  const [competencia, setCompetencia] = useState(`${anoAtual}-${mesAtual}`);
  const [exportando, setExportando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ResultadoExport | null>(null);

  async function exportar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setResultado(null);

    if (!competenciaValida(competencia)) {
      setErro("Competencia invalida. Informe no formato AAAA-MM.");
      return;
    }

    setExportando(true);
    try {
      const resp = await fetch("/api/export/competencia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ competencia }),
      });

      if (resp.status === 401) {
        setErro("Sessao expirada. Faca login novamente.");
        return;
      }
      if (resp.status === 422) {
        const body = await resp.json().catch(() => ({}));
        setErro(body.error ?? "Competencia invalida.");
        return;
      }
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        setErro(body.error ?? "Nao foi possivel gerar os arquivos.");
        return;
      }

      const data: ResultadoExport = await resp.json();
      setResultado(data);
    } catch {
      setErro("Erro de comunicacao com o servidor.");
    } finally {
      setExportando(false);
    }
  }

  return (
    <section style={{ maxWidth: 560 }}>
      <h1>Exportacao</h1>
      <p style={{ color: "#555", marginBottom: 16 }}>
        Gera os arquivos BASE.xlsx e RATEIO.xlsx para a competencia selecionada.
        Os arquivos seguem o layout do motor de rateio.
      </p>

      <form onSubmit={exportar}>
        <label style={{ display: "block", margin: "8px 0" }}>
          Competencia (AAAA-MM)
          <input
            type="text"
            value={competencia}
            onChange={(e) => setCompetencia(e.target.value)}
            placeholder="ex.: 2026-06"
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>

        {erro && <p style={{ color: "crimson", margin: "8px 0" }}>{erro}</p>}

        <button type="submit" disabled={exportando} style={{ marginTop: 8 }}>
          {exportando ? "Gerando arquivos..." : "Exportar"}
        </button>
      </form>

      {resultado && (
        <div style={{ marginTop: 24, borderTop: "1px solid #ddd", paddingTop: 16 }}>
          <h2 style={{ fontSize: "1rem", marginBottom: 12 }}>
            Arquivos gerados para {resultado.competencia}
          </h2>

          {[resultado.base, resultado.rateio].map((arq) => (
            <div
              key={arq.nome}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8px 0",
                borderBottom: "1px solid #eee",
              }}
            >
              <div>
                <strong style={{ display: "block" }}>{arq.nome}</strong>
                <span
                  style={{
                    fontSize: "0.75rem",
                    color: "#666",
                    fontFamily: "monospace",
                    wordBreak: "break-all",
                  }}
                >
                  sha256: {arq.hash}
                </span>
              </div>
              <button
                type="button"
                onClick={() => baixarArquivo(arq)}
                style={{ marginLeft: 16, flexShrink: 0 }}
              >
                Baixar
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
