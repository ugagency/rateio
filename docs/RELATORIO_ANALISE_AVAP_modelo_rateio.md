# Análise do modelo de rateio: Associação AVAP

Arquivos analisados (pasta `AVAP/`, exportações do SGA Hinova):

| Arquivo | Conteúdo | Gerado em |
|---|---|---|
| `Cotas_ativasAVAP_09_26.xlsx` | base de veículos com cota, categoria, FIPE e situação | 30/09/2026 |
| `foto28-09.xlsx` | eventos finalizados de 01/2025 a 28/09/2026, antes do fechamento de 09/2026 | 28/09/2026 |
| `foto30-09.xlsx` | os mesmos eventos, depois do fechamento de 09/2026 | 30/09/2026 |

As duas fotos são fechamentos reais da AVAP, exportados do SGA por quem opera o rateio (confirmado pela Mutualiza em 03/10/2026).

Data da análise: 01/10/2026. Competência presumida: 09/2026.

## 1. Resumo

1. **A AVAP já manda o pacote completo.** Diferente da ELLO, aqui temos base de veículos com cotas e eventos com custo, participação e valor rateado. Dá para reconstruir o modelo atual e simular o motor.
2. **O modelo atual é repasse de custo, não valor fixo por cota.** Quando um evento é rateado, o `Valor Rateado` é exatamente igual ao `Valor Custo Evento` (2.343 de 2.343 casos). Esse é o formato do motor AutoTruck (soma dos custos dividida pelas cotas), não o do motor ELLO.
3. **Indenizações integrais quase nunca aparecem como rateadas.** V.F.I, FURTO e ROUBO somam 500 eventos e R$ 21,5 milhões (55% do custo em 21 meses), mas só 16 deles têm `Valor Rateado`. Os arquivos não dizem como essas indenizações são pagas. Essa é a pergunta número 1 para a AVAP.
4. **As duas fotos NÃO são o fechamento completo de setembro (corrigido em 10/10/2026).** CORREÇÃO de 10/10/2026: o rateio real de agosto e setembro (`AVAP/rateio_agosto.xlsx`, ver `ANALISE_RATEIO_AGOSTO_SETEMBRO_AVAP.md`) mostrou que o campo `Valor Rateado` do SGA não é a verdade do fechamento. O rateio real de setembro tem 103 eventos (R$ 1.733.393,65), incluindo 6 dos 7 eventos que eu havia dado como retirados; só o furto 2026819916 ficou de fora. A diferença entre as fotos mostra apenas o que o SGA marcou, não o fechamento. Texto original, mantido para histórico:  Em 28/09 a fila tinha 80 eventos (R$ 849.115,48, igual ao "Valor a Ratear" do rodapé somando eventos e eventos relacionados). Em 30/09, 73 deles foram rateados (R$ 561.707,37) e 7 integrais (R$ 287.408,11) foram tirados da fila e voltaram para vazio. Ou seja, as integrais entram na fila e uma parte é excluída na hora de fechar.
5. **A cota tem que ser lida da base, não recalculada.** A regra é 1 cota a cada R$ 5.000 de FIPE, mas 2.270 veículos (6%) estão com cota diferente da FIPE atual, a maioria uma faixa abaixo.

## 2. Base de veículos e cotas

### 2.1 Totais

| Recorte | Veículos | Cotas | FIPE total (R$) |
|---|---:|---:|---:|
| Base completa (confere com o rodapé do SGA) | 39.242 | 361.530 | 1,73 bi |
| Veículo ATIVO | 22.539 | 231.628 | 1,11 bi |
| Veículo INADIMPLENTE | 16.703 | 129.902 | 0,61 bi |

O arquivo se chama "cotas ativas", mas 43% dos veículos estão inadimplentes. O rodapé do SGA (361.530 cotas) inclui os inadimplentes.

### 2.2 Situação do veículo x situação do associado

| Veículo | Associado | Veículos | Cotas |
|---|---|---:|---:|
| ATIVO | ATIVO | 22.520 | 231.386 |
| INADIMPLENTE | INADIMPLENTE | 13.419 | 101.121 |
| INADIMPLENTE | ATIVO | 3.267 | 28.585 |
| ATIVO | INADIMPLENTE / PENDENTE | 19 | 242 |
| INADIMPLENTE | PENDENTE (revistoria, adesão) | 17 | 196 |

Os 3.267 veículos inadimplentes de associado ativo (28.585 cotas) mudam o denominador em 12%. Precisa saber qual das duas situações define quem entra no rateio.

### 2.3 Categorias

