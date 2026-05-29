"use client";

// Fluxo de captura de vistoria (client component / PWA).
// Acessa camera ao vivo via getUserMedia. Galeria bloqueada por ausência
// de campo de upload (ADR-002 C8, CA-004-4). Fluxo sequencial obrigatório
// (CA-004-7). Carimbo de lat/long/horario por foto (CA-004-5).

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";

type Etapa = {
  id: string;
  sequencia: number;
  tipo_etapa: string;
  camera_preferencial: "frontal" | "traseira";
  obrigatoria: boolean;
  instrucao_texto: string | null;
};

type DadosVistoria = {
  id: string;
  veiculo_id: string;
  status: string;
  iniciado_em: string;
  token_sessao: string;
  etapas: Etapa[];
  scripts_vistoria: { tempo_max_min: number } | null;
};

type FaseCaptura = "aguardando" | "preview" | "enviando" | "concluida";

export default function VistoriaFluxoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [vistoria, setVistoria] = useState<DadosVistoria | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  // Índice da etapa atual no array ordenado por sequência.
  const [indiceAtual, setIndiceAtual] = useState(0);
  const [faseCaptura, setFaseCaptura] = useState<FaseCaptura>("aguardando");

  // Blob da foto capturada antes do envio.
  const [blobCaptura, setBlobCaptura] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Metadados coletados no momento do clique do obturador.
  const [metadados, setMetadados] = useState<{
    capturado_em: string;
    latitude: number | null;
    longitude: number | null;
  } | null>(null);

  // Cronômetro regressivo.
  const [segundosRestantes, setSegundosRestantes] = useState<number | null>(null);
  const [sessaoExpirada, setSessaoExpirada] = useState(false);

  // Vistoria concluída (todas as etapas enviadas, aguardando finalização).
  const [todasConcluidas, setTodasConcluidas] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const [finalizada, setFinalizada] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Carrega os dados da vistoria pelo id.
  useEffect(() => {
    async function carregar() {
      setCarregando(true);
      try {
        const resp = await fetch(`/api/vistorias?veiculo_id=&page=1&per_page=1`);
        // Não há endpoint GET /api/vistorias/:id ainda; usa a listagem e filtra.
        // Na prática, buscamos diretamente via Supabase pelo browser client.
        // Como a página roda no cliente, busca diretamente da API de lista com
        // um filtro de id simulado. Em um MVP real, criaria GET /api/vistorias/[id].
        // Aqui usamos a rota de lista sem filtro e localizamos pelo id.
        const listaResp = await fetch(`/api/vistorias?per_page=200`);
        if (!listaResp.ok) throw new Error("Erro ao carregar vistorias");
        const lista = await listaResp.json();
        const encontrada = (lista.data ?? []).find(
          (v: { id: string }) => v.id === id,
        );
        if (!encontrada) {
          setErro("Vistoria nao encontrada.");
          return;
        }
        setVistoria(encontrada);
        if (encontrada.status === "finalizada") setFinalizada(true);
        if (encontrada.status === "expirada") setSessaoExpirada(true);
        const tempoMax = encontrada.scripts_vistoria?.tempo_max_min ?? 30;
        const inicio = new Date(encontrada.iniciado_em).getTime();
        const decorrido = Math.floor((Date.now() - inicio) / 1000);
        const restantes = tempoMax * 60 - decorrido;
        setSegundosRestantes(Math.max(0, restantes));
      } catch (e) {
        setErro((e as Error).message);
      } finally {
        setCarregando(false);
      }
    }
    carregar();
  }, [id]);

  // Cronômetro regressivo.
  useEffect(() => {
    if (segundosRestantes === null) return;
    if (segundosRestantes <= 0) {
      setSessaoExpirada(true);
      return;
    }
    const timer = setTimeout(() => setSegundosRestantes((s) => (s ?? 1) - 1), 1000);
    return () => clearTimeout(timer);
  }, [segundosRestantes]);

  // Inicia a câmera para a etapa atual.
  const iniciarCamera = useCallback(
    async (etapa: Etapa) => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      const facingMode = etapa.camera_preferencial === "frontal" ? "user" : "environment";
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode },
          audio: false,
        });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch {
        setErro("Nao foi possivel acessar a camera. Verifique as permissoes do navegador.");
      }
    },
    [],
  );

  // Encerra a câmera ao desmontar ou ao trocar de etapa.
  const encerrarCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  // Quando a vistoria carregar e não estiver encerrada, inicia a câmera.
  useEffect(() => {
    if (!vistoria || finalizada || sessaoExpirada) return;
    const etapa = vistoria.etapas[indiceAtual];
    if (!etapa) return;
    if (faseCaptura === "aguardando") {
      iniciarCamera(etapa);
    }
    return () => {
      if (faseCaptura === "aguardando") encerrarCamera();
    };
  }, [vistoria, indiceAtual, faseCaptura, finalizada, sessaoExpirada, iniciarCamera, encerrarCamera]);

  // Captura o frame atual do vídeo como JPEG.
  function capturar() {
    if (!videoRef.current || !streamRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const capturado_em = new Date().toISOString();

    // Coleta geolocalização de forma não bloqueante; se indisponível,
    // prossegue com null (questão em aberto SPEC-004 secao 11, item 2).
    const coletarEEnviar = (latitude: number | null, longitude: number | null) => {
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            setErro("Falha ao gerar imagem da captura.");
            return;
          }
          const url = URL.createObjectURL(blob);
          setBlobCaptura(blob);
          setPreviewUrl(url);
          setMetadados({ capturado_em, latitude, longitude });
          encerrarCamera();
          setFaseCaptura("preview");
        },
        "image/jpeg",
        0.92,
      );
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => coletarEEnviar(pos.coords.latitude, pos.coords.longitude),
        () => coletarEEnviar(null, null),
        { timeout: 3000, maximumAge: 60000 },
      );
    } else {
      coletarEEnviar(null, null);
    }
  }

  // Descarta o preview e reabre a câmera para tentar novamente.
  function repetir() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setBlobCaptura(null);
    setPreviewUrl(null);
    setMetadados(null);
    setFaseCaptura("aguardando");
  }

  // Confirma e envia a foto capturada.
  async function confirmarEnvio() {
    if (!blobCaptura || !metadados || !vistoria) return;
    const etapa = vistoria.etapas[indiceAtual];
    if (!etapa) return;

    setFaseCaptura("enviando");

    const form = new FormData();
    form.append("etapa_id", etapa.id);
    form.append("arquivo", blobCaptura, "captura.jpg");
    form.append("capturado_em", metadados.capturado_em);
    if (metadados.latitude !== null) form.append("latitude", String(metadados.latitude));
    if (metadados.longitude !== null) form.append("longitude", String(metadados.longitude));

    const resp = await fetch(`/api/vistorias/${vistoria.id}/capturas`, {
      method: "POST",
      headers: {
        // token_sessao para autenticação alternativa no campo.
        "X-Vistoria-Token": vistoria.token_sessao,
      },
      body: form,
    });

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setBlobCaptura(null);
    setMetadados(null);

    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      if (resp.status === 408) {
        setSessaoExpirada(true);
        return;
      }
      if (resp.status === 403) {
        setSessaoExpirada(true);
        return;
      }
      setErro(body.error ?? "Erro ao enviar captura.");
      setFaseCaptura("aguardando");
      return;
    }

    // Avança para a próxima etapa ou conclui.
    const proximoIndice = indiceAtual + 1;
    if (proximoIndice >= vistoria.etapas.length) {
      setTodasConcluidas(true);
      setFaseCaptura("concluida");
    } else {
      setIndiceAtual(proximoIndice);
      setFaseCaptura("aguardando");
    }
  }

  // Finaliza a vistoria após todas as etapas concluídas.
  async function finalizar() {
    if (!vistoria) return;
    setFinalizando(true);
    const resp = await fetch(`/api/vistorias/${vistoria.id}/finalizar`, {
      method: "POST",
    });
    setFinalizando(false);
    if (resp.ok) {
      setFinalizada(true);
    } else {
      const body = await resp.json().catch(() => ({}));
      setErro(body.error ?? "Erro ao finalizar a vistoria.");
    }
  }

  // Formata o cronômetro como MM:SS.
  function formatarTempo(segundos: number): string {
    const m = Math.floor(segundos / 60);
    const s = segundos % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  // Estados de carregamento e erro iniciais.
  if (carregando) return <p>Carregando vistoria...</p>;
  if (erro && !vistoria) return <p style={{ color: "crimson" }}>{erro}</p>;
  if (!vistoria) return <p>Vistoria nao encontrada.</p>;

  const etapaAtual: Etapa | undefined = vistoria.etapas[indiceAtual];
  const totalEtapas = vistoria.etapas.length;

  // Tela: vistoria já finalizada.
  if (finalizada) {
    return (
      <section style={{ maxWidth: 480 }}>
        <h1>Vistoria finalizada</h1>
        <p>A vistoria foi concluida com sucesso. O veiculo esta apto a admissao.</p>
        <button onClick={() => router.push("/app/vistorias")}>Voltar ao painel</button>
      </section>
    );
  }

  // Tela: sessão expirada.
  if (sessaoExpirada) {
    return (
      <section style={{ maxWidth: 480 }}>
        <h1>Sessao expirada</h1>
        <p>
          O tempo maximo da vistoria foi excedido. Todas as fotos capturadas foram
          descartadas. O operador deve iniciar uma nova vistoria.
        </p>
        <button onClick={() => router.push("/app/vistorias")}>Voltar ao painel</button>
      </section>
    );
  }

  // Tela: todas as etapas concluídas, aguardando finalização.
  if (todasConcluidas) {
    return (
      <section style={{ maxWidth: 480 }}>
        <h1>Todas as fotos capturadas</h1>
        <p>
          Todas as {totalEtapas} etapas foram concluidas. Clique em "Finalizar
          vistoria" para registrar a admissao do veiculo.
        </p>
        {erro && <p style={{ color: "crimson" }}>{erro}</p>}
        <button onClick={finalizar} disabled={finalizando}>
          {finalizando ? "Finalizando..." : "Finalizar vistoria"}
        </button>
      </section>
    );
  }

  if (!etapaAtual) return <p>Nenhuma etapa disponivel.</p>;

  return (
    <section style={{ maxWidth: 480 }}>
      {/* Cabeçalho com progresso e cronômetro */}
      <header style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>Vistoria</h1>
        <p style={{ margin: "4px 0", color: "#555" }}>
          Etapa {indiceAtual + 1} de {totalEtapas}: {etapaAtual.tipo_etapa.replace(/_/g, " ")}
        </p>
        {segundosRestantes !== null && (
          <p
            style={{
              margin: "4px 0",
              fontWeight: "bold",
              color: segundosRestantes < 60 ? "crimson" : "#1e3a5f",
            }}
          >
            Tempo restante: {formatarTempo(segundosRestantes)}
          </p>
        )}
      </header>

      {/* Instrução da etapa */}
      {etapaAtual.instrucao_texto && (
        <p
          style={{
            background: "#f0f4ff",
            padding: "10px 14px",
            borderRadius: 6,
            marginBottom: 16,
          }}
        >
          {etapaAtual.instrucao_texto}
        </p>
      )}

      {erro && <p style={{ color: "crimson", marginBottom: 12 }}>{erro}</p>}

      {/* Fase: aguardando captura — exibe viewfinder ao vivo */}
      {faseCaptura === "aguardando" && (
        <div>
          {/* O elemento <video> serve como viewfinder ao vivo. NÃO há
              <input type="file"> em nenhum lugar desta tela (ADR-002 C8). */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: "100%",
              borderRadius: 8,
              background: "#000",
              display: "block",
              aspectRatio: "4/3",
              objectFit: "cover",
            }}
          />
          <button
            onClick={capturar}
            style={{
              marginTop: 16,
              width: "100%",
              padding: "14px 0",
              fontSize: 18,
              fontWeight: "bold",
              background: "#1e3a5f",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            Capturar foto
          </button>
        </div>
      )}

      {/* Fase: preview — exibe a foto capturada para confirmação */}
      {faseCaptura === "preview" && previewUrl && (
        <div>
          <img
            src={previewUrl}
            alt="Preview da captura"
            style={{ width: "100%", borderRadius: 8, display: "block", aspectRatio: "4/3", objectFit: "cover" }}
          />
          {metadados && (
            <p style={{ fontSize: 12, color: "#555", margin: "8px 0" }}>
              Capturado em: {new Date(metadados.capturado_em).toLocaleString("pt-BR")}
              {metadados.latitude !== null && metadados.longitude !== null
                ? ` | Lat: ${metadados.latitude.toFixed(5)}, Long: ${metadados.longitude.toFixed(5)}`
                : " | Geolocalizacao indisponivel"}
            </p>
          )}
          <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
            <button
              onClick={repetir}
              style={{
                flex: 1,
                padding: "12px 0",
                background: "#e5e7eb",
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
              }}
            >
              Repetir
            </button>
            <button
              onClick={confirmarEnvio}
              style={{
                flex: 2,
                padding: "12px 0",
                background: "#1e3a5f",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                fontWeight: "bold",
                cursor: "pointer",
              }}
            >
              Confirmar e enviar
            </button>
          </div>
        </div>
      )}

      {/* Fase: enviando */}
      {faseCaptura === "enviando" && (
        <p style={{ textAlign: "center", padding: 32, color: "#555" }}>
          Enviando foto...
        </p>
      )}

      {/* Indicador de progresso das etapas */}
      <div style={{ marginTop: 24, display: "flex", gap: 4 }}>
        {vistoria.etapas.map((e, i) => (
          <div
            key={e.id}
            title={e.tipo_etapa}
            style={{
              flex: 1,
              height: 6,
              borderRadius: 3,
              background: i < indiceAtual ? "#16a34a" : i === indiceAtual ? "#1e3a5f" : "#d1d5db",
            }}
          />
        ))}
      </div>
    </section>
  );
}
