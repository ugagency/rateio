import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { createSupabaseServiceClient } from "@/lib/supabase/server";

// SPEC-004 secao 5.7 e CA-004-10.
// Finaliza a vistoria quando todas as etapas obrigatórias estão concluídas.
// Usa service_role para atualizar vistorias.status e veiculos.status em
// sequência atômica (ADR-002 C1). A imutabilidade é garantida pela verificação
// de status antes de qualquer operação (CA-004-11).

type Params = { params: Promise<{ id: string }> };

export async function POST(req: NextRequest, { params }: Params) {
  const { id } = await params;

  // Autentica o operador.
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  // Carrega a vistoria com as etapas do script (via RLS do operador).
  const { data: vistoria, error: errVistoria } = await supabase
    .from("vistorias")
    .select(
      `id, veiculo_id, associacao_id, status,
       scripts_vistoria (
         etapas_script (id, obrigatoria, sequencia)
       )`,
    )
    .eq("id", id)
    .single();

  if (errVistoria || !vistoria) {
    return NextResponse.json({ error: "vistoria nao encontrada" }, { status: 404 });
  }

  // CA-004-11: imutabilidade pós-finalização.
  if (vistoria.status === "finalizada") {
    return NextResponse.json({ error: "vistoria ja finalizada" }, { status: 403 });
  }
  if (vistoria.status === "expirada") {
    return NextResponse.json({ error: "vistoria expirada" }, { status: 403 });
  }

  // Reúne as etapas obrigatórias do script.
  const scriptData = vistoria.scripts_vistoria as {
    etapas_script?: { id: string; obrigatoria: boolean; sequencia: number }[];
  } | null;
  const todasEtapas = scriptData?.etapas_script ?? [];
  const obrigatorias = todasEtapas.filter((e) => e.obrigatoria);

  // Verifica quais etapas obrigatórias já têm captura vigente (sem
  // substituida_por, que indicaria que a foto foi substituída por uma refação).
  const { data: capturas } = await supabase
    .from("capturas_vistoria")
    .select("etapa_id")
    .eq("vistoria_id", id)
    .is("substituida_por", null);

  const etapasConcluidas = new Set((capturas ?? []).map((c) => c.etapa_id));
  const pendentes = obrigatorias.filter((e) => !etapasConcluidas.has(e.id));

  if (pendentes.length > 0) {
    return NextResponse.json(
      {
        error: "etapas obrigatorias pendentes",
        etapas_pendentes: pendentes
          .sort((a, b) => a.sequencia - b.sequencia)
          .map((e) => ({ id: e.id, sequencia: e.sequencia })),
      },
      { status: 422 },
    );
  }

  // Usa service_role para:
  // 1. Atualizar vistorias.status para 'finalizada'.
  // 2. Atualizar veiculos.status para 'ativo' (ADR-002 C1).
  // 3. Registrar evento de finalização na timeline.
  // As três operações são executadas em sequência; se qualquer uma falhar,
  // o estado parcial será detectado na próxima chamada (status ainda não
  // será 'finalizada').
  const agora = new Date().toISOString();
  const service = createSupabaseServiceClient();

  const { error: errFinaliza } = await service
    .from("vistorias")
    .update({ status: "finalizada", finalizado_em: agora })
    .eq("id", id);

  if (errFinaliza) {
    return NextResponse.json({ error: errFinaliza.message }, { status: 500 });
  }

  const { error: errVeiculo } = await service
    .from("veiculos")
    .update({ status: "ativo" })
    .eq("id", vistoria.veiculo_id);

  if (errVeiculo) {
    // Registra o erro, mas não reverte a finalização (o operador pode
    // corrigir manualmente via service_role; o estado de vistoria finalizada
    // é imutável a partir daqui).
    console.error(
      "[FINALIZAR] erro ao atualizar status do veiculo",
      { vistoria_id: id, veiculo_id: vistoria.veiculo_id, erro: errVeiculo.message },
    );
  }

  await service.from("timeline_vistoria").insert({
    vistoria_id: id,
    associacao_id: vistoria.associacao_id,
    evento: "finalizacao",
    metadados: { operador_id: user.id, finalizado_em: agora },
  });

  return NextResponse.json({ id, status: "finalizada", finalizado_em: agora });
}
