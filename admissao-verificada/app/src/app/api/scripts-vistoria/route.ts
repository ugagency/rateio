import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { criarScriptVistoriaSchema } from "@/lib/schemas/vistoria";

// SPEC-004 secao 5.1 e 5.3. O associacao_id NÃO vem da URL; é inferido do
// operador logado. A RLS garante isolamento. Scripts sem referência podem ser
// excluídos via service_role; scripts referenciados só podem ser inativados.

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const tipo = sp.get("tipo");
  const status = sp.get("status") ?? "ativo";

  let query = supabase
    .from("scripts_vistoria")
    .select(
      `id, tipo, descricao, tempo_max_min, status, criado_em,
       etapas_script (
         id, sequencia, tipo_etapa, camera_preferencial, obrigatoria, instrucao_texto
       )`,
    )
    .eq("status", status)
    .order("criado_em", { ascending: false });

  if (tipo) query = query.eq("tipo", tipo);

  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Ordena as etapas por sequência antes de retornar.
  const scripts = (data ?? []).map((s) => ({
    ...s,
    etapas: ((s as { etapas_script?: unknown[] }).etapas_script ?? []).sort(
      (a: unknown, b: unknown) =>
        (a as { sequencia: number }).sequencia - (b as { sequencia: number }).sequencia,
    ),
    etapas_script: undefined,
  }));

  return NextResponse.json({ data: scripts });
}

export async function POST(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const parsed = criarScriptVistoriaSchema.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "dados invalidos", detalhes: parsed.error.flatten() },
      { status: 422 },
    );
  }
  const { tipo, descricao, tempo_max_min, etapas } = parsed.data;

  // Infere o associacao_id do operador logado, assim como a fatia de
  // associados faz (ADR-002 C2).
  const { data: op } = await supabase
    .from("operadores")
    .select("associacao_id")
    .eq("id", user.id)
    .single();
  if (!op) return NextResponse.json({ error: "operador sem associacao" }, { status: 401 });

  // Insere o script e as etapas numa transação via RPC ou em cascata manual.
  // Como não há RPC definido, usamos inserção sequencial; a RLS impõe
  // associacao_id correto no insert do script e o FK garante consistência das
  // etapas.
  const { data: script, error: errScript } = await supabase
    .from("scripts_vistoria")
    .insert({
      associacao_id: op.associacao_id,
      tipo,
      descricao: descricao || null,
      tempo_max_min,
      status: "ativo",
    })
    .select("id, tipo, descricao, tempo_max_min, status, criado_em")
    .single();

  if (errScript) {
    return NextResponse.json({ error: errScript.message }, { status: 500 });
  }

  const etapasPayload = etapas.map((e) => ({
    script_id: script.id,
    sequencia: e.sequencia,
    tipo_etapa: e.tipo_etapa,
    camera_preferencial: e.camera_preferencial,
    obrigatoria: e.obrigatoria,
    instrucao_texto: e.instrucao_texto || null,
  }));

  const { data: etapasCriadas, error: errEtapas } = await supabase
    .from("etapas_script")
    .insert(etapasPayload)
    .select("id, sequencia, tipo_etapa, camera_preferencial, obrigatoria, instrucao_texto");

  if (errEtapas) {
    // O script foi inserido, mas as etapas falharam. Registra o erro;
    // a limpeza manual com service_role fica fora do escopo do MVP.
    return NextResponse.json({ error: errEtapas.message }, { status: 500 });
  }

  const etapasOrdenadas = (etapasCriadas ?? []).sort((a, b) => a.sequencia - b.sequencia);

  return NextResponse.json({ ...script, etapas: etapasOrdenadas }, { status: 201 });
}
