// Constantes de domínio compartilhadas (ADR-002 C4). Fonte única para
// segmentos, marcadores de seção e o mapeamento de rótulos dos arquivos.

export const SEGMENTOS = ["LEVES", "MOTOS", "PESADOS"] as const;
export type Segmento = (typeof SEGMENTOS)[number];

export const ENVOLVIMENTOS = ["ASSOCIADOS", "TERCEIROS"] as const;
export type Envolvimento = (typeof ENVOLVIMENTOS)[number];

// Os seis marcadores de seção do RATEIO (segmento + envolvimento).
export const MARCADORES_SECAO = [
  "LEVES ASSOCIADOS",
  "LEVES TERCEIROS",
  "MOTOS ASSOCIADOS",
  "MOTOS TERCEIROS",
  "PESADOS ASSOCIADOS",
  "PESADOS TERCEIROS",
] as const;
export type MarcadorSecao = (typeof MARCADORES_SECAO)[number];

// Rótulo singular usado nas colunas da BASE (o app guarda no plural).
export const SEGMENTO_SINGULAR: Record<Segmento, string> = {
  LEVES: "LEVE",
  MOTOS: "MOTO",
  PESADOS: "PESADO",
};

export const COBERTURAS_TERCEIROS = ["nenhuma", "50k", "100k"] as const;
export type CoberturaTerceiros = (typeof COBERTURAS_TERCEIROS)[number];
