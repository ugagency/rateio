import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { competenciaParaDate, competenciaParaExibicao, competenciaValida } from "@/lib/competencia";
import { SEGMENTOS, type Segmento } from "@/lib/dominio";
import { SITUACOES, type Situacao } from "@/lib/schemas/situacao-boleto";

// SPEC-005 secao 5.2. Consolidacao dinamica por segmento e situacao para uma
// competencia. Sempre retorna os tres segmentos (LEVES, MOTOS, PESADOS) com
// zeros nos campos sem registro, para que o gerador da BASE nunca receba uma
// resposta incompleta (AC-008 e AC-009).
//
// O denominador da BASE e a soma de soma_cotas onde situacao = 'baixado' por
// segmento. As situacoes 'aberto' e 'cancelado' sao informativas; 'cancelado'
// nao entra no denominador nem no invariante (ADR-002 C1 e C7).

type BucketSituacao = { soma_cotas: number; qtd_veiculos: number };
type BucketSegmento = Record<Situacao, BucketSituacao>;

// Estrutura zerada para um segmento.
function bucketVazio(): BucketSegmento {
  const b = {} as BucketSegmento;
  for (const s of SITUACOES) {
    b[s] = { soma_cotas: 0, qtd_veiculos: 0 };
  }
  return b;
}

export async function GET(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  const sp = req.nextUrl.searchParams;
  const competenciaParam = sp.get("competencia");

  if (!competenciaParam || !competenciaValida(competenciaParam)) {
    return NextResponse.json(
      { error: "competencia invalida ou ausente (esperado AAAA-MM)" },
      { status: 422 },
    );
  }

  const competenciaDate = competenciaParaDate(competenciaParam);

  // Busca os registros de situacao com cota e segmento do veiculo associado.
  // Apenas veiculos com status 'ativo' entram na consolidacao (ADR-002 C1).
  // A RLS em situacoes_boleto filtra pelo tenant do operador automaticamente.
  const { data: linhas, error } = await supabase
    .from("situacoes_boleto")
    .select("situacao, veiculos!inner(segmento, cota, status)")
    .eq("competencia", competenciaDate)
    .eq("veiculos.status", "ativo");

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Inicializa todos os tres segmentos com zeros.
  const segmentos: Record<Segmento, BucketSegmento> = {} as Record<Segmento, BucketSegmento>;
  for (const seg of SEGMENTOS) {
    segmentos[seg] = bucketVazio();
  }

  // Agrega as cotas por segmento e situacao.
  for (const linha of linhas ?? []) {
    const veiculo = Array.isArray(linha.veiculos) ? linha.veiculos[0] : linha.veiculos;
    if (!veiculo) continue;
    const seg = veiculo.segmento as Segmento;
    const sit = linha.situacao as Situacao;
    if (!SEGMENTOS.includes(seg) || !SITUACOES.includes(sit)) continue;

    const bucket = segmentos[seg][sit];
    bucket.soma_cotas = +(bucket.soma_cotas + Number(veiculo.cota)).toFixed(2);
    bucket.qtd_veiculos += 1;
  }

  return NextResponse.json({
    competencia: competenciaParaExibicao(`${competenciaParam}-01`),
    segmentos,
  });
}