| Categoria | Veículos | Cotas | Cotas por veículo |
|---|---:|---:|---:|
| PASSEIO | 37.977 | 337.059 | 8,9 |
| GRUPO ESPECIAL | 982 | 22.013 | 22,4 |
| ALUGUEL | 263 | 2.271 | 8,6 |
| APLICATIVO | 15 | 158 | 10,5 |
| OFICIAL | 5 | 29 | 5,8 |

Todos os veículos são do tipo AUTOMOVEL. Não há motos nem pesados nesta base.

### 2.4 Regra da cota

A cota segue a faixa de FIPE: 1 cota até R$ 5.000 e mais 1 a cada R$ 5.000 (cota 80 = R$ 395.000,01 a R$ 400.000,00). São 211 rótulos distintos para cerca de 80 faixas, porque o mesmo degrau aparece com variações de escrita e com quatro sufixos:

| Sufixo | Veículos | Cotas |
|---|---:|---:|
| (sem sufixo) | 37.476 | 341.615 |
| VP | 968 | 10.125 |
| DP | 518 | 5.809 |
| CP | 240 | 3.374 |
| TP | 40 | 607 |

O significado de VP, DP, CP e TP não está nos arquivos. O peso entre parênteses no fim do rótulo é igual para todos os sufixos do mesmo degrau, então para o denominador eles não fazem diferença; podem fazer para o valor do boleto.

**Divergência FIPE x cota:** 2.270 veículos estão com cota diferente da que a FIPE atual indicaria. Em 1.915 casos a cota está uma faixa abaixo, em 282 casos duas faixas abaixo. O padrão sugere que a cota é fixada na adesão e não acompanha a FIPE. Por isso o motor deve usar o peso informado pelo SGA, nunca recalcular.

### 2.5 Problemas de cadastro

| Problema | Quantidade |
|---|---:|
| Placa vazia | 69 |
| FIPE zero ou vazia | 80 |
| Cota zero (4 "PRODUTOS AVULSOS" e 1 "COTA 0.00") | 5 |
| Placa duplicada | 0 |

## 3. Eventos

### 3.1 Estrutura e conferência

O arquivo de 30/09 tem 3.104 eventos, em linhas de dados limpas, mais um rodapé do SGA. A leitura confere com o rodapé:

| Rodapé do SGA | Valor |
|---|---:|
| Eventos encontrados | 3.068 |
| Eventos relacionados | 36 |
| Total | 3.104 |
| Custo eventos (R$) | 38.854.264,48 |
| Custo eventos relacionados (R$) | 268.727,31 |
| Custo total (R$) | 39.122.991,79 |

A soma das linhas lidas é exatamente R$ 39.122.991,79 em 3.104 protocolos, sem duplicidade. Não foi possível identificar quais são os 36 "eventos relacionados" (não batem com CONTINUAÇÃO DE PROCESSO, que são 159, nem com Evento Terceiro, que são 17).

Relações confirmadas linha a linha:

- `Valor Custo Evento = Valor Reparo − Valor Participação` (zero exceções).
- `Valor Rateado` tem três estados:

| Estado | Eventos | Significado |
|---|---:|---|
| igual ao custo | 2.343 | evento já rateado |
| `0.00` | 9 | evento na fila do fechamento |
| vazio | 752 | ainda não rateado (candidato, segundo o levantamento de 30/09; ver `LEVANTAMENTO_AVAP_organizado.md`, seção 9) |

A prova do estado `0.00`: os 9 eventos novos do dia 29 e 30/09 somam R$ 49.098,45 + R$ 620,00, exatamente o "Valor a Ratear" que o rodapé mostra para eventos e eventos relacionados.

### 3.2 Custo por motivo (01/2025 a 30/09/2026)

| Motivo | Eventos | Custo (R$) | Com valor rateado | Valor rateado (R$) |
|---|---:|---:|---:|---:|
| COLISÃO | 2.125 | 16.557.354 | 1.908 | 14.181.480 |
| V.F.I | 322 | 13.690.474 | 13 | 522.863 |
| FURTO | 156 | 6.811.782 | 2 | 40.357 |
| ROUBO | 22 | 1.043.134 | 1 | 25.814 |
| ROUBO PARCIAL | 33 | 360.801 | 27 | 254.085 |
| CONTINUAÇÃO DE PROCESSO | 159 | 234.216 | 138 | 191.804 |
| REPAROS | 17 | 180.958 | 3 | 34.602 |
| CARRO RESERVA | 248 | 146.022 | 247 | 146.715 |
| ALAGAMENTO | 5 | 73.886 | 5 | 73.886 |
| Outros (vidros, incêndio, frota, terceiro) | 17 | 24.364 | 8 | 20.197 |
| **Total** | **3.104** | **39.122.992** | **2.352** | **15.491.803** |

