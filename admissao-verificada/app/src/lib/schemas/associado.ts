import { z } from "zod";
import { cpfValido, normalizarCpf } from "@/lib/validators/cpf";

// Schema de criação de associado (SPEC-002). Compartilhável entre cliente e
// servidor; a validação autoritativa é do servidor.
export const criarAssociadoSchema = z.object({
  nome: z.string().trim().min(1, "nome é obrigatório"),
  cpf: z
    .string()
    .transform(normalizarCpf)
    .refine((v) => v.length === 11, "CPF deve ter 11 dígitos")
    .refine(cpfValido, "CPF inválido"),
  email: z.string().email("e-mail inválido").optional().or(z.literal("")),
  telefone: z.string().optional().or(z.literal("")),
});

export type CriarAssociado = z.infer<typeof criarAssociadoSchema>;
