# REVISAO-SDD — Admissao Verificada (MVP)

Status: revisao de QA (segunda rodada, pos-correcoes). Data: 2026-05-29.
Escopo: consistencia e rastreabilidade entre PROJETO, MVP-SCOPE, ADR-001,
ADR-002, SPEC-000 e SPEC-001 a SPEC-008.
Criterio mestre: gerar BASE e RATEIO no layout do motor aprovado e o motor
rodar com detectar_tipo correto e invariante de fechamento igual a zero.

> Relatorio de revisao das specs sob a otica de QA. Confirma a resolucao dos
> bloqueios da rodada anterior, aponta o que ainda resta e da um parecer go ou
> no-go por spec e um parecer geral do MVP.

---

## 1. Status dos bloqueios da revisao anterior

A primeira rodada apontou cinco inconsistencias bloqueantes (I-01 a I-05),
uma observacao (I-06) e seis lacunas (L-01 a L-06). A ADR-002 foi criada como
fonte unica das convencoes canonicas e as SPEC-007 e SPEC-008 foram escritas
para o exportador e o harness. O resultado por item:

### I-01. Status do veiculo apos a vistoria. RESOLVIDO.

A ADR-002 C1 fixa o enum unico `pendente_vistoria`, `ativo`, `inativo`. O valor
`admitido` foi eliminado. A SPEC-004 (CA-004-10 e API 5.7) transiciona o veiculo
para `ativo` na finalizacao, numa transacao atomica. A SPEC-005 (secao 4.4 e
AC-013) filtra a consolidacao por `v.status = 'ativo'`. A cadeia ate a coluna
BAIXADO esta integra: o veiculo finalizado pela vistoria entra no denominador.

### I-02. Forma de policy RLS. RESOLVIDO.

A ADR-002 C2 fixa a forma unica: claim `associacao_id` no JWT, via
`auth.jwt() ->> 'associacao_id'`, proibida a subquery em `operadores`. As
SPEC-002, 003, 004, 005, 006 e 007 reproduzem essa forma. A divergencia das
specs de modulo que usavam subquery foi eliminada.

### I-03. Formato de competencia. RESOLVIDO.

A ADR-002 C3 fixa armazenamento unico em coluna `date` no primeiro dia do mes,
entrada de API em `AAAA-MM` e exibicao em `MM/AAAA`. A SPEC-005 (secao 4.1,
constraint de primeiro dia) e a SPEC-006 (secao 4.1) seguem esse tipo. BASE e
RATEIO de uma exportacao usam a mesma `competencia` (SPEC-007 AC-3).

### I-04. Mapeamento de rotulos de segmento. RESOLVIDO.

A ADR-002 C4 fixa o segmento plural no app (LEVES, MOTOS, PESADOS), o rotulo
singular na BASE (LEVE, MOTO, PESADO) e os seis marcadores do RATEIO. A
SPEC-000 (secao 3, mapeamento canonico) e a SPEC-007 (secoes 4 e 5) referenciam
esse mapeamento. A origem da classificacao espelha `segmento_por_tipo` de
`rules.py`.

### I-05. Cobertura de terceiros nao determina o envolvimento. RESOLVIDO.

O texto da SPEC-003 (secao 1) foi corrigido: a cobertura de terceiros define o
preco do produto Danos a Terceiros (nenhuma 0, 50k 20, 100k 30) e NAO define o
envolvimento do RATEIO. O marcador ASSOCIADOS ou TERCEIROS vem do evento
(SPEC-006, ADR-002 C4). As duas specs agora casam.

### I-06. PRODUTOS e perfil ELLO. CONFIRMADO COMO FORA DO MVP.

O MVP-SCOPE (secao 6) e a SPEC-007 (secao 13) registram que o exportador nao
gera PRODUTOS e que o harness roda apenas com BASE e RATEIO. O perfil ELLO fica
para fase posterior. Decisao explicita; sem pendencia.

### L-01. Faixas de cota de referencia. RESOLVIDO.

A ADR-002 C5 fixa o seed que reproduz `cotas_por_fipe` de `rules.py`. A SPEC-003
(secao 4.2 e 5.6) determina que o seed inicial DEVE reproduzir esses valores,
mantendo a tabela parametrizavel. A rastreabilidade ao oraculo esta fechada.

### L-02. Antifraude de galeria sem barreira server-side. ENDERECADO COMO LIMITE.

