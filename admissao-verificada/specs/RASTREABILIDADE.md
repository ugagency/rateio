# RASTREABILIDADE — Admissao Verificada (MVP)

Status: revisao de QA (segunda rodada, pos-correcoes). Data: 2026-05-29.
Fonte dos requisitos: specs/MVP-SCOPE.md (secoes 3 e 4).
Specs analisadas: SPEC-000 a SPEC-008; ADR-001 e ADR-002.

> Matriz que mapeia cada requisito funcional (RF) e nao funcional (RNF) do
> MVP-SCOPE para a spec ou specs que o cobrem. A ultima secao lista os
> requisitos sem cobertura plena e o motivo.

---

## 1. Requisitos funcionais

| Requisito | Descricao resumida | Spec(s) que cobrem | Evidencia | Cobertura |
|---|---|---|---|---|
| RF-AUTH-01 | Login por e-mail e senha | SPEC-001 | secao 2, CA-001-1, CA-001-2; API 5.2 | Total |
| RF-AUTH-02 | Vincular todo registro a uma associacao | SPEC-001 | secoes 4.3, 4.4; CA-001-5, CA-001-6 | Total |
| RF-ASSOC-01 | Cadastrar associado com nome e CPF | SPEC-002 | secao 4.1, AC-001; API 5.1 | Total |
| RF-ASSOC-02 | Validar CPF pelo algoritmo oficial | SPEC-002 | AC-002, AC-003; secao 5.5 | Total |
| RF-ASSOC-03 | Impedir CPF duplicado na mesma associacao | SPEC-002 | AC-004, AC-005; constraint unique 4.1 | Total |
| RF-VEIC-01 | Cadastrar veiculo (placa, segmento, FIPE, cobertura) | SPEC-003 | secao 4.1, AC-001; API 5.1 | Total |
| RF-VEIC-02 | Validar placa (antigo e Mercosul) | SPEC-003 | AC-002, AC-003, AC-004; secao 5.7 | Total |
| RF-VEIC-03 | Classificar segmento LEVES, MOTOS, PESADOS | SPEC-003 | AC-005; check em segmento 4.1; ADR-002 C4 | Total |
| RF-VEIC-04 | Calcular cota pela faixa de FIPE (regra do motor) | SPEC-003 (ancorada no motor via ADR-002 C5) | AC-007, AC-008; secao 4.2, 5.6; seed de referencia espelha cotas_por_fipe de rules.py | Total |
| RF-VIST-01 | Scripts de vistoria por tipo, quantidade e ordem | SPEC-004 | CA-004-1; tabelas 4.1, 4.2 | Total |
| RF-VIST-02 | Captura somente ao vivo, bloquear galeria | SPEC-004 (limite do MVP em ADR-002 C8) | CA-004-4; API 5.5; secao 6.4; secao 8.1 | Total no alcance do MVP (ver nota A) |
| RF-VIST-03 | Carimbar foto com data, hora e geolocalizacao | SPEC-004 | CA-004-5, CA-004-6; tabela 4.4 | Total |
| RF-VIST-04 | Fluxo sequencial completo, finalizar so quando inteiro | SPEC-004 | CA-004-7, CA-004-10 | Total |
| RF-VIST-05 | Registrar inicio, cada captura e finalizacao | SPEC-004 | CA-004-9; tabela 4.5 timeline | Total |
| RF-VIST-06 | Vincular vistoria finalizada ao veiculo, habilitar admissao | SPEC-004 (status `ativo` per ADR-002 C1) | CA-004-10, CA-004-12; API 5.7 | Total |
| RF-SIT-01 | Registrar situacao do boleto por veiculo e competencia | SPEC-005 | secao 4.1, AC-001; API 5.1 | Total |
| RF-SIT-02 | Consolidar cotas por segmento e situacao | SPEC-005 | AC-008; secao 4.4, API 5.2 | Total |
| RF-EVT-01 | Cadastrar evento (marcador, tipo, protocolo, placa, data, valor) | SPEC-006 | secao 4.1, AC-001; API 5.1 | Total |
| RF-EVT-02 | Rejeitar evento sem protocolo ou valor menor ou igual a zero | SPEC-006 | AC-002, AC-003, AC-004 | Total |
| RF-EXP-01 | Exportar BASE da competencia no layout do motor | SPEC-007 (contrato em SPEC-000) | SPEC-007 secao 4, AC-1, AC-3; SPEC-000 secao 2 | Total |
| RF-EXP-02 | Exportar RATEIO da competencia no layout do motor | SPEC-007 (contrato em SPEC-000) | SPEC-007 secao 5, AC-2, AC-3; SPEC-000 secao 3 | Total |
| RF-EXP-03 | Arquivos passam em detectar_tipo com tipo correto | SPEC-007 + SPEC-008 | SPEC-007 AC-1, AC-2; SPEC-008 AC-1, AC-3 | Total |

