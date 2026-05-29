import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient, createSupabaseServiceClient } from "@/lib/supabase/server";
import { iniciarVistoriaSchema } from "@/lib/schemas/vistoria";

// SPEC-004 secao 5.4 e 5.9.
// POST inicia uma vistoria para um veículo.
// GET lista as vistorias da associação com filtros opcionais.

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const veiculo_id = sp.get("veiculo_id");
  const status = sp.get("status");
  const data_inicio = sp.get("data_inicio");
  const data_fim = sp.get("data_fim");
  const page = Math.max(1, Number(sp.get("page") ?? 1));
  const perPage = Math.min(200, Math.max(1, Number(sp.get("per_page") ?? 50)));
  const from = (page - 1) * perPage;

  // A RLS filtra pela associacao_id do operador automaticamente.
  let query = supabase
    .from("vistorias")
    .select(
      `id, veiculo_id, script_id, operador_id, status,
       iniciado_em, finalizado_em, expirado_em, criado_em,
       veiculos (placa, segmento),
       scripts_vistoria (tipo, descricao)`,
      { count: "exact" },
    )
    .order("iniciado_em", { ascending: false })
    .range(from, from + perPage - 1);

  if (veiculo_id) query = query.eq("veiculo_id", veiculo_id);
  if (status) query = query.eq("status", status);
  if (data_inicio) query = query.gte("iniciado_em", data_inicio);
  if (data_fim) query = query.lte("iniciado_em", data_fim);

  const { data, error, count } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({
    data: data ?? [],
    total: count ?? 0,
    page,
    per_page: perPage,
  });
}

export async function POST(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const parsed = iniciarVistoriaSchema.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "dados invalidos", detalhes: parsed.error.flatten() },
      { status: 422 },
    );
  }
  const { veiculo_id, script_id } = parsed.data;

  // Infere o associacao_id do operador logado.
  const { data: op } = await supabase
    .from("operadores")
    .select("associacao_id")
    .eq("id", user.id)
    .single();
  if (!op) return NextResponse.json({ error: "operador sem associacao" }, { status: 401 });

  // Verifica se o veículo existe e pertence à associação (a RLS já filtra,
  // mas o 404 explícito é mais informativo do que 0 linhas silencioso).
  const { data: veiculo, error: errVeiculo } = await supabase
    .from("veiculos")
    .select("id, status, segmento")
    .eq("id", veiculo_id)
    .single();

  if (errVeiculo || !veiculo) {
    return NextResponse.json({ error: "veiculo nao encontrado" }, { status: 422 });
  }

  // Verifica se o script existe, pertence à associação e está ativo.
  const { data: script, error: errScript } = await supabase
    .from("scripts_vistoria")
    .select("id, tipo, status, tempo_max_min, etapas_script (id, sequencia, tipo_etapa, camera_preferencial, obrigatoria, instrucao_texto)")
    .eq("id", script_id)
    .single();

  if (errScript || !script) {
    return NextResponse.json({ error: "script nao encontrado" }, { status: 422 });
  }
  if (script.status !== "ativo") {
    return NextResponse.json({ error: "script inativo" }, { status: 422 });
  }

  // Insere a vistoria; o partial unique index garante que não há duas
  // vistorias a_realizar para o mesmo veiculo (retornará 23505 → 409).
  const { data: vistoria, error: errVistoria } = await supabase
    .from("vistorias")
    .insert({
      associacao_id: op.associacao_id,
      veiculo_id,
      script_id,
      operador_id: user.id,
      status: "a_realizar",
    })
    .select("id, veiculo_id, script_id, status, iniciado_em, token_sessao")
    .single();

  if (errVistoria) {
    // Código 23505 = violação de unique constraint (vistoria já em andamento).
    if (errVistoria.code === "23505") {
      return NextResponse.json(
        { error: "ja existe uma vistoria em andamento para este veiculo" },
        { status: 409 },
      );
    }
    return NextResponse.json({ error: errVistoria.message }, { status: 500 });
  }

  // Registra o evento de início na timeline via service_role (a tabela não
  // aceita INSERT pelo cliente autenticado).
  const service = createSupabaseServiceClient();
  await service.from("timeline_vistoria").insert({
    vistoria_id: vistoria.id,
    associacao_id: op.associacao_id,
    evento: "inicio",
    metadados: { operador_id: user.id, veiculo_id },
  });

  const etapasOrdenadas = (
    (script as { etapas_script?: unknown[] }).etapas_script ?? []
  ).sort(
    (a, b) =>
      (a as { sequencia: number }).sequencia - (b as { sequencia: number }).sequencia,
  );

  return NextResponse.json(
    { ...vistoria, etapas: etapasOrdenadas },
    { status: 201 },
  );
}
