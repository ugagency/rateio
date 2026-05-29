import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { createSupabaseServiceClient } from "@/lib/supabase/server";

// SPEC-004 secao 5.5. Upload de foto de uma etapa de vistoria.
// Autenticação: JWT do operador (cookie) OU header X-Vistoria-Token
// (token_sessao). O upload de arquivo via galeria é bloqueado no cliente
// (ADR-002 C8); este endpoint não valida a origem da imagem (MVP).
// Tamanho máximo: 10 MB. Tipo: image/jpeg.

const TAMANHO_MAX_BYTES = 10 * 1024 * 1024; // 10 MB

type Params = { params: Promise<{ id: string }> };

export async function POST(req: NextRequest, { params }: Params) {
  const { id: vistoria_id } = await params;

  // Autenticação: tenta JWT de operador primeiro, depois token_sessao.
  let associacao_id: string | null = null;
  let autenticadoPor: "jwt" | "token_sessao" = "jwt";

  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    // Operador logado: lê associacao_id do perfil.
    const { data: op } = await supabase
      .from("operadores")
      .select("associacao_id")
      .eq("id", user.id)
      .single();
    associacao_id = op?.associacao_id ?? null;
  } else {
    // Tenta autenticar pelo token_sessao (fluxo de campo).
    const tokenHeader = req.headers.get("x-vistoria-token");
    if (tokenHeader) {
      const service = createSupabaseServiceClient();
      const { data: v } = await service
        .from("vistorias")
        .select("id, associacao_id, token_sessao, status")
        .eq("id", vistoria_id)
        .eq("token_sessao", tokenHeader)
        .single();
      if (v) {
        associacao_id = v.associacao_id;
        autenticadoPor = "token_sessao";
      }
    }
  }

  if (!associacao_id) {
    return NextResponse.json({ error: "nao autenticado" }, { status: 401 });
  }

  // Carrega a vistoria (usa service_role quando autenticado por token_sessao,
  // pois o cliente anon não tem acesso sem JWT de operador).
  const service = createSupabaseServiceClient();
  const { data: vistoria, error: errVistoria } = await service
    .from("vistorias")
    .select(
      `id, associacao_id, status, iniciado_em, token_sessao,
       scripts_vistoria (
         tempo_max_min,
         etapas_script (id, sequencia, obrigatoria, tipo_etapa, camera_preferencial)
       )`,
    )
    .eq("id", vistoria_id)
    .eq("associacao_id", associacao_id)
    .single();

  if (errVistoria || !vistoria) {
    return NextResponse.json({ error: "vistoria nao encontrada" }, { status: 404 });
  }

  if (vistoria.status === "finalizada") {
    return NextResponse.json({ error: "vistoria ja finalizada" }, { status: 403 });
  }
  if (vistoria.status === "expirada") {
    return NextResponse.json({ error: "vistoria expirada" }, { status: 403 });
  }

  // Verifica expiração de sessão.
  const scriptData = vistoria.scripts_vistoria as {
    tempo_max_min?: number;
    etapas_script?: { id: string; sequencia: number; obrigatoria: boolean }[];
  } | null;
  const tempoMax = scriptData?.tempo_max_min ?? 30;
  const iniciado = new Date(vistoria.iniciado_em as string).getTime();
  const agora = Date.now();
  if (agora - iniciado > tempoMax * 60 * 1000) {
    // Marca a vistoria como expirada e registra na timeline.
    await service
      .from("vistorias")
      .update({ status: "expirada", expirado_em: new Date().toISOString() })
      .eq("id", vistoria_id);
    await service.from("timeline_vistoria").insert({
      vistoria_id,
      associacao_id,
      evento: "expiracao",
      metadados: { motivo: "tempo_maximo_excedido" },
    });
    return NextResponse.json({ error: "sessao de vistoria expirada" }, { status: 408 });
  }

  // Processa o multipart.
  let formData: FormData;
  try {
    formData = await req.formData();
  } catch {
    return NextResponse.json({ error: "payload multipart invalido" }, { status: 422 });
  }

  const etapa_id = formData.get("etapa_id") as string | null;
  const arquivo = formData.get("arquivo") as File | null;
  const capturado_em_raw = formData.get("capturado_em") as string | null;
  const latitude_raw = formData.get("latitude") as string | null;
  const longitude_raw = formData.get("longitude") as string | null;

  if (!etapa_id || !arquivo || !capturado_em_raw) {
    return NextResponse.json(
      { error: "campos obrigatorios ausentes: etapa_id, arquivo, capturado_em" },
      { status: 422 },
    );
  }

  // Valida tipo e tamanho do arquivo.
  if (!arquivo.type.startsWith("image/jpeg") && !arquivo.type.startsWith("image/jpg")) {
    return NextResponse.json({ error: "arquivo deve ser JPEG" }, { status: 422 });
  }
  if (arquivo.size > TAMANHO_MAX_BYTES) {
    return NextResponse.json({ error: "arquivo excede 10 MB" }, { status: 422 });
  }

  // Valida timestamp do dispositivo.
  const capturado_em = new Date(capturado_em_raw);
  if (isNaN(capturado_em.getTime())) {
    return NextResponse.json({ error: "capturado_em invalido" }, { status: 422 });
  }

  const latitude = latitude_raw ? parseFloat(latitude_raw) : null;
  const longitude = longitude_raw ? parseFloat(longitude_raw) : null;

  // Verifica se a etapa pertence ao script desta vistoria e valida a
  // sequência (CA-004-7): a etapa enviada deve ser a próxima não concluída.
  const todasEtapas = (scriptData?.etapas_script ?? []).sort(
    (a, b) => a.sequencia - b.sequencia,
  );
  const etapa = todasEtapas.find((e) => e.id === etapa_id);
  if (!etapa) {
    return NextResponse.json(
      { error: "etapa nao pertence ao script desta vistoria" },
      { status: 422 },
    );
  }

  // Carrega capturas vigentes (sem substituida_por) desta vistoria.
  const { data: capturasExistentes } = await service
    .from("capturas_vistoria")
    .select("etapa_id")
    .eq("vistoria_id", vistoria_id)
    .is("substituida_por", null);

  const etapasConcluidas = new Set((capturasExistentes ?? []).map((c) => c.etapa_id));

  // A próxima etapa esperada é a de menor sequência ainda não concluída.
  const proximaEtapa = todasEtapas.find((e) => !etapasConcluidas.has(e.id));

  if (!proximaEtapa) {
    return NextResponse.json(
      { error: "todas as etapas ja foram concluidas" },
      { status: 422 },
    );
  }

  if (proximaEtapa.id !== etapa_id) {
    return NextResponse.json(
      {
        error: "etapa fora da sequencia",
        etapa_esperada: { id: proximaEtapa.id, sequencia: proximaEtapa.sequencia },
      },
      { status: 422 },
    );
  }

  // Gera um id antecipado para usar no storage_path.
  const captura_id = crypto.randomUUID();
  const storagePath = `${associacao_id}/${vistoria_id}/${etapa_id}/${captura_id}.jpg`;

  // Faz upload para o Storage via service_role (bucket privado).
  const arrayBuffer = await arquivo.arrayBuffer();
  const { error: errUpload } = await service.storage
    .from("vistorias")
    .upload(storagePath, arrayBuffer, { contentType: "image/jpeg", upsert: false });

  if (errUpload) {
    console.error("[CAPTURAS] erro no upload", { vistoria_id, etapa_id, erro: errUpload.message });
    return NextResponse.json({ error: "falha ao gravar arquivo" }, { status: 500 });
  }

  // Registra a captura no banco.
  const recebido_em = new Date().toISOString();
  const { data: captura, error: errCaptura } = await service
    .from("capturas_vistoria")
    .insert({
      id: captura_id,
      vistoria_id,
      etapa_id,
      associacao_id,
      storage_path: storagePath,
      capturado_em: capturado_em.toISOString(),
      recebido_em,
      latitude: latitude ?? null,
      longitude: longitude ?? null,
    })
    .select("id, etapa_id, capturado_em, recebido_em")
    .single();

  if (errCaptura) {
    console.error("[CAPTURAS] erro ao registrar captura", { captura_id, erro: errCaptura.message });
    return NextResponse.json({ error: errCaptura.message }, { status: 500 });
  }

  // Registra o evento na timeline antifraude.
  await service.from("timeline_vistoria").insert({
    vistoria_id,
    associacao_id,
    evento: "captura",
    etapa_id,
    captura_id: captura.id,
    metadados: {
      autenticado_por: autenticadoPor,
      latitude,
      longitude,
      capturado_em: capturado_em.toISOString(),
    },
  });

  return NextResponse.json(
    {
      captura_id: captura.id,
      etapa_id: captura.etapa_id,
      capturado_em: captura.capturado_em,
      recebido_em: captura.recebido_em,
    },
    { status: 201 },
  );
}
