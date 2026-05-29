import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { criarSituacaoBoletoSchema } from "@/lib/schemas/situacao-boleto";
import { competenciaParaDate, competenciaParaExibicao, competenciaValida } from "@/lib/competencia";

// SPEC-005 secao 5.1 e 5.3. O associacao_id NAO vem da URL; e inferido do
// operador logado (claim do JWT, aplicado pela RLS). A unicidade de veiculo
// por competencia e garantida pela constraint do banco (409). O veiculo deve
// ter status ativo para receber situacao de boleto (AC-007).

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const competenciaParam = sp.get("competencia");
  const veiculoId = sp.get("veiculo_id");
  const situacaoParam = sp.get("situacao");
  const page = Math.max(1, Number(sp.get("page") ?? 1));
  const perPage = Math.min(200, Math.max(1, Number(sp.get("per_page") ?? 50)));
  const from = (page - 1) * perPage;

  // Valida o filtro de competencia quando fornecido.
  if (competenciaParam && !competenciaValida(competenciaParam)) {
    return NextResponse.json(
      { error: "competencia invalida (esperado AAAA-MM)" },
      { status: 422 },
    );
  }

  let query = supabase
    .from("situacoes_boleto")
    .select("id, veiculo_id, competencia, situacao, registrado_em, atualizado_em", {
      count: "exact",
    })
    .order("competencia", { ascending: false })
    .order("registrado_em", { ascending: false })
    .range(from, from + perPage - 1);

  if (competenciaParam) {
    query = query.eq("competencia", competenciaParaDate(competenciaParam));
  }
  if (veiculoId) query = query.eq("veiculo_id", veiculoId);
  if (situacaoParam) query = query.eq("situacao", situacaoParam);

  const { data, error, count } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({
    data: (data ?? []).map((r) => ({
      ...r,
      competencia: competenciaParaExibicao(r.competencia as string),
    })),
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

  const parsed = criarSituacaoBoletoSchema.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "dados invalidos", detalhes: parsed.error.flatten() },
      { status: 422 },
    );
  }
  const { veiculo_id, competencia, situacao } = parsed.data;

  // associacao_id vem do claim; a RLS (with check) e a coluna NOT NULL exigem
  // o valor. Le do operador logado para preencher a coluna.
  const { data: op } = await supabase
    .from("operadores")
    .select("associacao_id")
    .eq("id", user.id)
    .single();
  if (!op) return NextResponse.json({ error: "operador sem associacao" }, { status: 401 });

  // Verifica que o veiculo existe na associacao do operador e tem status ativo
  // (AC-006 e AC-007). A RLS restringe a visibilidade; se nao encontrar, 404.
  const { data: veiculo } = await supabase
    .from("veiculos")
    .select("id, status")
    .eq("id", veiculo_id)
    .single();

  if (!veiculo) {
    return NextResponse.json({ error: "veiculo nao encontrado" }, { status: 404 });
  }
  if (veiculo.status !== "ativo") {
    return NextResponse.json(
      { error: "o veiculo precisa ter status ativo para receber situacao de boleto" },
      { status: 422 },
    );
  }

  const competenciaDate = competenciaParaDate(competencia);

  const { data, error } = await supabase
    .from("situacoes_boleto")
    .insert({
      associacao_id: op.associacao_id,
      veiculo_id,
      competencia: competenciaDate,
      situacao,
    })
    .select("id, veiculo_id, competencia, situacao, registrado_em, atualizado_em")
    .single();

  if (error) {
    if (error.code === "23505") {
      return NextResponse.json(
        { error: "ja existe registro de situacao para esse veiculo nessa competencia" },
        { status: 409 },
      );
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(
    {
      ...data,
      competencia: competenciaParaExibicao(data.competencia as string),
    },
    { status: 201 },
  );
}
