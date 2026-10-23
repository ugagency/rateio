# Guia da reunião: rateio AVAP

Preparação particular do Dudu para a conversa com o Cícero. Não é para entregar.
Base: `docs/REGRAS_RATEIO_AVAP.md` (fonte única, atualizada em 22/10/2026). Se algum número aqui divergir dela, vale ela.

## 1. A mensagem em uma frase

O motor reproduziu o fechamento de setembro/2026 da AVAP **ao centavo**: os mesmos 103 eventos, o mesmo total de R$ 1.802.067,92 e o mesmo valor por cota de R$ 7,78. Nada do mês de referência depende de resposta da AVAP.

## 2. A fórmula, em palavras simples

A AVAP faz rateio em **pote único**: soma tudo o que custou no mês e divide pelas cotas de quem está ativo.

```
                 custo dos eventos do mês
               + linhas de soma        (rastreamento, telemedicina, inadimplência)
               - linhas de dedução     (salvados vendidos, inadimplentes recuperados)
valor da cota = ───────────────────────────────────────────
                 total de cotas dos veículos ativos

boleto do veículo = cotas do veículo x valor da cota
```

O que **não** existe na AVAP (e existe em outras associações): categoria, segmento, classificação de risco, regra dos 75%, fila FIFO. Só cota.

**Cota:** 1 cota a cada R$ 5 mil de FIPE. Carro de R$ 20 mil tem 4 cotas; de R$ 100 mil, 20 cotas. O motor lê o número de cotas que já vem no relatório do SGA (o número entre parênteses no fim do rótulo, por exemplo "COTA 4,0 ... (4.00)") e nunca recalcula pela FIPE, porque 2.270 veículos têm peso diferente do que a FIPE daria (ajustes, remarcados).

## 3. O resultado de setembro

| Item | Valor |
|---|---:|
| Eventos rateados | 103 |
| Custo dos eventos | R$ 1.733.393,65 |
| Linhas de soma | + R$ 243.448,76 |
| Linhas de dedução | - R$ 174.774,49 |
| **Total a ratear** | **R$ 1.802.067,92** |
| Veículos ativos no denominador | 22.530 |
| Cotas no denominador | 231.556 |
| **Valor por cota** | **R$ 7,78** |

Composição das linhas de setembro:

| Linha | Tipo | Valor |
|---|---|---:|
| E-SAÚDE (telemedicina) | soma | 16.239,82 |
| RASTREAMENTO | soma | 118.173,45 |
| INADIMPLÊNCIA SET. 2026 | soma | 109.035,49 |
| RECEBIDOS AGO 2026 (inadimplentes recuperados) | dedução | 45.521,49 |
| Linha sem descrição (provável salvados) | dedução | 129.253,00 |

Integrais (V.F.I, furto, roubo) pesam muito: em setembro foram 32 integrais, R$ 1.288.358,60, ou **74% do custo dos eventos**.

### Cuidado com duas "diferenças" que parecem a mesma coisa

1. **Diferença zero (o aceite):** o motor chega ao mesmo total e aos mesmos eventos da planilha de fechamento da AVAP. Isso é o que prova que o motor está certo.
2. **Diferença de arredondamento dos boletos (R$ -13,25 em setembro):** cada boleto é arredondado no centavo (cotas x R$ 7,7824...). Somando os 22.530 boletos, sobram R$ 13,25 a menos que o total. O motor **mostra** essa sobra e **nunca redistribui** entre associados. É normal e esperado; o teste interno aceita até 1 centavo por boleto.

Na demo pública (Fenauto, dados fictícios) a sobra é zero porque o valor por cota foi ajustado para R$ 7,78 exatos. Na demo com os dados reais da AVAP aparece R$ -13,25. Se o Cícero perguntar, a resposta é o item 2 acima.

## 4. Quem paga: o denominador

- Entra o **veículo ativo**. Conta a situação do veículo, não a do associado (o mesmo associado pode ter vários veículos e pagar só alguns boletos). Resposta do próprio Cícero, registrada em 07/10/2026.
- **Inadimplente fica fora.** A perda não some: volta pela linha INADIMPLÊNCIA (soma no mês) e, quando o inadimplente paga depois, pela linha RECEBIDOS (dedução no mês seguinte).
- Pendente de adesão e pendente de revistoria não entram.
- Veículo depreciado paga cota cheia.

Setembro, na base de 30/09 (39.242 veículos):

| Situação | Veículos |
|---|---:|
| Ativos, no denominador | 22.530 |
| Fora: veículo inadimplente | 16.683 |
| Fora: associado pendente | 24 |
| Fora: peso zero | 5 |

