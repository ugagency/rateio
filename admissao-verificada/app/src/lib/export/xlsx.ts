/**
 * Escritor de BASE.xlsx e RATEIO.xlsx (SPEC-007).
 *
 * Espelha célula a célula o exportador de referência em Python
 * (reference/exportador.py). Os dois layouts devem ser idênticos para que
 * detectar_tipo e ler_base/ler_rateio_partes do motor aceitem os arquivos.
 *
 * ADR-002 C4: segmento armazenado no plural; BASE usa o singular (SEGMENTO_SINGULAR).
 * ADR-002 C3: data no formato dd/mm/aaaa nas células de data do RATEIO.
 */

import ExcelJS from "exceljs";
import { SEGMENTOS, SEGMENTO_SINGULAR, type Segmento } from "@/lib/dominio";

// Ordem dos segmentos na BASE e coluna inicial de cada bloco (espelha BLOCK_START
// do reference/exportador.py: PESADOS=1, MOTOS=6, LEVES=11).
const SEG_ORDER: Segmento[] = ["PESADOS", "MOTOS", "LEVES"];
const BLOCK_START: Record<Segmento, number> = { PESADOS: 1, MOTOS: 6, LEVES: 11 };

// Estrutura de cotas por segmento recebida pelo gerador da BASE.
export interface CotasSegmento {
  baixadas: number;
  abertas: number;
  canceladas: number;
}

// Estrutura de evento recebida pelo gerador do RATEIO.
export interface EventoExport {
  segmento: Segmento;
  // "ASSOCIADO" ou "TERCEIRO" (singular, como armazenado em eventos.envolvimento).
  envolvimento: string;
  tipo: "INTEGRAL" | "PARCIAL";
  protocolo: string | number;
  motivo?: string;
  placa: string;
  // dd/mm/aaaa — já formatado pelo chamador (route handler).
  data: string;
  valor: number;
}

// Mapeamento de envolvimento singular para plural (ADR-002 C4 e exportador.py).
const ENV_LABEL: Record<string, string> = {
  ASSOCIADO: "ASSOCIADOS",
  TERCEIRO: "TERCEIROS",
};

/**
 * Gera o arquivo BASE.xlsx em memória e retorna o Buffer.
 *
 * Espelha exportar_base() do reference/exportador.py:
 *   - Linha 1, col c0     : rótulo singular do segmento (PESADO, MOTO, LEVE)
 *   - Linha 3, col c0     : "Cota por Situação"
 *   - Linha 4, col c0+1   : "BAIXADO"
 *   - Linha 4, col c0+2   : "ABERTO"
 *   - Linha 4, col c0+3   : "CANCELADO"
 *   - Linha 5, col c0     : "TOTAL"
 *   - Linha 5, cols c0+1..3: contagens inteiras
 * Os três blocos ficam lado a lado (PESADOS em col 1, MOTOS em col 6, LEVES em col 11).
 */
export async function gerarBase(
  cotas: Record<Segmento, CotasSegmento>,
): Promise<Buffer> {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("BASE");

  for (const seg of SEG_ORDER) {
    const c0 = BLOCK_START[seg];
    const d: CotasSegmento = cotas[seg] ?? { baixadas: 0, abertas: 0, canceladas: 0 };

    // rótulo singular na linha 1
    ws.getCell(1, c0).value = SEGMENTO_SINGULAR[seg];
    // rótulo do sub-bloco na linha 3
    ws.getCell(3, c0).value = "Cota por Situação";
    // cabeçalho das situações na linha 4
    ws.getCell(4, c0 + 1).value = "BAIXADO";
    ws.getCell(4, c0 + 2).value = "ABERTO";
    ws.getCell(4, c0 + 3).value = "CANCELADO";
    // linha TOTAL com contagens inteiras na linha 5
    ws.getCell(5, c0).value = "TOTAL";
    ws.getCell(5, c0 + 1).value = Math.round(d.baixadas);
    ws.getCell(5, c0 + 2).value = Math.round(d.abertas);
    ws.getCell(5, c0 + 3).value = Math.round(d.canceladas);
  }

  const buf = await wb.xlsx.writeBuffer();
  return Buffer.from(buf);
}

