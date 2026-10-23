# Regras do rateio AVAP: fonte única

Atualizado em: 22/10/2026.

Este documento é a **referência vigente** de tudo o que sabemos sobre o rateio da AVAP. Os documentos anteriores (relatório, levantamento, análise de ago/set, listas de integrais e de retirados) ficam como histórico. Quando houver conflito, vale o que está aqui.

Cada item tem um status:

- **DECIDIDO**: confirmado pela AVAP ou provado pelos dados, com a fonte indicada. Não se pergunta de novo.
- **ABERTO, BLOQUEIA**: falta para o aceite com diferença zero do mês de referência (setembro/2026). Hoje não há nenhum item neste status.
- **ABERTO, NÃO BLOQUEIA**: dúvida real, mas o motor já funciona sem a resposta (o operador decide ou o valor vem pronto da planilha).

Siglas das fontes:

- **LEV**: `docs/LEVANTAMENTO_AVAP_organizado.md` (reunião de 30/09/2026).
- **ANA**: `docs/ANALISE_RATEIO_AGOSTO_SETEMBRO_AVAP.md` (planilha real de ago e set, recebida em 07/10/2026).
- **PLAN**: `AVAP/rateio_agosto.xlsx`, abas `Rateio_agosto` e `Rateio_setembro` (fechamento real, fora do git).

## 1. A fórmula

```
                 custo dos eventos selecionados
               + linhas de soma
               - linhas de dedução
valor da cota = ─────────────────────────────────
                 cotas dos veículos ativos

rateio do veículo = cotas do veículo x valor da cota
```

Pote único: sem categoria, sem segmento, sem regra dos 75% e sem FIFO.

## 2. Números de referência (fechamento real)

| | Agosto/2026 | Setembro/2026 |
|---|---:|---:|
| Eventos rateados | 150 | 103 |
| Custo dos eventos | R$ 1.775.640,36 | R$ 1.733.393,65 |
| Linhas de soma e dedução (líquido) | R$ 30.405,88 | R$ 68.674,27 |
| **Total a ratear** | **R$ 1.806.046,24** | **R$ 1.802.067,92** |
| Cotas de veículos ativos (base de 30/09, a única que temos) | 231.556 | 231.556 |
| **Valor por cota** | **cerca de R$ 7,80** | **R$ 7,78** |

Os valores antigos de "R$ 0,74 milhão por mês" e "R$ 3,18 por cota" (relatório e PRD) vieram do campo `Valor Rateado` do SGA, que não reflete o fechamento (ver 4.2). **Estão superados.**

## 3. Denominador (quem paga)

| # | Regra | Status | Fonte |
|---|---|---|---|
| 3.1 | Entra no denominador o **veículo ativo**. O que conta é a situação do veículo, não a do associado (o mesmo associado pode ter vários boletos e pagar só alguns). | **DECIDIDO** | LEV 1.18 e resposta da AVAP registrada em ANA seção 2 |
| 3.2 | Veículo **inadimplente fica fora** do rateio. A perda é compensada pelas linhas INADIMPLÊNCIA (soma) e RECEBIDOS ou RECEITA INAD. (dedução no mês seguinte). | **DECIDIDO** | ANA seção 2 |
| 3.3 | Pendente de adesão e pendente de revistoria **não entram**. | **DECIDIDO** | LEV 1.18 |
| 3.4 | Peso da cota: **ler do rótulo do SGA** (número entre parênteses no fim), nunca recalcular pela FIPE. 1 cota a cada R$ 5 mil. | **DECIDIDO** | LEV 1.8 e dados (2.270 veículos com peso diferente da FIPE) |
| 3.5 | Veículo depreciado paga a cota cheia. | **DECIDIDO** | LEV 1.9 |
| 3.6 | Ajuste de cota (ex.: remarcado) já vem no peso do SGA; o motor não aplica fator. | **DECIDIDO** | LEV 1.10 |
| 3.7 | Peso 0, FIPE 0 ou sem placa: fora do denominador, com alerta. | ABERTO, NÃO BLOQUEIA (D4) | default do motor |
| 3.8 | Sufixos VP, DP, CP, TP: mesmo peso, guardados como atributo. | ABERTO, NÃO BLOQUEIA (D3) | default do motor |

**Superado, não usar:**

- LEV 2.5 ("a situação que vale é a do associado"): contrariado pela resposta posterior em 3.1.
- ANA seção 7, último parágrafo (hipótese de dividir por todas as cotas, cerca de R$ 4,99): foi escrita depois da resposta da AVAP e ignorou essa resposta. Foi a origem da pergunta repetida sobre o valor por cota. Também não fecha com os números: dividindo por todas as cotas, os inadimplentes (cerca de 129 mil cotas) deixariam de pagar uns R$ 650 mil por mês, e a linha de inadimplência real é de R$ 100 a 110 mil. Com veículos ativos, essa linha equivale a umas 14 mil cotas (6% da base), o que é coerente.