A ADR-002 C8 registra a decisao aceita: no MVP a barreira e a captura ao vivo
pela camera do PWA, sem campo de upload. A verificacao server-side por
metadados fica para fase posterior. A SPEC-004 (CA-004-4, secao 8.1, questao em
aberto 1 marcada como resolvida) reflete o limite. Nao bloqueia o criterio de
aceite do MVP.

### L-03. Spec do exportador da BASE. RESOLVIDO.

A SPEC-007 (secao 4) define a geracao da BASE espelhando `ler_base`: rotulos de
segmento no singular na linha 1, sub-bloco Cota por Situacao com BAIXADO,
ABERTO, CANCELADO e TOTAL, e sub-bloco de boletos para conferencia. As
contagens vem da consolidacao da SPEC-005; o exportador nao recalcula situacao.

### L-04. Spec do exportador do RATEIO e orquestracao. RESOLVIDO.

A SPEC-007 (secao 5) define a montagem do RATEIO: uma linha por evento sob o
marcador de secao, cabecalho com VALOR RATEADO, ordem FIFO por data de
comunicacao. A orquestracao por competencia (gera os dois arquivos, chama
`detectar_tipo`) esta na SPEC-007 (API 5.7) e a prova de invariante na SPEC-008.

### L-05. Definicao do invariante de fechamento. RESOLVIDO.

A ADR-002 C6 descreve o invariante concreto de `engine.py`: por segmento
variavel (LEVES e MOTOS), soma da diferenca entre alvo e alocado; `invariante_ok`
e verdadeiro quando o valor absoluto e menor que 0,01. A SPEC-008 (AC-2) le esse
campo do resultado do motor. O QA tem agora a definicao para a fixture.

### L-06. Tratamento da situacao CANCELADO na BASE. RESOLVIDO.

A ADR-002 C7 fixa que o denominador e a coluna BAIXADO; ABERTO e CANCELADO sao
informativos e CANCELADO nao entra no denominador nem no invariante. A SPEC-005
(AC-013, secao 4.4) e a SPEC-007 (secao 4) seguem essa regra; a consolidacao
ainda registra canceladas apenas para conferencia.

---

## 2. Pendencias restantes

Nenhuma pendencia bloqueante restou. As questoes abaixo sao de produto ou de
detalhe de implementacao, nao impedem a implementacao nem o aceite por
reconciliacao, e ja estao registradas nas secoes de questoes em aberto das
specs:

- Forma de invocar o motor a partir do ambiente do app (subprocesso, servico
  local ou suite do backend): a definir na implementacao da SPEC-008, sem
  alterar o motor (SPEC-008 secao 9). E decisao de engenharia, nao de contrato.
- Geolocalizacao obrigatoria em ambientes sem sinal GPS (SPEC-004 questao 2):
  decidir se a captura sem coordenadas e permitida com aviso. Nao afeta a BASE
  nem o RATEIO.
- QR Code embutido por watermark versus geracao dinamica (SPEC-004 questao 3):
  detalhe de implementacao da vistoria.
- Compatibilidade tipo de script versus segmento de veiculo (SPEC-004 questao
  6): fixa ou parametrizavel; nao afeta a exportacao.
- Competencia retroativa apos exportacao e delecao de registros de situacao
  (SPEC-005 questoes em aberto): politica de operacao; nao afeta o layout.
- Protocolo unico por competencia versus multiplas linhas com mesmo protocolo
  (SPEC-006 questao 1): caso de ajuste parcial; resolvel por protocolos
  distintos no MVP.
- Recomendacao de QA: validar, na primeira tarefa de implementacao da SPEC-007,
  o layout celula a celula contra `ingestao_partes.py` e os arquivos de exemplo
  em `Remonta/` e `simulacoes/`, como a propria spec instrui. Esse e o ponto
  onde uma divergencia de posicao ainda poderia surgir; e tarefa de
  implementacao guiada por spec, nao lacuna de especificacao.

---

## 3. Avaliacao da cadeia do dado (verificacao solicitada)

Caminho admissao ate BASE e ate RATEIO, ponta a ponta:

- Associado (SPEC-002): cadastro com CPF validado e unico por associacao. Elo
  inicial integro.
- Veiculo e cota (SPEC-003): segmento canonico plural, cota derivada da faixa
  de FIPE com seed ancorado no motor (ADR-002 C5). Nasce `pendente_vistoria`.
