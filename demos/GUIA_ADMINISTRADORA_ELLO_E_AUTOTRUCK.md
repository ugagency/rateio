# Guia da administradora: operar o rateio no ELLO e no AutoTruck

Documento unico de apoio para a administradora que acompanha mais de uma
associacao na mesma plataforma. Cada associacao roda em um motor de rateio
proprio. Hoje a plataforma oferece dois produtos:

1. ELLO, Rateio e Faturamento.
2. AutoTruck, Modelo Ello retreinado.

Este guia mostra como proceder em cada um e, ao final, resume as diferencas
entre os dois rateios. Para o detalhamento completo de colunas de cada planilha,
consulte os guias especificos de cada produto, que acompanham os respectivos
kits de teste.

---

## 1. Acesso comum aos dois produtos

O acesso e o mesmo para os dois. O que muda e o produto selecionado no topo da
tela.

1. Abra o navegador atualizado (Google Chrome, Microsoft Edge ou Mozilla
   Firefox).
2. Acesse o endereco:

       http://72.61.59.127:5174

3. Use `http://` e nao `https://`. Trata-se de um ambiente de teste interno.
4. No topo da tela existe a faixa "Produto", com os botoes ELLO e AutoTruck.
   Selecione o produto da associacao que voce vai analisar. Voce pode alternar
   entre eles a qualquer momento, sem perder o acesso.

Conceito geral, valido nos dois produtos: voce envia planilhas de entrada na
aba "Rodar Mes", a plataforma calcula e preenche as demais telas. O selo central
de confianca, nos dois motores, e o Invariante de auditoria, que deve fechar em
R$ 0,00.

---

## 2. Como proceder no ELLO

### 2.1. Arquivos de entrada (3 planilhas)

1. `veiculos_completo.xlsx`: cadastro de veiculos elegiveis.
2. `eventos_cobre.xlsx`: sinistros pendentes do mes.
3. `servicos.xlsx`: produtos fixos por veiculo.

### 2.2. Passo a passo

1. Selecione o produto ELLO.
2. A tela inicia em branco. Isso e proposital: o painel so se preenche depois
   que voce roda o rateio. Ela volta a ficar em branco se a pagina for
   recarregada.
3. Va na aba "Rodar Mes".
4. Envie as 3 planilhas (Veiculos, Eventos, Servicos). A validacao acontece na
   selecao, com selo verde para arquivo correto e vermelho para arquivo no campo
   errado.
5. Confira o mes de referencia e calcule.
6. Use o botao para abrir a Visao Geral.

### 2.3. Leitura das telas

1. Visao Geral: mostra o Alvo do mes, o numero de veiculos elegiveis, as cotas
   apuradas e os eventos alocados.
2. Potinhos: mostra o motor dividido em quatro grupos de risco (P1 Roubo e
   Furto, P2 Moto FIP, P3 Venture 1, P4 Venture 2), com o valor de cada grupo e
   o degrau por cota.
3. Eventos: lista cada sinistro processado, com status Liquidado ou Parcial.
4. Boletos: valor por veiculo, somando rateio e servicos fixos.
5. Auditoria: consulta a composicao do valor de um veiculo informado.

Ponto central do ELLO: o Alvo do mes e levantado a partir da base de
associados, porque cada cota de cada categoria paga um valor fixo (o degrau).
Se voce retira veiculos de uma categoria, o Alvo cai de forma proporcional ao
degrau daquela categoria.

---

## 3. Como proceder no AutoTruck

### 3.1. Arquivos de entrada (3 planilhas)

1. `BASE_completa.xlsx`: cotas adimplentes e inadimplentes por segmento. E o denominador.
2. `RATEIO_completo.xlsx`: eventos sinistrados do mes. E o numerador.
3. `PRODUTOS.xlsx`: catalogo de fornecedor. Opcional e informativo.

Os segmentos sao LEVES (automoveis), MOTOS e PESADOS (caminhoes). A cota
variavel se aplica a LEVES e MOTOS. Eventos de terceiros sao rastreados em
separado e nao abatem a cota dos associados.

