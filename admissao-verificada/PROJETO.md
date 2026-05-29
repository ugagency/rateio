# Projeto: Admissão Verificada (MVP)

> Plataforma de admissão de associados que gera a base capaz de produzir os
> arquivos que o motor de rateio aprovado já consome hoje. O App Visto entra
> como estágio de admissão verificada. Spec Driven Development.

## 1. Visão

Hoje o motor de rateio (ELLO mais AutoTruck) é o fim de uma cadeia, mas a
entrada de dados é manual. Este projeto constrói o começo dessa cadeia: a
admissão do associado. O associado entra por uma esteira verificada (cadastro
mais vistoria antifraude), e ao final existe uma base de dados capaz de
exportar, mês a mês, os arquivos BASE e RATEIO no layout que o motor aprovado
já lê.

A vistoria, inspirada no App Visto, não é a porta de entrada e sim o portão de
admissão: o momento em que um interessado vira associado verificado, com
trilha imutável. É o mesmo DNA auditável do rateio, agora na entrada.

## 2. Objetivo do MVP (enxuto)

Funcionalidades e validações mínimas para gerar uma base que produza os
arquivos do rateio. O critério de sucesso é binário e verificável:

> Admitir N associados pela esteira, lançar eventos do mês, exportar
> BASE.xlsx e RATEIO.xlsx, e o motor aprovado rodar sobre esses arquivos com
> `detectar_tipo` correto e invariante de fechamento igual a zero.

O motor aprovado NÃO é alterado. A integração do MVP com ele é por arquivo: o
MVP gera os xlsx; o motor os ingere por `FonteFechamentoXlsx` /
`ingestao_partes`. Nenhuma linha do engine muda.

## 3. Escopo

Detalhado em `specs/MVP-SCOPE.md`. Resumo:

Dentro: cadastro de associado, cadastro de veículo com segmento e cota,
admissão verificada (vistoria App Visto), situação de boleto por competência,
captura mínima de eventos, exportação BASE e RATEIO, harness de reconciliação
contra o motor.

Fora: funil de lead e cotação, integração com SGA ou qualquer sistema externo,
gateway de pagamento real, gestão completa de sinistros, OCR e IA, app nativo
iOS/Android, o motor de rateio genérico do protótipo anterior (descartado).

## 4. Alvo de saída e oráculo de aceite

O contrato de exportação é a peça central, especificado em
`specs/SPEC-000-contrato-exportacao.md`. Ele foi derivado do leitor real do
motor (`backend/app/autotruck/ingestao_partes.py`):

- BASE: três segmentos lado a lado (PESADO, MOTO, LEVE), cabeçalho
  DESCRIÇÃO / ABERTO / BAIXADO / CANCELADO / TOTAL. O denominador do rateio é a
  coluna BAIXADO (cotas pagas) por segmento.
- RATEIO: marcador de seção na coluna A (segmento mais envolvimento, por
  exemplo LEVES ASSOCIADOS, PESADOS TERCEIROS), tipo INTEGRAL ou PARCIAL,
  Protocolo, Motivo, Placa, Data de comunicação (ordem FIFO), Valor Rateado.

O motor e seus utilitários (`detectar_tipo`, `validar_slot`,
`tools/reconciliar.py`, endpoint `/inspecionar-arquivo`) são, ao mesmo tempo,
o contrato e o oráculo de teste. O MVP está correto quando os arquivos que ele
gera passam por esses validadores.

## 5. Arquitetura (resumo, ver ADR-001)

- Frontend e backend: Next.js 15 mais Supabase mais TypeScript, reaproveitando
  a fundação SDD já existente (autenticação, multi-tenant por RLS, esqueleto de
  associados e veículos), descartado o motor de rateio genérico.
- Vistoria: PWA com captura ao vivo pela câmera (sem app nativo no MVP),
  carimbo de data, hora e geolocalização por foto.
- Rateio: permanece em Python (motor aprovado). Integração por exportação de
  arquivo xlsx. Um conector por API fica para fase posterior.
- Persistência: Postgres do Supabase, com trilha de auditoria nas operações de
  admissão.

## 6. A squad (papéis contratados)

Squad enxuta, orientada a SDD. Cada papel é dono de uma ou mais specs.

| Papel | Responsabilidade | Specs |
|---|---|---|
| Product Owner / Spec Lead | Escopo, requisitos, critérios de aceite, priorização | MVP-SCOPE |
| Tech Lead / Arquiteto | ADRs, modelo de dados, integração com o motor, contrato de exportação | ADR-001, SPEC-000 |
| Engenheiro Backend | Schema Supabase, serviços, geração dos xlsx | SPEC-002, SPEC-003, SPEC-005, SPEC-006 |
| Engenheiro Frontend | Telas de admissão, painel, exportação | SPEC-001, telas das specs |
| Engenheiro de Vistoria | Esteira de captura antifraude (App Visto) | SPEC-004 |
| QA | Plano de testes, fixtures, aceite por reconciliação | seção Testes de cada spec |
| Compliance LC 213 | Trilha de auditoria, registro de admissão como subscrição, aderência SUSEP | revisão transversal |

## 7. Backlog de specs (SDD)

Fundação escrita pelo Tech Lead e pelo Spec Lead:
- MVP-SCOPE: escopo, requisitos e aceite.
- ADR-001: arquitetura e decisões.
- SPEC-000: contrato de exportação BASE e RATEIO mais harness de reconciliação.

Specs de módulo, escritas pela squad:
- SPEC-001: Autenticação e contexto da associação (mínimo).
- SPEC-002: Cadastro de Associado.
- SPEC-003: Cadastro de Veículo e Cota (segmento, FIPE, cobertura).
- SPEC-004: Admissão Verificada (App Visto) — esteira de vistoria antifraude.
- SPEC-005: Situação de Boleto por Competência (denominador da BASE).
- SPEC-006: Eventos do Mês (numerador do RATEIO).

## 8. Marcos

- M0: Fundação SDD aprovada (este plano, MVP-SCOPE, ADR-001, SPEC-000).
- M1: Modelo de dados e contrato de exportação implementados, com harness de
  reconciliação verde contra um caso conhecido.
- M2: Esteira de admissão (cadastro mais vistoria) gerando registros reais.
- M3: Situação de boleto e eventos mínimos capturados.
- M4: Fim a fim — admitir associados, lançar eventos, exportar, motor roda com
  invariante zero.

## 9. Processo SDD

Especificar antes de codar. Cada spec segue o template padrão (Contexto,
Requisitos, Critérios Given/When/Then, Modelo de Dados, API, UI,
Observabilidade, Segurança, Testes, Rollout, Questões em aberto). Specs são
revisadas e aprovadas antes da implementação. O aceite de cada entrega se
ancora no oráculo do motor aprovado (reconciliação e invariante zero).
