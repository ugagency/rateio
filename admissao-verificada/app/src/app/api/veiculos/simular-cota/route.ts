import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

// SPEC-003 secao 5.5. Calcula a cota prevista para um valor FIPE sem gravar
// nenhum registro. Utilizado pelo formulario de cadastro para exibir a cota
// simulada ao sair do campo FIPE.

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const raw = sp.get("fipe_valor");
  const fipeValor = raw !== null ? Number(raw) : NaN;

  if (!raw || isNaN(fipeValor) || fipeValor <= 0) {
    return NextResponse.json(
      { error: "fipe_valor deve ser um numero positivo" },
      { status: 422 },
    );
  }

  const hoje = new Date().toISOString().slice(0, 10);

  // Faixas com fipe_ate finito em ordem crescente; a faixa especial (nulo) fica ao final.
  const { data: faixas, error } = await supabase
    .from("faixas_cota")
    .select("fipe_ate, cota_valor")
    .lte("vigente_desde", hoje)
    .order("fipe_ate", { ascending: true, nullsFirst: false });

  if (error || !faixas || faixas.length === 0) {
    return NextResponse.json(
      {
        error:
          "nenhuma faixa de cota configurada para esta associacao; configure a tabela faixas_cota",
      },
      { status: 500 },
    );
  }

  // Algoritmo SPEC-003 secao 5.6: primeira faixa com fipe_ate >= fipe_valor;
  // se nenhuma, a faixa com fipe_ate nulo.
  for (let i = 0; i < faixas.length; i++) {
    const faixa = faixas[i];
    if (faixa.fipe_ate !== null && faixa.fipe_ate >= fipeValor) {
      const anterior = i > 0 ? faixas[i - 1].fipe_ate : null;
      const faixaAplicada =
        anterior !== null ? `${anterior}-${faixa.fipe_ate}` : `ate-${faixa.fipe_ate}`;
      return NextResponse.json({
        fipe_valor: fipeValor,
        cota: Number(faixa.cota_valor),
        faixa_aplicada: faixaAplicada,
      });
    }
  }

  // Faixa especial (fipe_ate nulo).
  const especial = faixas.find((f) => f.fipe_ate === null);
  if (especial) {
    return NextResponse.json({
      fipe_valor: fipeValor,
      cota: Number(especial.cota_valor),
      faixa_aplicada: "acima-do-limite",
    });
  }

  return NextResponse.json(
    {
      error:
        "nenhuma faixa de cota configurada para esta associacao; configure a tabela faixas_cota",
    },
    { status: 500 },
  );
}