Por que "dividir por todas as cotas" está errado (caso alguém levante a hipótese): daria uns R$ 4,99 por cota, mas aí os inadimplentes (cerca de 129 mil cotas) deixariam de pagar uns R$ 650 mil por mês, e a linha de inadimplência real é de R$ 100 a 110 mil. Com veículos ativos a conta fecha. **Esse assunto está decidido; não se pergunta de novo.**

## 5. Quais eventos entram

Regras decididas:

- Só evento **totalmente finalizado**. Não existe rateio parcial.
- Corte: finalizado até a meia-noite do dia anterior ao fechamento.
- **Integral é rateada inteira**, mesmo que o pagamento ao associado seja parcelado.
- Terceiros não entram (são vendidos como produto).
- Guincho e pátio do salvado ficam dentro do custo do evento.
- Valor do evento = reparo menos participação do associado.
- O evento pertence ao mês do fechamento em que foi rateado, não ao mês da finalização (setembro levou eventos finalizados em agosto).

**O achado mais importante:** o campo `Valor Rateado` do relatório do SGA **não define** o fechamento. Setembro foi montado assim:

- 79 dos 80 eventos que estavam na "fila" do SGA (campo `Valor Rateado` = 0,00 na foto de 28/09), 1 excluído;
- mais **24 eventos com o campo vazio**, incluídos pelo operador (22 integrais, 1 colisão, 1 continuação de processo);
- total de 103.

Por isso o motor funciona assim: a fila do SGA entra por regra, e o que está fora da fila só entra por decisão do operador, com justificativa registrada. **O operador continua no comando**; o motor organiza, confere e registra.

## 6. Alertas: onde o motor pede decisão

O motor não exclui nada sozinho. Ele levanta alertas e o operador decide incluir ou excluir.

| Código | Quando aparece | Por que importa |
|---|---|---|
| A1 | Protocolo com formato estranho (8 ou 9 dígitos, ou ano muito antigo) | Caso fora do padrão citado na reunião de 30/09 |
| A2 | Custo do evento zero ou negativo | Participação lançada antes de ser paga |
| A3 | Sem participação e custo baixo (abaixo de R$ 500) | Padrão estranho citado na reunião |
| A4 | Um evento sozinho passa de 10% do total | Concentração |
| A5 | Indenização integral (V.F.I, furto, roubo) | Pesa muito no rateio; confirmar se entra no mês |
| A6 | Data de finalização mudou entre uma foto e outra | Reabertura ou ajuste |

Em setembro todos os alertas já vêm decididos conforme o fechamento real, e a tela mostra "0 pendências, pode homologar".

## 7. Como fica o mês a mês do operador (a tela)

1. **Rodar:** subir dois relatórios exportados do SGA, a base de veículos e a foto de eventos. A tela confere a contagem e a soma com o rodapé do próprio relatório; se não bater, recusa o arquivo.
2. **Seleção:** a fila entra sozinha; o operador decide os alertas e inclui o que precisar (por exemplo, integrais com acordo assinado).
3. **Lançamentos:** o operador digita as linhas de soma e dedução do mês (E-SAÚDE, rastreamento, inadimplência, recuperados, salvados). O motor não calcula essas linhas; elas vêm prontas da operação.
4. **Resultado:** total a ratear, cotas, valor por cota, comparação com outros critérios e as verificações automáticas.
5. **Boletos:** um valor por veículo, com exportação em CSV.

Leitura de 39 mil veículos leva cerca de 5 segundos.

## 8. O que o motor ainda não faz

| Item | Situação |
|---|---|
| Lacre do fechamento (foto travada com SHA-256, estados, trilha de auditoria) | Fase 3, pronta para começar |
| Separar no boleto rateio, fundo de estabilização, taxa de administração e produtos (Res. CNSP 491, art. 70) | Hoje só o rateio é calculado; depende da Mutualiza e do atuário |
| Arquivo de cobrança no layout que o SGA importa | Precisa do layout da AVAP |
| Guardar o histórico mês a mês | Hoje a tela trabalha em memória; vem com a Fase 3 |

O boleto real da AVAP traz só o total da mensalidade, sem separar rateio, taxa e produtos. Por isso o aceite é a planilha de fechamento, não o boleto.

## 9. O que perguntar ao Cícero (só se sobrar espaço)

Nada bloqueia. Ordem sugerida; as três primeiras mudam a operação do mês a mês:

