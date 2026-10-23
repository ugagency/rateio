# Relatório de aderência: dados reais ELLO x Motor de Rateio

Arquivo analisado: `ELLO/Relatório processos a ratear - 28_09.xlsx` (aba única `Planilha1`)
Data da análise: 30/09/2026
Competência presumida: 09/2026 (a confirmar)

## 1. Resumo

O arquivo recebido traz os processos (eventos) a ratear, mas ainda não permite rodar o rateio de ponta a ponta. Três pontos bloqueiam a execução e um ponto exige decisão de modelo antes de qualquer código:

1. **Duplicidade na planilha.** As linhas 403 a 502 são cópia exata das linhas 303 a 402 (100 protocolos colados duas vezes, R$ 1.063.907,34).
2. **Total do cabeçalho não confere.** O cabeçalho declara 462 registros e R$ 4.746.316,20. A planilha soma R$ 4.867.973,80 em 499 linhas, ou R$ 3.804.066,46 em 399 protocolos únicos.
3. **Falta a base de veículos.** O motor calcula o alvo do mês a partir das cotas por categoria (veículos elegíveis). O arquivo traz só eventos.
4. **Modelo de cálculo.** O arquivo está organizado como "total a ser rateado", o que sugere rateio orientado por custo. O motor ELLO atual é orientado por alvo (valor fixo por cota). Precisa confirmar como a ELLO calcula hoje.

## 2. Estrutura do arquivo

| Coluna | Conteúdo | Uso proposto no motor |
|---|---|---|
| PROTOCOLO | número do processo (prefixo = ano, 2023 a 2026) | `ID_Evento` |
| SITUACÃO | 16 situações distintas | filtro de elegibilidade |
| TIPO EVENTO | "ASSOCIADO" em 498 linhas, vazio em 1 | sem uso |
| PLACA | placa do veículo sinistrado | rastreabilidade |
| TIPO VEÍCULO | categoria do veículo | categoria de risco |
| CUSTO DO EVENTO | custo total | `Valor_Total_Evento` |
| PARTICIPAÇÃO | participação do associado | sem uso direto (ver 5.5) |
| VALOR A RATEAR | valor que vai para o rateio | `Valor_Saldo_Pendente` |

Linhas 1 e 2 são cabeçalho descritivo; a tabela começa na linha 3. Não há fórmulas; os valores já vêm calculados.

## 3. Duplicidade e o total do cabeçalho

| Base | Registros | Valor a ratear (R$) |
|---|---:|---:|
| Planilha como veio | 499 | 4.867.973,80 |
| Cabeçalho declarado | 462 | 4.746.316,20 |
| Protocolos únicos | 399 | 3.804.066,46 |
| Bloco duplicado (linhas 403 a 502) | 100 | 1.063.907,34 |

O total declarado fica R$ 121.657,60 abaixo da base com duplicidade e R$ 942.249,74 acima da base deduplicada. Isso é compatível com o total do cabeçalho ter sido calculado sobre a base que ainda continha o bloco duplicado, com algumas situações retiradas. Um teste combinatório encontrou uma exclusão de 9 situações que resulta em exatamente 462 registros e R$ 4.746.313,49 (diferença de R$ 2,71), o que reforça essa leitura.

**Risco:** se o motor devolver cerca de R$ 3,80 milhões e a ELLO esperar R$ 4,75 milhões, a divergência vai parecer erro do motor. Esse número precisa ser confirmado com a ELLO antes de qualquer rodada.

## 4. Perfil dos protocolos únicos (399)

### 4.1 Por categoria de veículo

| TIPO VEÍCULO | Categoria no motor | Registros | Valor a ratear (R$) |
|---|---|---:|---:|
| MOTOCICLETA FIPE | MOTO_FIP | 348 | 3.528.507,39 |
| VENTURE I | VENTURE_1 | 32 | 174.967,89 |
| VENTURE II | VENTURE_2 | 13 | 68.238,47 |
| GRUPO ROUBO/FURTO | ROUBO_FURTO | 5 | 31.560,82 |
| AUTOMOVEL FUNCIONARIO | sem correspondência | 1 | 791,89 |

As quatro categorias principais batem com os quatro degraus do motor. Motocicleta FIPE concentra 93% do valor.

### 4.2 Por situação

| SITUACÃO | Registros | Valor a ratear (R$) |
|---|---:|---:|
| FINALIZADO | 349 | 3.506.045,01 |
| INDENIZAÇÃO NOTIFICADA | 10 | 129.588,46 |
| PARALISADO(DIR) | 3 | 61.331,60 |
| VEICULO ENTREGUE SEM PENDENCIA | 7 | 49.476,85 |
| PRE RATEIO | 2 | 14.961,55 |
| VEICULO PRONTO | 1 | 14.178,62 |
| FINALIZADO SEM RATEIO | 1 | 10.900,00 |
| PROC. JUDICIAL | 11 | 7.169,61 |
| PECAS EM RESTAURAÇÃO | 1 | 5.515,72 |
| AG MONTAGEM | 6 | 4.410,19 |
| REPARO PARALISADO | 1 | 3.861,06 |
| EM ANDAMENTO | 1 | 2.048,57 |
| INDENIZAÇÃO EM ANDAMENTO | 1 | -720,70 |
| INDENIZAÇÃO REALIZADA/ AG RATEIO | 1 | -800,00 |
| CANCELADO | 1 | -1.300,00 |
| SUBSTITUIÇÃO DE BEM | 3 | -2.600,08 |