### 3.2. Passo a passo

1. Selecione o produto AutoTruck.
2. Va na aba "Rodar Mes".
3. Envie os 3 arquivos (BASE, RATEIO, PRODUTOS), conferindo os selos de
   validacao.
4. Confira o mes de referencia, que e apenas um carimbo, e calcule.
5. Use o botao para abrir a Visao Geral.

### 3.3. Leitura das telas

1. Visao Geral: Invariante de auditoria, cota por segmento, eventos alocados,
   reclassificacao pela regra dos 75 por cento, e os valores fixos de reserva
   (caminhao e terceiros).
2. Segmentos: custo a ratear, cotas adimplentes e valor da cota de cada
   segmento, alem da recuperacao de terceiros.
3. Eventos: lista de eventos com segmento, envolvimento, tipo e valor rateado.
4. Ajuste: assistente para simular alvos e variacoes antes de consolidar.
5. Boletos: valor por cota.
6. Auditoria: trilha imutavel das operacoes, voltada a LC 213.

Ponto central do AutoTruck: a cota e o resultado do calculo. O custo dos
eventos do mes e dividido pelas cotas adimplentes do segmento. Com o mesmo
custo, menos adimplentes significam cota maior.

---

## 4. Resumo das diferencas entre os dois rateios

O quadro abaixo concentra o essencial. Os dois motores fecham o Invariante de
auditoria em R$ 0,00, mas chegam la por caminhos diferentes.

Tema                         | ELLO                                            | AutoTruck
-----------------------------|-------------------------------------------------|------------------------------------------------
Sentido do calculo           | De baixo para cima: o Alvo e levantado da base  | De cima para baixo: o custo do mes gera a cota
Como nasce a cota            | Degrau fixo por categoria (valor por cota)      | Cota variavel, igual ao custo dividido pelos adimplentes
O que move o resultado       | Quantidade de veiculos por categoria            | Custo dos eventos e numero de adimplentes
Segmentacao                  | 4 grupos de risco (potinhos P1 a P4)            | 3 segmentos (LEVES, MOTOS, PESADOS)
Denominador                  | Veiculos elegiveis e suas cotas                 | Apenas cotas adimplentes (BAIXADO)
Arquivos de entrada          | Veiculos, Eventos, Servicos                     | BASE, RATEIO, Produtos (opcional)
Tratamento de terceiros      | Nao se aplica de forma destacada                | Rastreados em separado, nao abatem a cota
Saldo entre meses            | Existe saldo para o proximo mes                 | Rateia o custo do mes corrente
Regras especiais             | Categorias e degraus por tipo de risco          | Regra dos 75 por cento, estabilizacao trimestral, valores fixos de reserva
Tela inicial                 | Inicia em branco ate rodar o rateio             | Comportamento padrao, sem tela em branco
Selo de confianca            | Invariante Alvo contra alocado igual a R$ 0,00  | Invariante de auditoria igual a R$ 0,00

Leitura pratica da diferenca:

1. No ELLO, se voce mexe na base de associados, muda o Alvo do mes, porque cada
   cota paga um valor fixo. O foco e cobrir o Alvo com os eventos e o saldo.
2. No AutoTruck, se voce mexe nos eventos ou no numero de adimplentes, muda a
   cota, porque ela e o custo do mes dividido por quem paga. O foco e distribuir
   o custo real entre os adimplentes de cada segmento.

---

## 5. Resumo rapido

1. Acessar `http://72.61.59.127:5174`.
2. Selecionar o produto da associacao (ELLO ou AutoTruck).
3. Ir em "Rodar Mes" e enviar as planilhas de entrada do produto.
4. Calcular e abrir a Visao Geral.
5. Navegar pelas abas e conferir o Invariante em R$ 0,00.
6. No ELLO, observar o Alvo do mes. No AutoTruck, observar a cota por segmento.

---

## Observacao

Este ambiente de teste (MVP) ficara disponivel por 24 horas a partir da
liberacao do acesso. Apos esse periodo, o endereco pode sair do ar.
