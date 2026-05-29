import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { criarVeiculoSchema } from "@/lib/schemas/veiculo";

// SPEC-003 secao 5. O associacao_id NAO vem da URL; e inferido do operador
// logado (claim do JWT, aplicado pela RLS). A unicidade de placa por associacao
// e garantida pela constraint do banco (409). A cota e calculada pela tabela
// faixas_cota vigente no momento da operacao (secao 5.6).

// Calcula a cota a partir das faixas vigentes para a associacao.
// Retorna null se nenhuma faixa estiver configurada.
async function calcularCota(
  supabase: Awaited<ReturnType<typeof createSupabaseServerClient>>,
  fipeValor: number,
): Promise<{ cota: number; faixaAplicada: string } | null> {
  const hoje = new Date().toISOString().slice(0, 10);

  // Faixas com fipe_ate finito primeiro (ascendente), depois a faixa aberta (nulo).
  // A query ordena nulls last para garantir que a faixa especial fica ao final.
  const { data: faixas, error } = await supabase
    .from("faixas_cota")
    .select("fipe_ate, cota_valor")
    .lte("vigente_desde", hoje)
    .order("fipe_ate", { ascending: true, nullsFirst: false });

  if (error || !faixas || faixas.length === 0) return null;

  // SPEC-003 secao 5.6: primeira faixa com fipe_ate >= fipe_valor; se
  // nenhuma, a faixa com fipe_ate nulo.
  for (const faixa of faixas) {
    if (faixa.fipe_ate !== null && faixa.fipe_ate >= fipeValor) {
      const rotulo =
        faixas.indexOf(faixa) === 0
          ? `ate-${faixa.fipe_ate}`
          : `${faixas[faixas.indexOf(faixa) - 1].fipe_ate}-${faixa.fipe_ate}`;
      return { cota: Number(faixa.cota_valor), faixaAplicada: rotulo };
    }
  }

  // Nenhuma faixa finita cobriu o valor; usa a faixa especial (fipe_ate nulo).
  const faixaEspecial = faixas.find((f) => f.fipe_ate === null);
  if (faixaEspecial) {
    return { cota: Number(faixaEspecial.cota_valor), faixaAplicada: "acima-do-limite" };
  }

  return null;
}

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const q = sp.get("q");
  const segmento = sp.get("segmento");
  const status = sp.get("status");
  const associadoId = sp.get("associado_id");
  const page = Math.max(1, Number(sp.get("page") ?? 1));
  const perPage = Math.min(200, Math.max(1, Number(sp.get("per_page") ?? 50)));
  const from = (page - 1) * perPage;

  let query = supabase
    .from("veiculos")
    .select(
      "id, associado_id, placa, segmento, fipe_valor, cobertura_terceiros, cota, status, criado_em",
      { count: "exact" },
    )
    .order("placa", { ascending: true })
    .range(from, from + perPage - 1);

  if (q) query = query.ilike("placa", `%${q}%`);
  if (segmento) query = query.eq("segmento", segmento);
  if (status) query = query.eq("status", status);
  if (associadoId) query = query.eq("associado_id", associadoId);

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

  const parsed = criarVeiculoSchema.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "dados invalidos", detalhes: parsed.error.flatten() },
      { status: 422 },
    );
  }
  const { associado_id, placa, segmento, fipe_valor, cobertura_terceiros } = parsed.data;

  // associacao_id vem do claim; a RLS (with check) e a coluna NOT NULL exigem
  // o valor. Le do operador logado para preencher a coluna.
  const { data: op } = await supabase
    .from("operadores")
    .select("associacao_id")
    .eq("id", user.id)
    .single();
  if (!op) return NextResponse.json({ error: "operador sem associacao" }, { status: 401 });

  // Verifica que o associado existe na associacao do operador (AC-011).
  // A RLS restringe a visibilidade, entao se nao encontrar retorna 404.
  const { data: associado } = await supabase
    .from("associados")
    .select("id")
    .eq("id", associado_id)
    .single();
  if (!associado) {
    return NextResponse.json({ error: "associado nao encontrado" }, { status: 404 });
  }

  // Calcula a cota pela tabela de faixas vigente (SPEC-003 secao 5.6).
  const resultado = await calcularCota(supabase, fipe_valor);
  if (!resultado) {
    return NextResponse.json(
      {
        error:
          "nenhuma faixa de cota configurada para esta associacao; configure a tabela faixas_cota antes de cadastrar veiculos",
      },
      { status: 500 },
    );
  }

  const { data, error } = await supabase
    .from("veiculos")
    .insert({
      associacao_id: op.associacao_id,
      associado_id,
      placa,
      segmento,
      fipe_valor,
      cobertura_terceiros,
      cota: resultado.cota,
    })
    .select(
      "id, associado_id, placa, segmento, fipe_valor, cobertura_terceiros, cota, status, criado_em",
    )
    .single();

  if (error) {
    if (error.code === "23505") {
      return NextResponse.json({ error: "placa ja cadastrada na associacao" }, { status: 409 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data, { status: 201 });
}