Leitura: o rateio de hoje cobre basicamente o dano parcial (colisão, roubo parcial, carro reserva). As perdas totais (V.F.I, furto, roubo), que custam em média R$ 43 mil por evento, cerca de 90% do teto da faixa de FIPE, ficam fora do `Valor Rateado`. Também ficam fora 217 colisões (R$ 2,3 milhões) e 15 dos 17 eventos de terceiro. Pelo levantamento de 30/09, os terceiros ficam fora porque são vendidos como produto, e as integrais com acordo deveriam ser rateadas por inteiro, o que estes dados não mostram (tensão em aberto).

Hipóteses possíveis para as integrais, sem como decidir pelos arquivos: fundo de reserva pago por uma parcela fixa da mensalidade, rateio em separado, parcelamento em vários meses ou simplesmente não registrado neste campo.

### 3.3 Situação dos eventos

| Situação | Eventos | Com valor rateado |
|---|---:|---:|
| FINALIZADO | 3.064 | 2.352 |
| FINALIZADO SEM RATEIO | 33 | 0 |
| VEÍCULO ENTREGUE | 5 | 0 |
| CANCELADO | 1 | 0 |
| PENDENTE NF | 1 | 0 |

"FINALIZADO SEM RATEIO" confirma que existe uma decisão explícita de excluir eventos. Mas 712 eventos FINALIZADO (R$ 23,3 milhões) também estão sem rateio, e a maioria são integrais.

### 3.4 Pontos de atenção nos eventos

- 10 eventos com custo negativo (R$ −7.372 no total), possíveis estornos. Só 2 deles aparecem como rateados (com valor negativo). O motor atual ignora saldo menor ou igual a zero.
- Categorias dos eventos (PASSEIO, GRUPO ESPECIAL, ALUGUEL, APLICATIVO) batem com as da base.
- O arquivo de 28/09 traz Nome e Placa; o de 30/09 não traz, e traz Tipo Veículo. Para rastreabilidade o layout de 28/09 é melhor. Dos 2.797 veículos com evento, 1.666 continuam na base (1.460 ativos), o que é esperado, já que veículos indenizados saem.

## 4. O ciclo de fechamento (28/09 para 30/09)

| Mudança | Eventos |
|---|---:|
| Eventos novos (finalizados em 29 e 30/09, todos com `0.00`) | 9 |
| `Valor Rateado` de `0.00` para o custo (rateados) | 73 |
| `Valor Rateado` de `0.00` para vazio (tirados da fila) | 7 |
| Data de finalização alterada | 11 |
| Cota do veículo alterada | 2 |

> CORREÇÃO de 10/10/2026: o rateio real de agosto e setembro (`AVAP/rateio_agosto.xlsx`, ver `ANALISE_RATEIO_AGOSTO_SETEMBRO_AVAP.md`) mostrou que o campo `Valor Rateado` do SGA não é a verdade do fechamento. O rateio real de setembro tem 103 eventos (R$ 1.733.393,65), incluindo 6 dos 7 eventos que eu havia dado como retirados; só o furto 2026819916 ficou de fora. A diferença entre as fotos mostra apenas o que o SGA marcou, não o fechamento.

A fila de 28/09 tinha 80 eventos, e a soma deles é exatamente o "Valor a Ratear" do rodapé de 28/09 (R$ 848.735,48 de eventos mais R$ 380,00 de eventos relacionados, total R$ 849.115,48). No fechamento ela se dividiu em dois grupos:

| Grupo | Eventos | Valor (R$) | Composição |
|---|---:|---:|---|
| Rateados | 73 | 561.707,37 | 54 colisões, 15 continuações, 3 V.F.I, 1 roubo parcial |
| Tirados da fila (voltaram para vazio) | 7 | 287.408,11 | 5 V.F.I e 2 furtos, todos finalizados em 18 ou 23/09 |

O valor rateado é igual ao custo em todos os 73 (diferença zero) e confere com o aumento do "Valor Rateado" no rodapé (R$ 561.327,37 de eventos mais R$ 380,00 de relacionados). Esse é o primeiro dado que explica a tensão das integrais: elas entram na fila, mas na hora de fechar algumas são rateadas e outras são retiradas. O critério da retirada não está nos arquivos.

Dos 73 rateados, 66 foram finalizados em setembro e 7 em agosto. Ou seja, o fechamento de um mês leva também eventos finalizados antes, e a data de finalização é só uma aproximação da competência. Para o motor, a competência tem que vir do próprio fechamento (data em que o evento foi rateado), não da finalização.

Também mudaram datas de finalização de eventos já fechados (um evento foi de 02/03/2026 para 28/09/2026). Isso reforça a necessidade de fotografar e lacrar a base no fechamento, como já fazemos no AutoTruck.

