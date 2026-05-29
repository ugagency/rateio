// Normalização e validação de placa (SPEC-003 secao 5.7).

export function normalizarPlaca(entrada: string): string {
  return (entrada || "").replace(/[\s-]/g, "").toUpperCase();
}

const ANTIGA = /^[A-Z]{3}[0-9]{4}$/;
const MERCOSUL = /^[A-Z]{3}[0-9][A-Z][0-9]{2}$/;

export function placaValida(entrada: string): boolean {
  const p = normalizarPlaca(entrada);
  return ANTIGA.test(p) || MERCOSUL.test(p);
}
