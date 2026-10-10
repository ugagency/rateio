# AVAP: o que o rateio real de agosto e setembro mostra

Fonte: `AVAP/rateio_agosto.xlsx` (abas `Rateio_agosto` e `Rateio_setembro`), enviado pelo Cícero em 07/10/2026, cruzado com as fotos de 28/09 e 30/09 do SGA.

## 1. Como a planilha é montada

Cada aba é o fechamento do mês: linhas de evento (com placa) mais linhas de soma e dedução (sem placa). Em todo evento vale `Valor Rateado = Valor Reparo - Valor Participação`, sem exceção (150 em agosto, 103 em setembro).

| | Agosto | Setembro |
|---|---:|---:|
| Eventos | 150 | 103 |
| Valor rateado dos eventos | R$ 1.775.640,36 | R$ 1.733.393,65 |
| Linhas sem placa (líquido) | R$ 30.405,88 | R$ 68.674,27 |
| **Total a ratear** | **R$ 1.806.046,24** | **R$ 1.802.067,92** |
| Ordem de grandeza por cota (231.628 cotas ativas) | ~R$ 7,80 | ~R$ 7,78 |

Linhas sem placa:

| Linha | Agosto | Setembro |
|---|---:|---:|
| E-SAUDE | 3 x 16.310,38 | 1 x 16.239,82 |
| RASTREAMENTO | 119.481,22 | 118.173,45 |
| INADIMPLÊNCIA do mês | +99.605,19 | +109.035,49 |
| Recuperados do mês anterior | -42.840,20 (inad. julho) | -45.521,49 (recebidos ago) |
| Salvados | -194.771,47 | linha sem descrição de -129.253,00 |

## 2. Resposta sobre inadimplência

O Cícero respondeu: o que conta é o **veículo**, não o associado (o mesmo associado pode ter vários boletos e pagar só alguns). Veículo inadimplente não entra no rateio. A compensação aparece em duas linhas:

- `INADIMPLÊNCIA <mês>`: soma ao custo o que os inadimplentes deixaram de pagar, para quem pagou não ficar no prejuízo.
- `RECEITA INAD.` / `RECEBIDOS`: no mês seguinte, o que foi recuperado volta como dedução.

Isso fecha a pergunta 3 do relatório (denominador): situação do **veículo** manda, e o associado só importa como dono dos veículos. Fica a confirmar como a linha de inadimplência é calculada (cota do mês dos veículos inadimplentes?).

## 3. Achado principal: o campo `Valor Rateado` do SGA não é a verdade

Na foto de 30/09, 22 V.F.I, 4 furtos, 2 roubos, 1 colisão e 1 continuação (R$ 1.171.686,28 pelo rateio) aparecem **vazios** no SGA, mas estão **dentro** do rateio real de setembro. Entre eles estão 6 dos 7 eventos que eu tinha dado como "retirados da fila":

2026804427, 2026811385, 2026812583, 2026814192, 2026816052, 2026817349.

Ou seja, eles não saíram do fechamento. O que ficou de fora de verdade foi só o **2026819916** (furto, R$ 67.092,44, finalizado em 28/09). O Cícero escreveu o último número truncado (`202681991`), é esse. A pergunta que ele repassou ao presidente da AVAP deve ser reduzida a este protocolo.

Consequências:

1. Integral **é rateada inteira**, como a reunião de 30/09 dizia. Setembro: 32 integrais = R$ 1.288.358,60 (74% do rateio de eventos). Agosto: 19 integrais = R$ 647.695,42 (36%).
2. A seleção do motor não pode usar o campo `Valor Rateado` do SGA. A tensão aberta "712 finalizados sem Valor Rateado" tende a se explicar assim. Precisa de regra própria de seleção (D1 do PRD).
3. A premissa "as fotos de 28/09 e 30/09 são o fechamento: 73 rateados + 7 retirados" estava errada e precisa ser corrigida no relatório, no levantamento, no PRD e em `AVAP_eventos_retirados_fila_09_2026.md`.

## 4. Critério de corte ainda não decifrado

- Eventos finalizados em set na aba agosto: 11. Finalizados em ago na aba setembro: 14. A data de finalização sozinha não define o mês.
- A coluna `Data` da planilha é a data do evento (vai de 2025 a 2026), não a de finalização.
- Há **39 integrais** finalizados em ago/set (R$ 1.880.268,04), com SGA vazio, que não estão em nenhuma das duas abas. Pode ser adiamento, acordo pendente ou salvado pendente. É a pergunta real a fazer.
- 9 eventos finalizados em 29 e 30/09 (6 colisões, 3 continuações) estão no SGA com `0.00` e fora da aba setembro: provável corte por data de fechamento.
- Agosto: 2 divergências de valor contra a foto (2026795888: reparo 28.217,80 na planilha x 35.426,80 no SGA; 2026782899: reparo 11.092,69 x 0) e 1 protocolo que não existe na foto de 30/09 (2026779124, colisão de R$ 12.525).

## 5. Perguntas novas para a AVAP

1. Qual a regra de seleção do mês? O que faz um integral finalizado entrar (66 de 105) ou ficar de fora (39, R$ 1,88 mi)?
2. O furto 2026819916 (R$ 67 mil) saiu por quê?
3. E-SAUDE aparece 3 vezes em agosto (R$ 48.931,14) e 1 vez em setembro. São três competências, três planos ou duplicidade?
4. Qual o conteúdo da linha sem descrição de -R$ 129.253,00 em setembro (salvados, como em agosto)?
5. Como é calculada a linha de inadimplência (quais veículos, qual valor por cota)?
6. Qual o valor por cota efetivamente cobrado em agosto e setembro, e o denominador usado? Com isso fecho a conta e valido o Δ=0.
7. Rastreamento (~R$ 118 mil) é custo do pote ou repasse a terceiro?
8. Os 2 eventos de agosto com valor divergente do SGA: houve ajuste manual?

## 6. Efeito no PRD_AVAP

- D1 (integrais): passa de dúvida para **rateadas inteiras**, conferir só a regra de seleção.
- D7 (linhas de soma/dedução): agora há o catálogo real: E-SAUDE, RASTREAMENTO, INADIMPLÊNCIA, recuperados, salvados.
- Aceite da fase 1: já existem dois fechamentos completos (ago e set) para reproduzir, falta o denominador e o valor por cota.
