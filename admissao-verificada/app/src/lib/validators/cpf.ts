// Validação de CPF pelo algoritmo oficial (SPEC-002 secao 5.5).

export function normalizarCpf(entrada: string): string {
  return (entrada || "").replace(/\D/g, "");
}

export function cpfValido(entrada: string): boolean {
  const cpf = normalizarCpf(entrada);
  if (cpf.length !== 11) return false;
  // rejeita sequências uniformes (000...000, 111...111, ...)
  if (/^(\d)\1{10}$/.test(cpf)) return false;

  const dv = (base: string, pesoInicial: number): number => {
    let soma = 0;
    for (let i = 0; i < base.length; i++) {
      soma += Number(base[i]) * (pesoInicial - i);
    }
    const resto = soma % 11;
    return resto < 2 ? 0 : 11 - resto;
  };

  const d1 = dv(cpf.slice(0, 9), 10);
  const d2 = dv(cpf.slice(0, 10), 11);
  return d1 === Number(cpf[9]) && d2 === Number(cpf[10]);
}

// Máscara para exibição: três primeiros e dois últimos dígitos (SPEC-002 5.1).
export function mascararCpf(entrada: string): string {
  const cpf = normalizarCpf(entrada);
  if (cpf.length !== 11) return entrada;
  return `${cpf.slice(0, 3)}.***.***-${cpf.slice(9)}`;
}
