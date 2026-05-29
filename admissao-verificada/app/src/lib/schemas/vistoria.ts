import { z } from "zod";

// Tipos de etapa válidos conforme a migration (SPEC-004 secao 4.2).
export const TIPOS_ETAPA = [
  "selfie",
  "documento",
  "frente",
  "traseira",
  "lateral_esquerda",
  "lateral_direita",
  "teto",
  "placa",
  "chassi",
  "outro",
] as const;
export type TipoEtapa = (typeof TIPOS_ETAPA)[number];

// Tipos de câmera preferencial.
export const CAMERAS = ["frontal", "traseira"] as const;
export type CameraPreferencial = (typeof CAMERAS)[number];

// Tipos de script de vistoria válidos.
export const TIPOS_SCRIPT = ["carro", "moto", "reboque", "revistoria"] as const;
export type TipoScript = (typeof TIPOS_SCRIPT)[number];

// Schema de uma etapa dentro do payload de criação de script.
export const etapaScriptSchema = z.object({
  sequencia: z.number().int().min(1, "sequencia deve ser maior que zero"),
  tipo_etapa: z.enum(TIPOS_ETAPA, { message: "tipo_etapa invalido" }),
  camera_preferencial: z.enum(CAMERAS).default("traseira"),
  obrigatoria: z.boolean().default(true),
  instrucao_texto: z.string().optional(),
});
export type EtapaScriptInput = z.infer<typeof etapaScriptSchema>;

// Schema de criação de script de vistoria (POST /api/scripts-vistoria).
export const criarScriptVistoriaSchema = z
  .object({
    tipo: z.enum(TIPOS_SCRIPT, { message: "tipo invalido" }),
    descricao: z.string().optional(),
    tempo_max_min: z.number().int().min(1, "tempo_max_min deve ser maior que zero"),
    etapas: z.array(etapaScriptSchema).min(1, "ao menos uma etapa e obrigatoria"),
  })
  .refine(
    (v) => {
      const seqs = v.etapas.map((e) => e.sequencia);
      return seqs.length === new Set(seqs).size;
    },
    { message: "sequencias das etapas devem ser unicas" },
  );
export type CriarScriptVistoria = z.infer<typeof criarScriptVistoriaSchema>;

// Schema de iniciação de vistoria (POST /api/vistorias).
export const iniciarVistoriaSchema = z.object({
  veiculo_id: z.string().uuid("veiculo_id deve ser um UUID"),
  script_id: z.string().uuid("script_id deve ser um UUID"),
});
export type IniciarVistoria = z.infer<typeof iniciarVistoriaSchema>;
