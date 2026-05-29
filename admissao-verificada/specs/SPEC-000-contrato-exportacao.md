# SPEC-000 — Contrato de Exportação (BASE e RATEIO) e Harness de Reconciliação

> Peça central do MVP. Define o formato exato dos arquivos que o app gera para
> o motor aprovado, e como provar que estão corretos. Derivado do leitor real
> `backend/app/autotruck/ingestao_partes.py`. Esta spec é o oráculo das demais.

## 1. Contexto

O motor de rateio aprovado ingere a base do mês por arquivos xlsx separados,
lidos por `ingestao_partes` (BASE, RATEIO e PRODUTOS opcional). O MVP deve
gerar BASE e RATEIO nesse layout. O motor não muda; o app se adapta a ele.

A detecção de tipo (`detectar_tipo`) e a validação de slot (`validar_slot`)
inspecionam a assinatura do arquivo. O export só é aceito se essas funções
reconhecerem o tipo correto.

As convenções canônicas que esta spec assume (status do veículo, RLS, formato
de competência, rótulos de segmento, seed de cota, invariante e tratamento de
CANCELADO) estão fixadas na ADR-002 e valem para todas as specs.

## 2. Arquivo BASE

Conteúdo: cotas e boletos por situação, por segmento. O denominador do rateio
é a coluna BAIXADO (cotas pagas) por segmento.

Assinatura reconhecida pelo leitor (qualquer uma serve para `detectar_tipo`):
- Linha 1 com os rótulos de segmento PESADO, MOTO e LEVE dispostos lado a lado
  (pelo menos dois deles), ou
- Cabeçalho com pelo menos quatro de DESCRIÇÃO, ABERTO, BAIXADO, CANCELADO,
  TOTAL nas linhas 3 a 5.

Informação que o leitor extrai, por segmento (LEVES, MOTOS, PESADOS):
- cotas baixadas (denominador)
- cotas abertas (informativo de inadimplência)
- boletos baixados e abertos (conferência)
- valor recebido e inadimplência (conferência)

Critério: a coluna BAIXADO de cotas por situação deve refletir as cotas pagas
da competência, somadas por segmento. Valores monetários aceitam vírgula
decimal e prefixo de reais; o leitor normaliza.

## 3. Arquivo RATEIO

Conteúdo: um evento por linha, agrupados por marcador de seção na coluna A.

Assinatura reconhecida (ambas necessárias para `detectar_tipo`):
- Marcador de seção na coluna A nas primeiras linhas, combinando segmento e
  envolvimento, por exemplo LEVES ASSOCIADOS, MOTOS ASSOCIADOS,
  PESADOS TERCEIROS. O marcador contém ASSOCIADOS ou TERCEIROS mais um de
  PESADOS, MOTOS, LEVES.
- Cabeçalho contendo VALOR RATEADO.

Colunas por linha de evento:
- A: marcador de seção (define segmento e envolvimento)
- B: tipo de indenização, INTEGRAL ou PARCIAL
- Protocolo: identificador do sinistro (obrigatório)
- Motivo: descrição (desejável)
- Placa: identificação do veículo (obrigatório)
- Data de comunicação: dd/mm/aaaa, define a ordem FIFO (obrigatório)
- Valor Rateado: valor do evento em reais, maior que zero (obrigatório)

Regras: ASSOCIADOS indica custo do grupo (entra na conta); TERCEIROS indica
recuperação (vai ao pote de Danos a Terceiros, não abate a cota). Linha sem
protocolo ou com valor menor ou igual a zero é ignorada pelo motor, então o
app não deve exportá-la.

Os seis marcadores possíveis (segmento mais envolvimento), conforme ADR-002 C4:
LEVES ASSOCIADOS, LEVES TERCEIROS, MOTOS ASSOCIADOS, MOTOS TERCEIROS,
PESADOS ASSOCIADOS, PESADOS TERCEIROS.

### Mapeamento canônico de rótulos (ADR-002 C4)

O app guarda o segmento no plural (LEVES, MOTOS, PESADOS). Na BASE, o rótulo de
coluna é o singular correspondente (LEVE, MOTO, PESADO). No RATEIO, o marcador
de seção combina o segmento plural com o envolvimento (ASSOCIADOS ou TERCEIROS).
O envolvimento vem do evento (SPEC-006), não da cobertura de terceiros do
veículo.

### Situação CANCELADO (ADR-002 C7)

O denominador é a coluna BAIXADO. ABERTO e CANCELADO são informativos; CANCELADO
não entra no denominador nem no invariante. A consolidação por segmento registra
cotas canceladas apenas para conferência.

## 4. Mapeamento da base do app para os arquivos

BASE
- Para cada veículo ativo na competência, com vistoria finalizada, agrupar por
  segmento. A situação de boleto da competência classifica a cota em baixada,
  aberta ou cancelada (ver SPEC-005).
- Somar cotas e boletos por situação e por segmento; escrever no layout da
  seção 2.

RATEIO
- Para cada evento da competência (ver SPEC-006), escrever uma linha sob o
  marcador correspondente ao segmento e envolvimento, com tipo, protocolo,
  placa, data e valor rateado.

## 5. Critérios de aceite (Given/When/Then)

- AC-1: Given veículos ativos com vistoria finalizada e situação de boleto na
  competência, When o app exporta a BASE, Then `detectar_tipo` retorna BASE e
  as cotas baixadas por segmento conferem com a soma da base do app.
- AC-2: Given eventos válidos na competência, When o app exporta o RATEIO,
  Then `detectar_tipo` retorna RATEIO e a soma de Valor Rateado por seção
  confere com a base do app.
- AC-3: Given BASE e RATEIO exportados, When o motor aprovado roda sobre eles
  (`tools/reconciliar.py` ou o serviço de fechamento), Then processa sem erro e
  retorna `invariante_ok` verdadeiro. Invariante concreto (ADR-002 C6,
  `engine.py`): por segmento variável (LEVES e MOTOS), soma da diferença entre
  alvo e alocado, com valor absoluto menor que 0,01.
- AC-4: Given um arquivo exportado no slot errado, When passa por
  `validar_slot`, Then a validação acusa o erro.

## 6. Harness de reconciliação

Um utilitário do MVP deve: gerar BASE e RATEIO a partir de uma competência,
chamar `detectar_tipo` em cada um, rodar o motor aprovado sobre os arquivos e
reportar o invariante. Esse harness é o teste de aceite de ponta a ponta e
deve rodar na suíte automatizada.

## 7. Observações

- A primeira tarefa de implementação é extrair do leitor
  `ingestao_partes` (e dos arquivos de exemplo em `Remonta/` e
  `simulacoes/`) o layout célula a célula, para o export bater exatamente. Não
  presumir posições; espelhar o leitor.
- O motor aprovado e seus validadores são a fonte de verdade do formato.
