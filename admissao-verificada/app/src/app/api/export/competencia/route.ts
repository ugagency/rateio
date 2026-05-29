import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { competenciaParaDate, competenciaValida } from "@/lib/competencia";
import { SEGMENTOS, type Segmento } from "@/lib/dominio";
import { gerarBase, gerarRateio, type CotasSegmento, type EventoExport } from "@/lib/export/xlsx";
import crypto from "node:crypto";

// SPEC-007 secao 7. POST /api/export/competencia
// Body: { competencia: "AAAA-MM" }
//
// Gera BASE.xlsx e RATEIO.xlsx para a competencia informada e registra em
// exportacoes (trilha de auditoria). Retorna os buffers codificados em base64
// para download direto pelo cliente.
//
// O associacao_id NAO vem do corpo da requisicao; e inferido do operador
// logado (claim do JWT). A RLS protege situacoes_boleto, eventos_mes e
// exportacoes automaticamente.

// Deriva segmento e envolvimento a partir do marcador_secao armazenado na
// tabela eventos_mes (ex.: "LEVES ASSOCIADOS" -> { segmento: "LEVES",
// envolvimento: "ASSOCIADO" }). Espelha o que o exportador.py recebe.
function parsearMarcador(marcador: string): { segmento: Segmento; envolvimento: string } | null {
  // marcador_secao: "SEGMENTO ENVOLVIMENTO_PLURAL" (ADR-002 C4)
  const partes = (marcador || "").trim().split(" ");
  if (partes.length < 2) return null;
  const envPlural = partes[partes.length - 1]; // "ASSOCIADOS" ou "TERCEIROS"
  const segmento = partes.slice(0, partes.length - 1).join(" ") as Segmento;
  if (!SEGMENTOS.includes(segmento)) return null;
  // Converte plural para singular esperado pelo gerador do RATEIO
  // (exportador.py recebe envolvimento no singular: ASSOCIADO / TERCEIRO).
  const envSingular = envPlural === "ASSOCIADOS" ? "ASSOCIADO" : "TERCEIRO";
  return { segmento, envolvimento: envSingular };
}

