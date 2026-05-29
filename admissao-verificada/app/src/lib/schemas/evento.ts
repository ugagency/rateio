import { z } from "zod";
import { competenciaValida } from "@/lib/competencia";
import { normalizarPlaca } from "@/lib/validators/placa";
import { MARCADORES_SECAO } from "@/lib/dominio";

// Schema de criacao de evento do mes (SPEC-006). Compartilhavel entre cliente
// e servidor; a validacao autoritativa e do servidor.

export const TIPOS_EVENTO = ["INTEGRAL", "PARCIAL"] as const;
export type TipoEvento = (typeof TIPOS_EVENTO)[number];

export const criarEventoSchema = z.object({
  competencia: z
    .string()
    .refine(competenciaValida, "competencia invalida (esperado AAAA-MM)"),
  marcador_secao: z.enum(MARCADORES_SECAO, {
    errorMap: () => ({ message: "marcador de secao invalido" }),
  }),
  tipo: z.enum(TIPOS_EVENTO, {
    errorMap: () => ({ message: "tipo deve ser INTEGRAL ou PARCIAL" }),
  }),
  protocolo: z.string().trim().min(1, "protocolo e obrigatorio"),
  motivo: z.string().optional().or(z.literal("")),
  placa: z
    .string()
    .trim()
    .min(1, "placa e obrigatoria")
    .transform(normalizarPlaca),
  data_comunicacao: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "data de comunicacao invalida (esperado YYYY-MM-DD)"),
  valor_rateado: z
    .number({ invalid_type_error: "valor rateado deve ser um numero" })
    .gt(0, "valor rateado deve ser maior que zero"),
});

export type CriarEvento = z.infer<typeof criarEventoSchema>;
