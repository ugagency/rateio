import { z } from "zod";
import { competenciaValida } from "@/lib/competencia";

// Schema de criacao de situacao de boleto (SPEC-005). Compartilhavel entre
// cliente e servidor; a validacao autoritativa e do servidor.

export const SITUACOES = ["baixado", "aberto", "cancelado"] as const;
export type Situacao = (typeof SITUACOES)[number];

export const criarSituacaoBoletoSchema = z.object({
  veiculo_id: z.string().uuid("veiculo_id deve ser um UUID"),
  competencia: z
    .string()
    .refine(competenciaValida, "competencia invalida (esperado AAAA-MM)"),
  situacao: z.enum(SITUACOES, {
    errorMap: () => ({ message: "situacao deve ser baixado, aberto ou cancelado" }),
  }),
});

export type CriarSituacaoBoleto = z.infer<typeof criarSituacaoBoletoSchema>;

// Schema para atualizacao parcial (apenas o campo situacao e editavel via PATCH).
export const atualizarSituacaoBoletoSchema = z.object({
  situacao: z.enum(SITUACOES, {
    errorMap: () => ({ message: "situacao deve ser baixado, aberto ou cancelado" }),
  }),
});

export type AtualizarSituacaoBoleto = z.infer<typeof atualizarSituacaoBoletoSchema>;