## 2. Requisitos nao funcionais

| Requisito | Descricao resumida | Spec(s) que cobrem | Evidencia | Cobertura |
|---|---|---|---|---|
| RNF-01 | Isolamento por associacao (RLS) em toda tabela | SPEC-001 (padrao); SPEC-002 a SPEC-007 (aplicacao) | ADR-002 C2 fixa a forma unica (claim JWT); RLS em cada spec | Total |
| RNF-02 | Trilha de auditoria imutavel nas operacoes de admissao | SPEC-002, 003, 004, 005, 006 | tabelas *_audit e timeline_vistoria; SPEC-007 registra exportacoes | Total |
| RNF-03 | Fotos e metadados de vistoria imutaveis apos finalizacao | SPEC-004 | CA-004-11; secao 8.1 | Total |
| RNF-04 | HTTPS e tratamento LGPD | SPEC-001 a SPEC-007 | secao Seguranca/LGPD de cada spec | Total |

## 3. Requisitos sem cobertura plena (lacunas de rastreabilidade)

Nesta segunda rodada nao restam requisitos do MVP-SCOPE sem cobertura de spec.
As lacunas da rodada anterior foram fechadas:

- RF-EXP-01 e RF-EXP-02: passaram a ser cobertos pela SPEC-007 (exportador),
  que define a geracao celula a celula da BASE espelhando `ler_base` e a
  montagem do RATEIO com os seis marcadores de secao. O contrato de aceite por
  invariante esta na SPEC-008 (harness), que roda o motor aprovado e confere
  `invariante_ok` (ADR-002 C6).
- RF-VEIC-04: a SPEC-003 ancora o calculo no motor via ADR-002 C5; o seed de
  `faixas_cota` reproduz `cotas_por_fipe` de `rules.py` (cota base 1,0 ate
  10.000; acrescimo de 0,5 por faixa de 10.000; cota especial 20,0 acima de
  450.000). O default e identico ao motor, mantendo a tabela parametrizavel.
- RF-VIST-06: a SPEC-004 transiciona o veiculo para `ativo` na finalizacao,
  conforme o enum unico da ADR-002 C1. O valor `admitido` foi eliminado.

Notas de alcance e limite:

- Nota A (RF-VIST-02): a barreira contra foto de galeria e a captura ao vivo
  pela camera do PWA, sem campo de upload de arquivo. A verificacao server-side
  por metadados (EXIF) fica para fase posterior. Limite do MVP aceito e
  registrado na ADR-002 C8; nao e lacuna de rastreabilidade.

## 4. Cadeia do dado da admissao ate os arquivos

Cadeia esperada e onde cada elo esta especificado:

| Elo | Origem | Destino | Spec | Situacao |
|---|---|---|---|---|
| associado | cadastro | tabela `associados` | SPEC-002 | OK |
| veiculo + cota + segmento | cadastro | tabela `veiculos` | SPEC-003 | OK (cota ancorada no motor, ADR-002 C5) |
| vistoria finalizada | esteira | `veiculos.status = ativo` | SPEC-004 | OK (status unico, ADR-002 C1) |
| veiculo apto a BASE | filtro | consolidacao | SPEC-005 | OK (filtro por `status = ativo`) |
| situacao do boleto | registro | coluna BAIXADO por segmento | SPEC-005 | OK (CANCELADO informativo, ADR-002 C7) |
| evento do mes | registro | linha do RATEIO | SPEC-006 | OK (envolvimento e do evento, ADR-002 C4) |
| consolidacao + eventos | exportador | BASE.xlsx e RATEIO.xlsx | SPEC-007 | OK (espelha `ingestao_partes`) |
| BASE.xlsx e RATEIO.xlsx | harness | motor aprovado, invariante zero | SPEC-008 | OK (detectar_tipo, validar_slot, invariante_ok) |

A cadeia esta coerente de ponta a ponta. O elo final de serializacao, antes
ausente, esta especificado pela SPEC-007 (geracao dos arquivos no layout do
leitor) e pela SPEC-008 (prova de aceite por reconciliacao). O mapeamento de
rotulos plural do app para o rotulo de cada arquivo esta fixado na ADR-002 C4
e referenciado por SPEC-000 e SPEC-007. Detalhes do parecer na REVISAO-SDD.