A situação "INDENIZAçãO REALIZADA/ AG RATEIO" vem com grafia mista no arquivo; a ingestão precisa normalizar maiúsculas e acentos.

### 4.3 Por ano do protocolo

| Ano | Registros |
|---|---:|
| 2023 | 13 |
| 2024 | 30 |
| 2025 | 60 |
| 2026 | 296 |

## 5. Pontos de atenção por linha

1. **Valores negativos:** 16 protocolos, somando R$ -18.948,74. Quatro deles estão como FINALIZADO. Hoje o motor ignora eventos com saldo menor ou igual a zero. Se forem estornos ou recuperações, deveriam abater o total do mês em vez de serem ignorados.
2. **Situações que não parecem de rateio:** CANCELADO (1) e FINALIZADO SEM RATEIO (1, R$ 10.900,00).
3. **Processos em andamento:** PROC. JUDICIAL, AG MONTAGEM, EM ANDAMENTO, PECAS EM RESTAURAÇÃO e similares. Precisa definir se entram agora ou só quando finalizados.
4. **Linha 58** (protocolo 2025216002): TIPO EVENTO vazio. Os demais campos estão preenchidos.
5. **Participação:** em 46 protocolos o valor a ratear é menor que o custo, mas em nenhum deles a diferença é igual à participação. O motor deve usar VALOR A RATEAR como está, e a regra de cálculo dessa coluna fica registrada como pergunta.
6. **AUTOMOVEL FUNCIONARIO:** um protocolo (2024213545, R$ 791,89). No motor, funcionário não entra na base de cotas nem gera boleto; falta definir se o evento dele é rateado.

## 6. O que falta para rodar o rateio

| Insumo | Situação | Observação |
|---|---|---|
| Eventos | recebido, com ressalvas | depende das decisões da seção 8 |
| Base de veículos (cotas, categoria, status, forma de pagamento, funcionário) | não recebido | sem ela não há alvo nem boleto |
| Serviços fixos por veículo (taxa administrativa, assistência 24h, outros) | não recebido | necessário para o valor final do boleto |
| Data de ocorrência do evento | ausente | a ordem de alocação do motor é data, depois valor, depois identificador |

Sem data de ocorrência, o número do protocolo pode servir de aproximação cronológica (é sequencial e começa pelo ano). Isso é uma premissa e precisa ser aceita pela ELLO.

## 7. Questão de modelo

O motor ELLO atual trabalha assim: o alvo do mês é a soma das cotas elegíveis multiplicada pelos degraus fixos (R$ 14, 4, 18 e 18, cumulativos). Os eventos são consumidos em ordem até atingir esse alvo; o que sobra fica para o mês seguinte. A origem do evento não importa.

O arquivo recebido sugere outra leitura: existe um total a ser rateado, separado por categoria de veículo, a ser dividido entre os associados. Essa forma é mais próxima do motor AutoTruck (valor da cota calculado a partir do custo do mês).

| Leitura | Como funciona | Impacto no projeto |
|---|---|---|
| A. Orientado por alvo (motor atual) | valor por cota fixo; este arquivo é a fila de eventos | só falta um adaptador de leitura e a base de veículos |
| B. Orientado por custo | valor por cota = custo do mês por degrau dividido pelas cotas que pagam o degrau | exige um cálculo novo no motor ELLO, com validação própria |

Decisão (30/09/2026): a ELLO mantém a leitura A, com valor fixo por cota e eventos preenchendo os potinhos até atingir o alvo. A leitura B pertence ao modelo AutoTruck e não se aplica à ELLO. O arquivo recebido é, portanto, a fila de eventos do motor atual.

## 8. Decisões pendentes (com proposta)

| Nº | Decisão | Proposta |
|---|---|---|
| 1 | Confirmar o total esperado (R$ 4,75 milhões declarado x R$ 3,80 milhões deduplicado) | levar à ELLO antes de rodar |
| 2 | Remover duplicidade por PROTOCOLO | sim, sempre, com aviso na tela de importação |
| 3 | Situações elegíveis | excluir CANCELADO e FINALIZADO SEM RATEIO; confirmar as demais com a ELLO |
| 4 | Valores negativos | tratar como abatimento do total, se a ELLO confirmar que são estornos |
| 5 | Ordem de alocação sem data | usar o número do protocolo como proxy cronológico |
| 6 | Modelo de cálculo (A ou B) | DECIDIDO (30/09/2026): leitura A, valor fixo por cota preenchendo os potinhos até o alvo |
| 7 | Evento de funcionário | seguir a regra da ELLO; por padrão, ratear o evento |
| 8 | Competência | 09/2026 |

## 9. Próximos passos

1. Enviar à ELLO as perguntas das decisões 1, 3, 4, 6 e 7 e o pedido da base de veículos e dos serviços fixos.
2. Construir o leitor do formato real (este layout de planilha) com deduplicação, normalização de situação e relatório de importação, sem alterar a matemática do motor.
3. Com a base de veículos, rodar a competência 09/2026 e conciliar com o total confirmado pela ELLO.

Os arquivos reais ficam fora do controle de versão (pasta `ELLO/` incluída no `.gitignore`, mesma regra da pasta `Remonta/`).
