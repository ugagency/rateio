# ADR-001 — Arquitetura do MVP de Admissão Verificada

Status: aceito. Data: 2026-05-29.

## Contexto

Precisamos de um MVP enxuto que gere a base capaz de produzir os arquivos do
rateio, com a vistoria como estágio de admissão verificada. Já existe uma
fundação SDD com protótipo em Next.js mais Supabase (a parte de motor de
rateio genérico foi descartada). O motor de rateio aprovado vive em Python e
não pode ser alterado.

## Decisões

1. Stack de aplicação: Next.js 15, Supabase (Postgres mais Auth mais Storage)
   e TypeScript. Reaproveita a fundação existente (autenticação, multi-tenant
   por RLS, esqueleto de associados e veículos). Razão: já está scaffold,
   alinha com o documento estratégico e acelera o MVP.

2. Multi-tenant por RLS desde o início, mesmo com uma associação só no MVP.
   Razão: barato agora, evita retrabalho de isolamento depois.

3. Vistoria como PWA com captura ao vivo pela câmera (getUserMedia), sem app
   nativo no MVP. Razão: entrega a regra antifraude essencial (captura ao vivo,
   carimbo de data, hora e geolocalização, fluxo sequencial) sem o custo de
   publicar app em loja. App nativo fica para fase posterior.

4. Integração com o motor de rateio por exportação de arquivo. O app gera
   BASE.xlsx e RATEIO.xlsx; o motor os ingere por `FonteFechamentoXlsx` e
   `ingestao_partes`. Razão: respeita a regra de não tocar o motor e usa o
   contrato que ele já lê. Conector por API fica para depois (o motor já tem o
   adaptador `FonteSGAHttp` previsto).

5. O contrato de exportação é derivado do leitor real do motor, não inventado.
   Os validadores do motor (`detectar_tipo`, `validar_slot`,
   `tools/reconciliar.py`) são o oráculo de aceite.

6. Storage de fotos da vistoria no Supabase Storage, com metadados (timestamp,
   geolocalização, ordem) no Postgres e imutabilidade após finalização.

## Consequências

- O app novo e o motor permanecem desacoplados; o ponto de contato é o arquivo.
- A reconciliação automatiza a prova de que a base gerada serve ao rateio.
- A captura por PWA tem limites de hardware e permissão de navegador; aceitável
  no MVP, revisitado quando houver app nativo.

## Alternativas descartadas

- Reimplementar o rateio no app (TypeScript): descartado por decisão de
  produto. O motor aprovado é o único de produção.
- Integração imediata por API com o motor: adia-se; exportação por arquivo é
  suficiente e mais simples para o MVP.
