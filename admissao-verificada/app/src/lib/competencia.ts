// Competência canônica (ADR-002 C3): armazenada como date no primeiro dia do
// mês; entrada AAAA-MM; exibição MM/AAAA. Helpers compartilhados pelas fatias
// de situação de boleto, eventos e exportação para não divergir.

const RE_AAAA_MM = /^\d{4}-(0[1-9]|1[0-2])$/;

export function competenciaValida(entrada: string): boolean {
  return RE_AAAA_MM.test((entrada || "").trim());
}

// "AAAA-MM" -> "AAAA-MM-01" (string de date para o Postgres).
export function competenciaParaDate(entrada: string): string {
  const v = (entrada || "").trim();
  if (!competenciaValida(v)) throw new Error("competência inválida (esperado AAAA-MM)");
  return `${v}-01`;
}

// "AAAA-MM-01" ou Date -> "MM/AAAA" para exibição.
export function competenciaParaExibicao(date: string): string {
  const [ano, mes] = date.slice(0, 7).split("-");
  return `${mes}/${ano}`;
}