/**
 * Gera o arquivo RATEIO.xlsx em memória e retorna o Buffer.
 *
 * Espelha exportar_rateio() do reference/exportador.py:
 *   - Linha 1: cabeçalho com PROTOCOLO (col 1), MOTIVO (col 3), ENVOLVIMENTO
 *     (col 4), SITUAÇÃO (col 5), PLACA (col 6), PARTICIPAÇÃO (col 7),
 *     DATA COMUNIC (col 8), TIPO EVENTO (col 9), MÊS REF (col 10),
 *     VALOR RATEADO (col 11).
 *   - Eventos agrupados por (segmento, envolvimento), ordenados por data (FIFO).
 *   - Primeira linha de cada grupo: marcador de seção na coluna A
 *     (ex.: "LEVES ASSOCIADOS").
 *   - Linhas sem protocolo ou com valor <= 0 são ignoradas (SPEC-007 sec. 5).
 *   - protocolo numérico escrito como inteiro; alfanumérico como texto.
 */
export async function gerarRateio(eventos: EventoExport[]): Promise<Buffer> {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("RATEIO");

  // Cabeçalho na linha 1 (espelha o dict cab do exportador.py).
  const cabecalho: Record<number, string> = {
    1: "PROTOCOLO",
    3: "MOTIVO",
    4: "ENVOLVIMENTO",
    5: "SITUAÇÃO",
    6: "PLACA",
    7: "PARTICIPAÇÃO",
    8: "DATA COMUNIC",
    9: "TIPO EVENTO",
    10: "MÊS REF",
    11: "VALOR RATEADO",
  };
  for (const [col, valor] of Object.entries(cabecalho)) {
    ws.getCell(1, Number(col)).value = valor;
  }

  // Ordena por segmento, envolvimento e data (FIFO — espelha sorted() do Python).
  const ordenados = [...eventos].sort((a, b) => {
    const segA = a.segmento.localeCompare(b.segmento);
    if (segA !== 0) return segA;
    const envA = a.envolvimento.localeCompare(b.envolvimento);
    if (envA !== 0) return envA;
    return a.data.localeCompare(b.data);
  });

  let linha = 2;
  let grupoAtual: string | null = null;

  for (const ev of ordenados) {
    // Ignora eventos sem protocolo ou com valor menor ou igual a zero (SPEC-007 sec. 5).
    if (!ev.protocolo || ev.valor <= 0) continue;

    const envPlural = ENV_LABEL[ev.envolvimento] ?? ev.envolvimento;
    const marcador = `${ev.segmento} ${envPlural}`;

    // Insere linha de marcador de seção quando o grupo muda.
    if (marcador !== grupoAtual) {
      ws.getCell(linha, 1).value = marcador;
      linha += 1;
      grupoAtual = marcador;
    }

    // Protocolo: inteiro se for string de dígitos; texto caso contrário.
    const protoStr = String(ev.protocolo);
    const protoValor = /^\d+$/.test(protoStr) ? parseInt(protoStr, 10) : protoStr;

    ws.getCell(linha, 1).value = protoValor;
    ws.getCell(linha, 2).value = `INDENIZAÇÃO ${ev.tipo}`;
    ws.getCell(linha, 3).value = ev.motivo ?? "";
    ws.getCell(linha, 4).value = envPlural;
    ws.getCell(linha, 6).value = ev.placa;
    ws.getCell(linha, 8).value = ev.data;
    ws.getCell(linha, 9).value = ev.tipo;
    ws.getCell(linha, 11).value = ev.valor;

    linha += 1;
  }

  const buf = await wb.xlsx.writeBuffer();
  return Buffer.from(buf);
}