- Vistoria (SPEC-004): a finalizacao leva o veiculo a `ativo` (ADR-002 C1),
  habilitando-o a constar na BASE. Sem o conflito de status da rodada anterior.
- Situacao de boleto (SPEC-005): define o denominador. So veiculos `ativo` com
  situacao `baixado` entram na coluna BAIXADO; ABERTO e CANCELADO sao
  informativos (ADR-002 C7). A consolidacao retorna os tres segmentos sempre.
- Eventos (SPEC-006): numerador do RATEIO; eventos validos ordenados FIFO por
  data de comunicacao sob o marcador de secao do evento (ADR-002 C4).
- Exportador (SPEC-007): serializa a consolidacao na BASE e os eventos no
  RATEIO, no layout do leitor, mesma competencia para os dois arquivos.
- Harness (SPEC-008): chama `detectar_tipo`, roda o motor e confere
  `invariante_ok` (ADR-002 C6); roda na suite e bloqueia o build se a paridade
  quebrar.

Modelo de dados: coerente e suficiente. Nenhuma entidade de negocio falta para
gerar os arquivos. O tratamento de LEVES, MOTOS e PESADOS e consistente: plural
no app, mapeado para o rotulo de cada arquivo pela ADR-002 C4, com os tres
segmentos sempre presentes na consolidacao e os seis marcadores do RATEIO
cobrindo segmento e envolvimento.

Fronteira de serializacao: antes interrompida, agora fechada por SPEC-007 e
SPEC-008. A cadeia e fechavel: existe spec para cada elo, da entidade ao
arquivo, e o aceite por invariante tem oraculo definido.

---

## 4. Parecer por spec

| Spec | Parecer | Condicao |
|---|---|---|
| SPEC-000 | Go | Contrato derivado do leitor; mapeamento de rotulos, CANCELADO e invariante referenciados na ADR-002. Oraculo das demais, fechado. |
| SPEC-001 | Go | RLS por claim do JWT fixado na ADR-002 C2 e seguido pelas specs de modulo. |
| SPEC-002 | Go | Cadastro de associado completo; RLS alinhada ao padrao. |
| SPEC-003 | Go | Status unico (C1), cota ancorada no motor (C5), texto de envolvimento corrigido (I-05) e RLS alinhada (C2). |
| SPEC-004 | Go | Esteira de vistoria; status final `ativo` alinhado (C1); limite de galeria registrado (C8). |
| SPEC-005 | Go | Filtro por `status = ativo` (C1), competencia canonica (C3), CANCELADO informativo (C7). |
| SPEC-006 | Go | Registro de eventos; envolvimento do evento (C4); competencia canonica (C3); exportador coberto pela SPEC-007. |
| SPEC-007 | Go | Exportador da BASE e do RATEIO espelhando o leitor; fecha RF-EXP-01 a RF-EXP-03. Ressalva de execucao: validar layout celula a celula contra `ingestao_partes` na implementacao. |
| SPEC-008 | Go | Harness de reconciliacao com fixture deterministica e invariante concreto (C6); roda na suite. |

Parecer geral: go para o MVP. Os tres pontos que impediam a reconciliacao verde
na rodada anterior foram resolvidos: o conflito de status que zerava a BASE
(I-01), a ausencia das specs de exportacao e do harness (L-03, L-04, L-05) e a
falta do mapeamento de rotulos e do seed de cota de referencia (I-04, L-01). A
fundacao canonica (ADR-002) unificou as convencoes divergentes. O conjunto esta
apto a implementacao e ao teste de ponta a ponta. A unica ressalva e de
execucao, nao de especificacao: a fidelidade celula a celula da SPEC-007 ao
leitor real deve ser verificada na primeira tarefa de implementacao, e o harness
da SPEC-008 e justamente o guardiao automatico dessa fidelidade.

## 5. Acoes restantes (ordem sugerida)

1. Implementar a SPEC-007 extraindo o layout celula a celula de
   `ingestao_partes.py` e dos exemplos em `Remonta/` e `simulacoes/`.
2. Implementar a SPEC-008 com a fixture deterministica e integra-la a suite;
   confirmar `invariante_ok` verdadeiro no caso dourado.
3. Resolver as questoes de produto pendentes (secao 2) conforme surgirem na
   implementacao, sem impacto no contrato dos arquivos.
