import { z } from "zod";
import { normalizarPlaca, placaValida } from "@/lib/validators/placa";
import { SEGMENTOS } from "@/lib/dominio";
import { COBERTURAS_TERCEIROS } from "@/lib/dominio";

// Schema de criação de veiculo (SPEC-003). Compartilhável entre cliente e
// servidor; a validação autoritativa é do servidor.
export const criarVeiculoSchema = z.object({
  associado_id: z.string().uuid("associado_id deve ser um UUID"),
  placa: z
    .string()
    .transform(normalizarPlaca)
    .refine(placaValida, "placa invalida (padrão antigo ABC1234 ou Mercosul ABC1D23)"),
  segmento: z.enum(SEGMENTOS, {
    errorMap: () => ({ message: "segmento deve ser LEVES, MOTOS ou PESADOS" }),
  }),
  fipe_valor: z
    .number({ invalid_type_error: "fipe_valor deve ser um numero" })
    .positive("fipe_valor deve ser maior que zero"),
  cobertura_terceiros: z.enum(COBERTURAS_TERCEIROS, {
    errorMap: () => ({ message: "cobertura_terceiros deve ser nenhuma, 50k ou 100k" }),
  }),
});

export type CriarVeiculo = z.infer<typeof criarVeiculoSchema>;
