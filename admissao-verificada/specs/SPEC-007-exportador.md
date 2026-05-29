# SPEC-007 — Exportador de BASE e RATEIO

> Componente que gera os arquivos BASE.xlsx e RATEIO.xlsx de uma competência, no
> layout que o motor aprovado lê. Fecha RF-EXP-01, RF-EXP-02 e RF-EXP-03.
> Espelha o leitor `ingestao_partes` (não inventa posições). Segue ADR-002.

## 1. Contexto

A SPEC-000 define o contrato dos arquivos e o oráculo de aceite. Esta spec
define o componente que de fato produz os dois arquivos a partir da base do
app, dado uma associação e uma competência. O cálculo do rateio não acontece
aqui; o exportador apenas serializa os insumos no layout do motor.

## 2. Requisitos

- RF-EXP-01: exportar a BASE da competência no layout do motor.
- RF-EXP-02: exportar o RATEIO da competência no layout do motor.
- RF-EXP-03: os arquivos exportados passam em `detectar_tipo` com o tipo correto.

## 3. Critérios de aceite (Given/When/Then)

- AC-1: Given uma competência com veículos ativos e situação de boleto, When o
  exportador gera a BASE, Then `detectar_tipo` retorna BASE e `ler_base`
  devolve cotas baixadas por segmento iguais à consolidação do app (SPEC-005).
- AC-2: Given eventos válidos na competência, When o exportador gera o RATEIO,
  Then `detectar_tipo` retorna RATEIO e a soma de Valor Rateado por marcador
  confere com a base do app (SPEC-006).
- AC-3: Given um pedido de exportação, When concluído, Then gera os dois
  arquivos nomeados BASE_AAAAMM.xlsx e RATEIO_AAAAMM.xlsx referentes à mesma
  competência (ADR-002 C3).

## 4. Geração da BASE

O exportador espelha `ler_base`. Layout mínimo compatível:
- Linha 1: rótulos de segmento iniciando cada bloco de colunas, no singular:
  PESADO, MOTO, LEVE (ADR-002 C4).
- Em cada bloco, sub-bloco Cota por Situação com cabeçalho contendo BAIXADO,
  ABERTO, CANCELADO e uma linha TOTAL com as contagens de cotas por situação do
  segmento na competência. BAIXADO é o denominador (ADR-002 C7).
- Sub-bloco Quantidade de Boletos por situação, para conferência.
- Os blocos dos três segmentos ficam lado a lado.

As contagens vêm da consolidação por segmento da SPEC-005 (cotas baixadas,
abertas, canceladas). O exportador não recalcula situação; apenas soma e
posiciona.

## 5. Geração do RATEIO

- Para cada evento da competência (SPEC-006), uma linha sob o marcador de seção
  correspondente na coluna A, conforme os seis marcadores da ADR-002 C4.
- Cabeçalho contendo VALOR RATEADO (exigido por `detectar_tipo`).
- Colunas por linha: A marcador, B tipo (INTEGRAL ou PARCIAL), Protocolo,
  Motivo, Placa, Data de comunicação (dd/mm/aaaa), Valor Rateado.
- Eventos agrupados por marcador, ordenados por data de comunicação (FIFO).
- Não exportar linha sem protocolo ou com valor menor ou igual a zero.

## 6. Modelo de dados

Sem tabela nova de domínio. Registrar cada exportação em
`exportacoes` (id, associacao_id, competencia, tipo BASE ou RATEIO, arquivo,
hash, criado_por, criado_em) para trilha de auditoria. RLS por
`auth.jwt() ->> 'associacao_id'` (ADR-002 C2).

## 7. API

- POST `/api/export/competencia` com `{ competencia: "AAAA-MM" }`, gera os dois
  arquivos e retorna os links de download e o resultado de `detectar_tipo`.
- GET `/api/export/{id}` baixa o arquivo gerado.

## 8. UI

Tela de Exportação: seleção de competência, botão Exportar, e o resultado da
validação de tipo por arquivo (verde ou vermelho), com link de download.

## 9. Observabilidade

Registrar competência, contagens por segmento, número de eventos por marcador e
o resultado de `detectar_tipo` no log de cada exportação.

## 10. Segurança e LGPD

Arquivos contêm placa e protocolo. Acesso restrito à associação dona (RLS) e
trilha de quem exportou. Sem dado pessoal além do necessário ao rateio.

## 11. Testes

Cobertos pelo harness da SPEC-008. Teste unitário do escritor da BASE garante
que `detectar_tipo` e `ler_base` aceitam a saída; do RATEIO, que `detectar_tipo`
reconhece e as somas por marcador batem.

## 12. Rollout

Entra após SPEC-005 e SPEC-006 estarem implementadas. A primeira tarefa é
extrair o layout célula a célula de `ingestao_partes` e dos arquivos de exemplo
em `Remonta/` e `simulacoes/`.

## 13. Questões em aberto

- Arquivo PRODUTOS não é gerado no MVP (opcional, ADR e MVP-SCOPE). O harness
  roda só com BASE e RATEIO.
