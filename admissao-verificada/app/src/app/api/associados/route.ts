import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { criarAssociadoSchema } from "@/lib/schemas/associado";
import { mascararCpf } from "@/lib/validators/cpf";

// SPEC-002 secao 5. O associacao_id NÃO vem da URL; é inferido do operador
// logado (claim do JWT, aplicado pela RLS). A unicidade de CPF por associação
// é garantida pela constraint do banco (409).

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const q = sp.get("q");
  const status = sp.get("status") ?? "ativo";
  const page = Math.max(1, Number(sp.get("page") ?? 1));
  const perPage = Math.min(200, Math.max(1, Number(sp.get("per_page") ?? 50)));
  const from = (page - 1) * perPage;

  let query = supabase
    .from("associados")
    .select("id, nome, cpf, email, telefone, status, criado_em", { count: "exact" })
    .eq("status", status)
    .order("nome", { ascending: true })
    .range(from, from + perPage - 1);
  if (q) query = query.ilike("nome", `%${q}%`);

  const { data, error, count } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({
    data: (data ?? []).map((a) => ({ ...a, cpf: undefined, cpf_mascarado: mascararCpf(a.cpf) })),
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

  const parsed = criarAssociadoSchema.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "dados invalidos", detalhes: parsed.error.flatten() },
      { status: 422 },
    );
  }
  const { nome, cpf, email, telefone } = parsed.data;

  // associacao_id vem do claim; a RLS (with check) e a coluna NOT NULL exigem
  // o valor. Lê do operador logado para preencher a coluna.
  const { data: op } = await supabase
    .from("operadores")
    .select("associacao_id")
    .eq("id", user.id)
    .single();
  if (!op) return NextResponse.json({ error: "operador sem associacao" }, { status: 401 });

  const { data, error } = await supabase
    .from("associados")
    .insert({
      associacao_id: op.associacao_id,
      nome,
      cpf,
      email: email || null,
      telefone: telefone || null,
    })
    .select("id, nome, cpf, email, telefone, status, criado_em")
    .single();

  if (error) {
    if (error.code === "23505") {
      return NextResponse.json({ error: "CPF ja cadastrado na associacao" }, { status: 409 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(
    { ...data, cpf: undefined, cpf_mascarado: mascararCpf(data.cpf) },
    { status: 201 },
  );
}