## 4. Seleção dos eventos (o que entra)

| # | Regra | Status | Fonte |
|---|---|---|---|
| 4.1 | Só eventos **totalmente finalizados**. Não existe rateio parcial. | **DECIDIDO** | LEV 1.1 |
| 4.2 | O campo `Valor Rateado` do SGA **não define** o fechamento. O fechamento real de setembro foi: 79 dos 80 eventos da fila do SGA (`0.00` em 28/09), mais 24 eventos com campo vazio incluídos pelo operador (22 integrais, 1 colisão, 1 continuação), sem 1 evento excluído. Total de 103. | **DECIDIDO** (provado) | ANA seção 7 e teste `test_real_selecao_setembro_reproduz_fechamento` |
| 4.3 | Regra do motor: a fila do SGA entra por regra; o vazio só entra por decisão INCLUIR do operador, com justificativa. | **DECIDIDO** | consequência de 4.2 |
| 4.4 | **Integral (V.F.I, furto, roubo) é rateada inteira**, mesmo com pagamento parcelado. Setembro: 32 integrais, R$ 1.288.358,60. | **DECIDIDO** | LEV 1.5 e ANA seção 3 |
| 4.5 | Terceiros não são rateados (são produto). | **DECIDIDO** | LEV 1.16 |
| 4.6 | Corte: finalizados até a meia-noite do dia anterior ao fechamento. | **DECIDIDO** | LEV 1.3 |
| 4.7 | Competência do evento = mês do fechamento em que foi rateado, não a data de finalização (setembro levou eventos finalizados em agosto). | **DECIDIDO** | ANA seção 4 |
| 4.8 | Valor do evento = reparo menos participação. Vale em 100% das linhas da planilha real. | **DECIDIDO** | ANA seção 1 |
| 4.9 | Guincho e pátio do salvado ficam dentro do custo do evento. | **DECIDIDO** | LEV 1.15 |
| 4.10 | Critério que deixa integrais finalizados de fora (39 eventos, R$ 1,88 mi, fora de ago e set). | ABERTO, NÃO BLOQUEIA | o motor gera alerta A5 e o operador decide |
| 4.11 | Furto 2026819916 (R$ 67.092,44): por que ficou fora de setembro. | ABERTO, NÃO BLOQUEIA | perguntado ao presidente da AVAP |

**Superado, não usar:** "73 rateados e 7 integrais retirados" (relatório, versão de 03/10) e a lista `AVAP_eventos_retirados_fila_09_2026.md`. Dos 7, 6 estão no rateio real; só o 2026819916 ficou fora.

## 5. Linhas de soma e dedução

| # | Linha | Tipo | Ago | Set | Status |
|---|---|---|---:|---:|---|
| 5.1 | E-SAUDE (telemedicina) | soma | 3 x 16.310,38 | 16.239,82 | valor **DECIDIDO** (vem da planilha); por que aparece 3 vezes em agosto: ABERTO, NÃO BLOQUEIA |
| 5.2 | RASTREAMENTO | soma | 119.481,22 | 118.173,45 | valor **DECIDIDO**; se é custo do pote ou repasse: ABERTO, NÃO BLOQUEIA. Atenção: o rastreador também aparece como produto pago à parte no boleto (R$ 30,00 no caso de 6.5); perguntar se a linha do pote é o custo de quem não paga o produto ou se há cobrança em dobro |
| 5.3 | INADIMPLÊNCIA do mês | soma | 99.605,19 | 109.035,49 | valor **DECIDIDO**; fórmula: ABERTO, NÃO BLOQUEIA |
| 5.4 | Recuperados do mês anterior | dedução | 42.840,20 | 45.521,49 | **DECIDIDO** |
| 5.5 | Salvados vendidos | dedução | 194.771,47 | (ver 5.6) | **DECIDIDO** |
| 5.6 | Linha sem descrição | dedução | | 129.253,00 | conteúdo: ABERTO, NÃO BLOQUEIA (provável salvados) |

Regras gerais (DECIDIDO, LEV 1.11 a 1.17): valor sempre positivo, o sinal vem do tipo; deduções entram cheias, sem efeito contábil.

No mês a mês, o operador digita essas linhas. Elas não precisam ser calculadas pelo motor, por isso as dúvidas acima não bloqueiam.

## 6. Boleto

