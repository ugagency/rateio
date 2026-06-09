# Guia de acesso e teste da plataforma de Rateio (AutoTruck)

Documento de apoio para a sessao de teste da administradora. Descreve, do
endereco de acesso ate a leitura das telas, como usar o produto AutoTruck,
o Modelo Elo Ajustado, e como validar que o resultado vem de fato dos arquivos
enviados.

Tempo estimado de leitura e execucao: 15 minutos.

---

## 1. Antes de comecar

Requisitos:

1. Um computador com navegador atualizado (Google Chrome, Microsoft Edge ou
   Mozilla Firefox). A plataforma roda inteiramente no navegador, sem instalacao.
2. Conexao de rede que alcance o servidor de teste.
3. Os arquivos de planilha do kit de teste, que acompanham este guia:
   - `BASE_completa.xlsx`
   - `RATEIO_completo.xlsx`
   - `PRODUTOS.xlsx`
   - `BASE_reduzida.xlsx` (usado no teste de validacao opcional)
   - `RATEIO_reduzido.xlsx` (usado no teste de validacao opcional)

Guarde os arquivos em uma pasta de facil acesso no computador, por exemplo a
Area de Trabalho.

---

## 2. Endereco de acesso

Abra o navegador e digite na barra de enderecos:

    http://72.61.59.127:5174

Pressione Enter. A plataforma deve carregar em poucos segundos.

Observacoes importantes:

1. Use `http://` e nao `https://`. Trata-se de um ambiente de teste interno.
2. Se a pagina nao abrir, confirme com a equipe tecnica que o servidor de teste
   esta ligado no momento do acesso.

---

## 3. Selecionar o produto AutoTruck

No topo da tela existe uma faixa escura com o rotulo "Produto" e dois botoes:

1. ELLO, Rateio e Faturamento
2. AutoTruck, Modelo Elo Ajustado

Para este teste, clique no botao AutoTruck, Modelo Elo Ajustado. Toda a sessao
acontece dentro desse produto.

---

## 4. Entendendo os tres arquivos de entrada

O AutoTruck calcula o rateio a partir de tres planilhas:

1. BASE: a relacao de cotas por segmento, separadas entre adimplentes e
   inadimplentes. E o denominador, ou seja, quem divide o custo do mes.
2. RATEIO: os eventos sinistrados do mes. E o numerador, ou seja, o custo que
   sera rateado.
3. PRODUTOS: o catalogo de fornecedor. E opcional e apenas informativo, nao
   entra no calculo da cota.

Os tres segmentos sao LEVES (automoveis), MOTOS e PESADOS (caminhoes). A cota
variavel se aplica a LEVES e MOTOS. Os eventos de terceiros sao rastreados em
separado e nao abatem a cota dos associados.

---

## 5. Rodar o primeiro rateio

1. Clique na aba "Rodar Mes".
2. A tela mostra os campos de envio de arquivo:
   - BASE, pagamentos recebidos e pendentes
   - RATEIO, eventos sinistrados do mes
   - PRODUTOS, catalogo fornecedor (opcional)
3. No campo BASE, selecione `BASE_completa.xlsx`.
4. No campo RATEIO, selecione `RATEIO_completo.xlsx`.
5. No campo PRODUTOS, selecione `PRODUTOS.xlsx`.
6. A cada selecao, a plataforma valida o arquivo na hora e mostra um selo:
   - Selo verde indica que o arquivo e do tipo correto.
   - Selo vermelho indica que o arquivo foi colocado no campo errado. Nesse caso,
     refaca a selecao no campo adequado.
7. Confira o campo de mes de referencia. Pode usar 05/2026. O mes e apenas um
   carimbo e nao altera os valores, que vem dos arquivos.
8. Clique no botao para calcular.

Apos alguns instantes, aparece o resultado processado. Para examinar em detalhe,
use o botao que abre a Visao Geral. A plataforma leva voce ao painel preenchido.

---

## 6. Como ler cada aba

### 6.1. Visao Geral

E o resumo do mes. Os principais indicadores:

1. Invariante de auditoria: a diferenca entre o total a ratear e o total
   alocado. Deve ser sempre R$ 0,00. E o principal selo de confianca do calculo.
2. Cota por segmento: o valor que cada cota de LEVES e de MOTOS paga no mes.
3. Eventos alocados: a quantidade de eventos considerados no mes, com os
   postergados informados a parte.
4. Reclassificacao pela regra dos 75 por cento: eventos parciais que viraram
   perda total por ultrapassar o limite de reparo.
5. Valor fixo de caminhao e de terceiros: reservas controladas em separado.

### 6.2. Segmentos

Detalha cada segmento, LEVES, MOTOS e PESADOS, com o custo a ratear, o numero de
cotas adimplentes e o valor da cota. Tambem mostra a recuperacao de terceiros,
que e rastreada mas nao abate a cota dos associados.

### 6.3. Eventos

Lista cada evento sinistrado do mes, com segmento, envolvimento (associado ou
terceiro), tipo (integral ou parcial) e o valor rateado. E onde se confere, um a
um, o que foi lido do arquivo de RATEIO.

### 6.4. Ajuste

Espaco do assistente de ajuste, que permite simular alvos e variacoes antes de
consolidar. Para o teste inicial, pode ser apenas visualizado.

### 6.5. Boletos

Apresenta, por cota, o valor de boleto resultante, somando a parcela de rateio e
os itens aplicaveis. Ha filtro por segmento.

### 6.6. Auditoria

Mostra a trilha de auditoria, o registro imutavel das operacoes, voltado ao
cumprimento da LC 213. Se nenhuma intervencao manual foi feita, a tela informa
isso de forma explicita.

---

## 7. Prova de que o resultado vem dos arquivos

Para confirmar que a plataforma le os arquivos de verdade e nao exibe numeros
fixos, compare o resultado com os valores esperados do kit.

Com `BASE_completa.xlsx`, `RATEIO_completo.xlsx` e `PRODUTOS.xlsx`, o resultado
correto e:

1. Cota MOTOS: R$ 20,00
2. Cota LEVES: R$ 60,00
3. Custo a ratear MOTOS: R$ 40.000,00
4. Custo a ratear LEVES: R$ 60.000,00
5. Eventos alocados: 7
6. Invariante de auditoria: R$ 0,00

Teste adicional 1, mover a cota. Volte a aba "Rodar Mes", troque apenas o campo
BASE por `BASE_reduzida.xlsx` e mantenha os demais. Calcule novamente. A cota de
MOTOS deve dobrar, de R$ 20,00 para R$ 40,00, porque o mesmo custo passa a ser
dividido pela metade dos motociclistas adimplentes. A cota de LEVES permanece em
R$ 60,00.

Teste adicional 2, mover o custo a ratear. Volte a `BASE_completa.xlsx` e troque
apenas o campo RATEIO por `RATEIO_reduzido.xlsx`. Calcule novamente. O custo a
ratear de MOTOS cai de R$ 40.000,00 para R$ 30.000,00, a cota de MOTOS cai de
R$ 20,00 para R$ 15,00, e os eventos lidos caem de 7 para 6.

Esse comportamento demonstra que o resultado acompanha o conteudo real das
planilhas enviadas.

---

## 8. Pontos de atencao

1. O campo de mes e apenas um carimbo. Os numeros vem dos arquivos enviados.
2. Mantenha os tres arquivos no campo correto. Se o selo ficar vermelho, o
   arquivo esta no campo errado e o calculo nao prossegue.
3. Em caso de qualquer falha de acesso ou comportamento inesperado, registre o
   horario e a tela em que ocorreu e encaminhe a equipe tecnica.

---

## 9. Resumo rapido

1. Acessar `http://72.61.59.127:5174`.
2. Selecionar o produto AutoTruck.
3. Ir em "Rodar Mes".
4. Enviar os 3 arquivos: BASE, RATEIO e PRODUTOS.
5. Calcular e abrir na Visao Geral.
6. Navegar pelas abas e conferir que o Invariante esta em R$ 0,00.