1. **Integrais que ficaram de fora:** 39 integrais finalizados em agosto e setembro, cerca de R$ 1,88 milhão, não entraram em nenhum dos dois meses. Qual o critério? (Acordo não assinado, salvado pendente, adiamento?)
2. **Linha de inadimplência:** como é calculada? (Cotas do mês dos veículos inadimplentes?)
3. **Layout de cobrança:** existe um modelo de arquivo que o SGA importa para gerar os boletos?
4. A linha sem descrição de R$ 129.253,00 em setembro é venda de salvados?
5. Rastreamento é custo da associação ou repasse ao fornecedor?
6. O que significam os sufixos VP, DP, CP e TP nas cotas?
7. Por que o E-SAÚDE aparece 3 vezes em agosto?

O furto 2026819916 (R$ 67.092,44) já está com o presidente da AVAP; não precisa repetir.

### Nunca perguntar

- Quem entra no denominador ou qual o valor por cota: **já respondido** por ele em 07/10.
- Os 3 protocolos de agosto: agosto foi só comparação.
- Qualquer item marcado como DECIDIDO na fonte única. Perguntar de novo algo respondido queima credibilidade.

### Cuidado com o vocabulário

Nós **não temos acesso ao SGA**. Sempre falar "relatório exportado do SGA" ou "a foto de 28/09 que você mandou", nunca "no SGA está assim".

## 10. Perguntas que ele pode fazer, e respostas curtas

**"Como vocês sabem que bate?"**
Reproduzimos a planilha de fechamento de setembro que vocês mandaram: mesmos 103 protocolos, mesmo total, mesmo valor por cota. Há um teste automático que refaz essa conta a cada mudança no código.

**"E se eu quiser incluir um evento que não está na fila?"**
Inclui na aba Seleção, com justificativa. Foi exatamente o que aconteceu com 24 eventos em setembro.

**"O sistema exclui evento sozinho?"**
Não. Ele só alerta. Quem decide é o operador, e a decisão fica registrada.

**"E a inadimplência?"**
Veículo inadimplente fica fora do denominador; a perda volta pela linha INADIMPLÊNCIA, e o que for recuperado volta como dedução no mês seguinte. Do jeito que vocês já fazem.

**"Por que a soma dos boletos dá R$ 13,25 a menos?"**
Arredondamento no centavo de 22.530 boletos. O sistema mostra a sobra e não joga em ninguém.

**"Os dados estão seguros?"**
Os arquivos reais da AVAP ficam só no nosso servidor e fora do repositório de código. Para apresentação pública usamos uma base fictícia, com protocolos, placas, nomes e matrículas trocados.

**"Funciona para outubro?"**
Sim, é o mesmo processo: os dois relatórios do fechamento de outubro mais as linhas de soma e dedução. A proposta é rodar outubro em paralelo ao fechamento de vocês e comparar.

**"E a SUSEP / Res. 491?"**
O motor já separa o rateio do resto; falta definir com a Mutualiza e o atuário os valores de estabilização, taxa de administração e produtos para o boleto sair discriminado, como a norma pede.

## 11. Demonstração ao vivo

- **Com o Cícero:** usar a aba "AVAP · Rateio em pote único", botão "Demonstração 09/2026". São os dados reais da própria AVAP, e é isso que prova a diferença zero.
- **Em público (Fenaprove, 18 e 19/11):** usar a aba "Fenauto · Demonstração", dados fictícios.
- Endereço: http://72.61.59.127:5174 (o servidor precisa estar no ar).

## 12. Proposta de próximo passo para levar

1. **Outubro em paralelo:** a AVAP fecha outubro como sempre, nos manda os mesmos arquivos, e comparamos o resultado do motor. Segundo mês com diferença zero consolida o aceite.
2. **Lacre (Fase 3):** fechamento travado, com histórico e trilha de auditoria.
3. **Layout de cobrança:** com o modelo do SGA, o motor passa a devolver o arquivo pronto para importar.

## 13. Glossário rápido

| Termo | Significado |
|---|---|
| Cota | Peso do veículo no rateio: 1 cota a cada R$ 5 mil de FIPE |
| Pote único | Todos dividem o mesmo total, sem categorias |
| Evento | Sinistro registrado (colisão, furto, roubo, etc.) |
| V.F.I | Indenização integral do veículo (perda total) |
| Integral | V.F.I, furto ou roubo: o veículo é indenizado por inteiro |
| Participação | Parte do custo paga pelo próprio associado (franquia) |
| Salvado | Veículo indenizado que a associação vende; a venda vira dedução |
| Continuação de processo | Evento que continua um anterior (complemento de reparo) |
| Foto | Relatório exportado do SGA em uma data (28/09, 30/09) |
| Fila | Eventos com `Valor Rateado` = 0,00 no relatório, prontos para ratear |
| Linha de soma / dedução | Valores sem placa que entram ou saem do total a ratear |
| Fechamento | A planilha final do mês com eventos e linhas; é o aceite |
| Lacre | Trava do fechamento com assinatura digital (SHA-256), para ninguém alterar depois |