| # | Regra | Status | Fonte |
|---|---|---|---|
| 6.1 | Um boleto real de 09/2026 (veículo de 20 cotas) traz **só o total** da mensalidade (R$ 270,73), sem separar rateio, taxa e produtos. Ele aponta para um "extrato de rateio" na área do associado. | **DECIDIDO** (verificado no documento) | boleto recebido em 12/10/2026, fora do git |
| 6.2 | Por isso o boleto **não serve de aceite**. O aceite é a planilha PLAN. Pelo motor (20 cotas x R$ 7,7824..., arredondado só no boleto), o rateio desse veículo é R$ 155,65; o restante (R$ 115,08) seriam taxa e produtos. | **DECIDIDO** | consequência de 6.1 |
| 6.3 | Split da Res. 491, art. 70 (rateio, estabilização, taxa de administração, produtos). Hoje só o rateio é calculado; os outros ficam em 0. | ABERTO, NÃO BLOQUEIA (D5) | depende da Mutualiza e do atuário |
| 6.4 | Layout do arquivo de cobrança para o SGA. | ABERTO, NÃO BLOQUEIA (D8) | operação AVAP |
| 6.5 | Conferência por amostra (5 veículos, rateio pelo motor). O SGA não "explode" o boleto, mas o relatório de proteção veicular mostra, por placa, o total do último boleto (emitido em 01/10/2026, referente a setembro) e os produtos contratados com valor. Caso aberto, veículo de 24 cotas: boleto R$ 379,66 = rateio do motor R$ 186,78 (24 x 7,7824...) + produtos R$ 99,60 (assistência 300 km 26,80; carro reserva 6,90; rastreador 30,00; terceiros 30 mil 24,00; vidros 11,90; colisão 0,00; roubo/furto 0,00) + restante R$ 93,28 (taxa de administração e o que mais houver: não confirmado). Colisão e roubo/furto a R$ 0,00 confirmam que a cobertura é paga pelo rateio e o resto é produto. Os outros dois totais (R$ 126,73 e R$ 283,74) ainda sem placa confirmada. Para fechar: valor da taxa de administração do veículo; com ele, rateio = boleto - produtos - taxa, e dividido pelas cotas tem que dar 7,78. | ABERTO, NÃO BLOQUEIA | conversa com a Mutualiza em 22/10/2026 |
| 6.6 | A Mutualiza confirmou que **precisa** da discriminação rateio, produtos e taxa no boleto. Isso puxa o 6.3 (split) de "um dia" para requisito do produto. | **DECIDIDO** (requisito) | conversa com a Mutualiza em 22/10/2026 |

## 7. Aceite

O mês de referência é **setembro/2026**. Agosto foi usado só como comparação, para entender as regras, e não é critério de aceite (decisão do Dudu em 22/10/2026).

| Mês | Situação |
|---|---|
| Setembro/2026 | **APROVADO**: 103 eventos, total R$ 1.802.067,92, diferença zero. Referência do aceite. |
| Agosto/2026 | Só comparação. 3 protocolos diferem entre a planilha de agosto e as fotos do SGA de setembro; **não bloqueia**. |

Os 3 protocolos de agosto (ANA seção 4), guardados como histórico, sem pergunta pendente:

- 2026779124 (colisão de R$ 12.525): está no rateio de agosto, mas não aparece nas fotos do SGA de 28/09 e 30/09.
- 2026782899: reparo de R$ 11.092,69 na planilha contra R$ 0 na foto do SGA de 28/09 (veículo entregue, previsão de R$ 9.040,55).
- 2026795888: reparo de R$ 28.217,80 na planilha contra R$ 35.426,80 na foto do SGA de 28/09.

"SGA" aqui são sempre os relatórios exportados que a AVAP nos mandou (fotos de 28/09 e 30/09). Não temos acesso direto ao sistema.

## 8. O que perguntar à AVAP (e só isso)

Nada bloqueia. Perguntar só se houver espaço na conversa, nesta ordem (as três primeiras mudam a operação mês a mês):

1. Critério que deixa integrais finalizados de fora (4.10).
2. Fórmula da linha de inadimplência (5.3).
3. Layout do arquivo de cobrança para o SGA (6.4).
4. Linha sem descrição de R$ 129.253,00 em setembro (5.6).
5. Rastreamento: custo do pote ou repasse (5.2).
6. Sufixos VP, DP, CP, TP (3.8).
7. E-SAUDE 3 vezes em agosto (5.1).

Já com o presidente da AVAP: furto 2026819916 (4.11).

**Nunca perguntar** nada marcado como DECIDIDO acima, em especial o denominador e o valor por cota. Também não perguntar os 3 protocolos de agosto.

## 9. Fora da regra de rateio, mas em aberto

- Demonstração na Fenaprove (18 e 19/11/2026): **DECIDIDO** base anonimizada (aba Fenauto, arquivos fictícios em `demo_fenauto/`, R$ 7,78 por cota exatos).
- Estabilização obrigatória pela Res. 491, art. 69 (D5).
- Modelo "associação cotista da administradora" e a vedação de partes relacionadas: levar ao jurídico.