export async function POST(req: NextRequest) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "nao autenticado" }, { status: 401 });

  // Valida o payload de entrada.
  const body = await req.json().catch(() => ({}));
  const competenciaParam: unknown = body?.competencia;
  if (typeof competenciaParam !== "string" || !competenciaValida(competenciaParam)) {
    return NextResponse.json(
      { error: "competencia invalida ou ausente (esperado AAAA-MM)" },
      { status: 422 },
    );
  }

  // Infere associacao_id do operador logado (mesmo padrao de /api/associados).
  const { data: op } = await supabase
    .from("operadores")
    .select("associacao_id")
    .eq("id", user.id)
    .single();
  if (!op) return NextResponse.json({ error: "operador sem associacao" }, { status: 401 });

  const competenciaDate = competenciaParaDate(competenciaParam);

  // --- Consolida situacoes de boleto por segmento (SPEC-005) ---
  // Apenas veiculos com status 'ativo' entram na BASE (ADR-002 C1).
  const { data: linhasBoleto, error: errBoleto } = await supabase
    .from("situacoes_boleto")
    .select("situacao, veiculos!inner(segmento, cota, status)")
    .eq("competencia", competenciaDate)
    .eq("veiculos.status", "ativo");

  if (errBoleto) return NextResponse.json({ error: errBoleto.message }, { status: 500 });

  // Inicializa cotas zeradas para todos os segmentos.
  const cotasPorSegmento: Record<Segmento, CotasSegmento> = {} as Record<Segmento, CotasSegmento>;
  for (const seg of SEGMENTOS) {
    cotasPorSegmento[seg] = { baixadas: 0, abertas: 0, canceladas: 0 };
  }

  for (const linha of linhasBoleto ?? []) {
    const veiculo = Array.isArray(linha.veiculos) ? linha.veiculos[0] : linha.veiculos;
    if (!veiculo) continue;
    const seg = veiculo.segmento as Segmento;
    if (!SEGMENTOS.includes(seg)) continue;
    const cota = Number(veiculo.cota);

    switch (linha.situacao) {
      case "baixado":
        cotasPorSegmento[seg].baixadas = +(cotasPorSegmento[seg].baixadas + cota).toFixed(2);
        break;
      case "aberto":
        cotasPorSegmento[seg].abertas = +(cotasPorSegmento[seg].abertas + cota).toFixed(2);
        break;
      case "cancelado":
        cotasPorSegmento[seg].canceladas = +(cotasPorSegmento[seg].canceladas + cota).toFixed(2);
        break;
    }
  }

  // --- Busca eventos ativos da competencia (SPEC-006, tabela eventos_mes) ---
  // Filtra apenas status 'ativo'; ordenacao garante agrupamento FIFO por marcador.
  const { data: linhasEvento, error: errEvento } = await supabase
    .from("eventos_mes")
    .select("marcador_secao, tipo, protocolo, motivo, placa, data_comunicacao, valor_rateado")
    .eq("competencia", competenciaDate)
    .eq("status", "ativo")
    .order("marcador_secao", { ascending: true })
    .order("data_comunicacao", { ascending: true });

  if (errEvento) return NextResponse.json({ error: errEvento.message }, { status: 500 });

  // Transforma os eventos no formato esperado pelo gerador do RATEIO.
  const eventos: EventoExport[] = [];
  for (const ev of linhasEvento ?? []) {
    // Ignora linhas sem protocolo ou com valor <= 0 (SPEC-007 sec. 5).
    if (!ev.protocolo || Number(ev.valor_rateado) <= 0) continue;

    const parsed = parsearMarcador(ev.marcador_secao as string);
    if (!parsed) continue;

    // Converte data_comunicacao (YYYY-MM-DD) para dd/mm/aaaa (formato do motor).
    const [ano, mes, dia] = (ev.data_comunicacao as string).split("-");
    const dataFormatada = `${dia}/${mes}/${ano}`;

    eventos.push({
      segmento: parsed.segmento,
      envolvimento: parsed.envolvimento,
      tipo: ev.tipo as "INTEGRAL" | "PARCIAL",
      protocolo: ev.protocolo,
      motivo: ev.motivo ?? "",
      placa: ev.placa,
      data: dataFormatada,
      valor: Number(ev.valor_rateado),
    });
  }

  // --- Gera os dois arquivos ---
  let bufBase: Buffer;
  let bufRateio: Buffer;
  try {
    [bufBase, bufRateio] = await Promise.all([
      gerarBase(cotasPorSegmento),
      gerarRateio(eventos),
    ]);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ error: `falha ao gerar arquivo: ${msg}` }, { status: 500 });
  }

  // Nomes de arquivo com sufixo de competencia (AC-3: BASE_AAAAMM.xlsx).
  const sufixo = competenciaParam.replace("-", "");
  const nomeBase = `BASE_${sufixo}.xlsx`;
  const nomeRateio = `RATEIO_${sufixo}.xlsx`;

  // Hash SHA-256 de cada arquivo para trilha de auditoria.
  const hashBase = crypto.createHash("sha256").update(bufBase).digest("hex");
  const hashRateio = crypto.createHash("sha256").update(bufRateio).digest("hex");

  // --- Registra na trilha de auditoria (exportacoes) ---
  const registros = [
    {
      associacao_id: op.associacao_id,
      competencia: competenciaDate,
      tipo: "BASE",
      arquivo: nomeBase,
      hash: hashBase,
      criado_por: user.id,
    },
    {
      associacao_id: op.associacao_id,
      competencia: competenciaDate,
      tipo: "RATEIO",
      arquivo: nomeRateio,
      hash: hashRateio,
      criado_por: user.id,
    },
  ];

  const { error: errAuditoria } = await supabase.from("exportacoes").insert(registros);
  // Falha de auditoria nao bloqueia a entrega dos arquivos; apenas loga.
  if (errAuditoria) {
    console.error("[export] falha ao registrar exportacao:", errAuditoria.message);
  }

  // --- Log de observabilidade (SPEC-007 sec. 9) ---
  const eventosPosMarcador: Record<string, number> = {};
  for (const ev of eventos) {
    const marcador = `${ev.segmento} ${ev.envolvimento === "ASSOCIADO" ? "ASSOCIADOS" : "TERCEIROS"}`;
    eventosPosMarcador[marcador] = (eventosPosMarcador[marcador] ?? 0) + 1;
  }
  console.info("[export]", {
    competencia: competenciaParam,
    cotas: cotasPorSegmento,
    eventosPosMarcador,
    hashBase,
    hashRateio,
  });

  // Retorna os arquivos codificados em base64 para download direto pelo cliente.
  return NextResponse.json({
    competencia: competenciaParam,
    base: {
      nome: nomeBase,
      hash: hashBase,
      conteudo: bufBase.toString("base64"),
    },
    rateio: {
      nome: nomeRateio,
      hash: hashRateio,
      conteudo: bufRateio.toString("base64"),
    },
  });
}
