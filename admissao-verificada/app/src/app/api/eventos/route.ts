import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { criarEventoSchema } from "@/lib/schemas/evento";
import {
  competenciaParaDate,
  competenciaParaExibicao,
  competenciaValida,
} from "@/lib/competencia";

// SPEC-006 secao 5.1 e 5.2. O associacao_id NAO vem da URL; e inferido do
// operador logado (claim do JWT, aplicado pela RLS). A unicidade de protocolo
// por competencia e associacao e garantida pela constraint do banco (409).

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const competenciaParam = sp.get("competencia");
  const marcadorSecao = sp.get("marcador_secao");
  const tipo = sp.get("tipo");
  const placa = sp.get("placa");
  const status = sp.get("status") ?? "ativo";
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
    .from("eventos_mes")
    .select(
      "id, competencia, marcador_secao, tipo, protocolo, motivo, placa, data_comunicacao, valor_rateado, status, criado_em",
      { count: "exact" },
    )
    .eq("status", status)
    .order("competencia", { ascending: false })
    .order("data_comunicacao", { ascending: true })
    .range(from, from + perPage - 1);

  if (competenciaParam) {
    query = query.eq("competencia", competenciaParaDate(competenciaParam));
  }
  if (marcadorSecao) query = query.eq("marcador_secao", marcadorSecao);
  if (tipo) query = query.eq("tipo", tipo);
  if (placa) query = query.ilike("placa", `%${placa}%`);

  const { data, error, count } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({
    data: (data ?? []).map((ev) => ({
      ...ev,
      competencia: competenciaParaExibicao(ev.competencia as string),
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

  const parsed = criarEventoSchema.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "dados invalidos", detalhes: parsed.error.flatten() },
      { status: 422 },
    );
  }
  const {
    competencia,
    marcador_secao,
    tipo,
    protocolo,
    motivo,
    placa,
    data_comunicacao,
    valor_rateado,
  } = parsed.data;

  // associacao_id vem do claim; a RLS (with check) e a coluna NOT NULL exigem
  // o valor. Le do operador logado para preencher a coluna.
  const { data: op } = await supabase
    .from("operadores")
    .select("associacao_id")
    .eq("id", user.id)
    .single();
  if (!op) return NextResponse.json({ error: "operador sem associacao" }, { status: 401 });

  const competenciaDate = competenciaParaDate(competencia);

  const { data, error } = await supabase
    .from("eventos_mes")
    .insert({
      associacao_id: op.associacao_id,
      competencia: competenciaDate,
      marcador_secao,
      tipo,
      protocolo,
      motivo: motivo || null,
      placa,
      data_comunicacao,
      valor_rateado,
    })
    .select(
      "id, competencia, marcador_secao, tipo, protocolo, motivo, placa, data_comunicacao, valor_rateado, status, criado_em",
    )
    .single();

  if (error) {
    if (error.code === "23505") {
      return NextResponse.json(
        { error: "protocolo ja cadastrado nesta competencia" },
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