## 5. Ordem de grandeza por cota

Estimativa grosseira: são 21 meses de eventos contra uma única foto da base (09/2026), e não sabemos o tamanho da frota no passado.

| Numerador mensal médio | Valor (R$/mês) | Por cota, 231.628 cotas ativas | Por cota, 361.530 cotas totais |
|---|---:|---:|---:|
| Só o que foi rateado | 737.705 | 3,18 | 2,04 |
| Custo total (parcial + integral) | 1.862.999 | 8,04 | 5,15 |
| Só integrais (V.F.I, furto, roubo) | 1.025.971 | 4,43 | 2,84 |

Faixa de variação mês a mês do custo total: de R$ 1,02 milhão (06/2025) a R$ 2,78 milhões (09/2026). Setembro de 2026 tem o maior custo da série, puxado por integrais (R$ 2,23 milhões). Sem estabilização, um modelo de repasse integral faria a cota oscilar mais que o dobro entre meses.

## 6. Encaixe com os motores que já temos

| Ponto | Motor ELLO | Motor AutoTruck | AVAP hoje |
|---|---|---|---|
| Lógica | valor fixo por cota, eventos enchem os potes até o alvo | soma dos custos do mês dividida pelas cotas | repasse do custo (rateado = custo) |
| Peso | cota por categoria | cota por FIPE | cota por FIPE (degraus de R$ 5 mil) |
| Integrais | dentro do pote | dentro do numerador, com regra dos 75% e salvado | fora do `Valor Rateado` |
| Estabilização | o próprio alvo | média trimestral ±5% | não identificada |
| Fechamento lacrado | não | sim (D+0 a D+5, SHA-256) | não |

Recomendação: o motor AutoTruck é o ponto de partida natural para a AVAP, condicionado à resposta sobre as integrais. Se as integrais estiverem num fundo separado, o motor rateia só o parcial e o fundo vira um pote fixo. Se a AVAP quiser trazer as integrais para dentro do rateio, a estabilização trimestral passa a ser obrigatória.

Ajustes necessários, todos pequenos:

1. Leitor do layout SGA desta exportação (cabeçalho na linha 1, rodapé com resumo, valores como texto).
2. Peso lido do rótulo da cota, sem recálculo pela FIPE.
3. Segmentação por categoria a decidir (PASSEIO e GRUPO ESPECIAL juntos ou separados).
4. Uma única faixa de veículo (só automóvel), sem segmento de motos ou pesados.

Primeira validação proposta (revista em 10/10/2026): reconstruir o fechamento de setembro da planilha real (103 eventos, R$ 1.733.393,65 mais linhas, total R$ 1.802.067,92) e comparar com o valor cobrado por cota no boleto de outubro. Se bater, temos o mesmo tipo de aceite com diferença zero que fizemos no AutoTruck.

## 7. Perguntas para a AVAP

1. **Integrais.** Como V.F.I, furto e roubo são pagos hoje? Fundo de reserva, rateio à parte, parcelamento? Existe alguma rubrica no boleto para isso? Respondida em parte em 10/10/2026: integral é rateada inteira; 6 dos 7 "retirados" estavam no rateio real. Resta o furto 2026819916 (R$ 67.092,44) e o critério que deixou 39 integrais (R$ 1,88 mi) fora de agosto e setembro.
2. **Colisões sem rateio.** Por que 217 colisões (R$ 2,3 milhões) e 15 eventos de terceiro não têm `Valor Rateado`?
3. **Denominador.** Quem entra na divisão: situação do veículo, situação do associado ou as duas? Os inadimplentes pagam rateio?
4. **Valor por cota.** Qual foi o valor por cota cobrado nos últimos meses? Com isso calibramos a simulação.
5. **Sufixos VP, DP, CP e TP.** O que significam e se mudam o valor cobrado.
6. **Reenquadramento.** A cota é fixada na adesão ou é reclassificada quando a FIPE muda? Com que frequência?
7. **Categorias.** PASSEIO, GRUPO ESPECIAL, ALUGUEL e APLICATIVO pagam a mesma cota ou têm potes separados?
8. **Competência.** Qual é a data de corte do fechamento? Eventos finalizados em agosto entraram no fechamento de setembro.
9. **Eventos relacionados.** O que são os 36 "eventos relacionados" do rodapé e como o SGA os identifica?
10. **Negativos.** Os 10 custos negativos são estornos? Devem abater o rateio?
11. **Layout.** Podemos padronizar a exportação no formato de 28/09 (com Placa) mais a coluna Tipo Veículo?
12. **Modelo novo.** O que a AVAP quer mudar em relação ao modelo de hoje? A resposta define se mantemos o repasse de custo ou se evoluímos para alvo com estabilização.
