# Guia de acesso e teste da plataforma de Rateio (ELLO)

Documento de apoio para a sessão de teste da administradora. Descreve, do
endereço de acesso até a leitura das telas, como usar a plataforma e como
validar que o resultado vem de fato dos arquivos enviados.

---

## 1. Antes de começar

Requisitos:

1. Um computador com navegador atualizado (Google Chrome, Microsoft Edge ou
   Mozilla Firefox). A plataforma roda inteiramente no navegador, sem instalação.
2. Conexão de rede que alcance o servidor de teste.
3. Os 3 arquivos de planilha do kit de teste, que acompanham este guia:
   - `veiculos_completo.xlsx`
   - `eventos_cobre.xlsx`
   - `servicos.xlsx`

Guarde os 3 arquivos em uma pasta de fácil acesso no computador, por exemplo a
Área de Trabalho.

---

## 2. Endereço de acesso

Abra o navegador e digite na barra de endereços:

    http://72.61.59.127:5174

Pressione Enter. A plataforma deve carregar em poucos segundos.

Observações importantes:

1. Use `http://` e não `https://`. Trata-se de um ambiente de teste interno.
2. Se a página não abrir, confirme com a equipe técnica que o servidor de teste
   está ligado no momento do acesso.

---

## 3. Selecionar o produto

No topo da tela existe uma faixa escura com o rótulo "Produto" e dois botões:

1. ELLO, Rateio e Faturamento
2. AutoTruck, Modelo Ello retreinado

Para este teste, mantenha selecionado o botão ELLO, Rateio e Faturamento. Ele já
vem marcado por padrão. O segundo produto pertence a outro contexto e não deve
ser usado nesta sessão.

---

## 4. Entendendo a tela inicial em branco

Logo abaixo do cabeçalho existe um menu com as abas:

Visão Geral, Potinhos, Eventos, Boletos, Auditoria, Rodar Mês.

À direita do menu há um campo "Mês" preenchido com `05/2026`.

Ao abrir, a plataforma começa intencionalmente vazia. As abas exibem a mensagem
"Nenhum rateio nesta sessão". Isso é o comportamento esperado e proposital: a
tela só apresenta números depois que o próprio usuário enviar as planilhas e
solicitar o cálculo. Assim, fica claro que nada está pré-carregado ou simulado.

Para preencher a tela, siga para o passo 5.

---

## 5. Rodar o primeiro rateio

1. Clique na aba "Rodar Mês".
2. A tela mostra três campos de envio de arquivo, cada um com a descrição das
   colunas esperadas:
   - Veículos, cadastro elegível
   - Eventos, sinistros pendentes
   - Serviços fixos, produtos por veículo
3. No campo Veículos, clique no botão de seleção de arquivo e escolha
   `veiculos_completo.xlsx`.
4. No campo Eventos, selecione `eventos_cobre.xlsx`.
5. No campo Serviços fixos, selecione `servicos.xlsx`.
6. A cada seleção, a plataforma valida o arquivo na hora e mostra um selo de
   confirmação ao lado do nome:
   - Selo verde com o texto "detectado" indica que o arquivo é do tipo correto.
   - Selo vermelho indica que o arquivo foi colocado no campo errado. Nesse caso,
     refaça a seleção no campo adequado.
7. Confira que o campo "Mês de referência" está com `05/2026`.
8. Clique no botão "Calcular Rateio".

Após alguns instantes, aparece um cartão "Resultado processado" com o resumo do
cálculo. Para examinar tudo em detalhe, clique no botão "Abrir na Visão Geral".
A plataforma leva você de volta ao painel, agora preenchido.

Observação: enquanto os 3 arquivos não forem selecionados, ou se algum estiver
no campo errado, a plataforma exibe um aviso e não realiza o cálculo. Isso é
proposital, para evitar processamento com dados incompletos.

---

## 6. Como ler cada aba

### 6.1. Visão Geral

É o resumo do mês. Os principais números:

1. Alvo do mês: o valor total a ser rateado entre os veículos no mês. É o número
   de maior destaque na tela.
2. Veículos: quantidade de veículos elegíveis considerados no cálculo.
3. Cotas: total de cotas apuradas. Cada veículo contribui com uma ou mais cotas.
4. Eventos: quantidade de eventos, sinistros, alocados no mês.

### 6.2. Potinhos

Mostra o motor de rateio dividido em quatro grupos de risco, os "potinhos":

1. P1, Roubo e Furto
2. P2, Moto FIP
3. P3, Venture 1
4. P4, Venture 2

Para cada grupo, a tela apresenta o valor acumulado e o degrau por cota, ou seja,
quanto cada cota daquele grupo contribui. A soma dos quatro potinhos compõe o
Alvo do mês visto na Visão Geral.

### 6.3. Eventos

Lista cada evento, sinistro, processado no mês, com:

1. Identificador do evento e data de ocorrência.
2. Valor total do evento e saldo pendente antes do rateio.
3. Valor rateado no mês e saldo remanescente após o rateio.
4. Status: Liquidado, quando o evento foi totalmente coberto, ou Parcial, quando
   ainda resta saldo para meses futuros.

### 6.4. Boletos

Apresenta, por veículo, o valor de boleto resultante:

1. Identificador do veículo e categoria de risco.
2. Quantidade de cotas.
3. Valor total do boleto, que soma a parcela de rateio e os serviços fixos.
4. Indicação de geração de boleto, Sim ou Não.

Há um campo de filtro por identificador de veículo para localizar um registro
específico.

### 6.5. Auditoria

Permite inspecionar um veículo individual. Digite o identificador do veículo, por
exemplo no formato `VEI-000001`, e clique em Buscar. A plataforma mostra a
composição do valor daquele veículo: parcela de rateio, serviços fixos e total do
boleto. É a ferramenta para conferir caso a caso.

---

## 7. Prova de que o resultado vem dos arquivos

Para confirmar que a plataforma lê os arquivos de verdade e não exibe números
fixos, é possível comparar o resultado com os valores esperados do kit de teste.

Com os arquivos `veiculos_completo.xlsx`, `eventos_cobre.xlsx` e `servicos.xlsx`,
no mês `05/2026`, o resultado correto é:

1. Veículos elegíveis: 100
2. Cotas apuradas: 100
3. Alvo do mês: R$ 2.010,00
   - P1 Roubo e Furto: R$ 1.400,00
   - P2 Moto FIP: R$ 160,00
   - P3 Venture 1: R$ 360,00
   - P4 Venture 2: R$ 90,00
4. Eventos alocados: 2
5. Invariante, diferença entre alvo e alocado: R$ 0,00

O indicador "Invariante" igual a R$ 0,00 é a verificação central de integridade.
Significa que todo o valor calculado foi distribuído sem sobra nem falta. É o
principal selo de confiança do cálculo.

Teste adicional, opcional, para reforçar a confiança:

1. Volte à aba "Rodar Mês".
2. No campo Veículos, troque o arquivo por `veiculos_reduzido.xlsx`, que contém
   10 veículos a menos. Mantenha os demais arquivos.
3. Calcule novamente.
4. O Alvo do mês deve cair de R$ 2.010,00 para R$ 1.870,00, exatamente R$ 140,00
   a menos, pois foram retirados 10 veículos que contribuíam com R$ 14,00 cada no
   grupo de Roubo e Furto.

Esse comportamento demonstra que o resultado acompanha o conteúdo real das
planilhas enviadas.

---

## 8. Pontos de atenção

1. A plataforma volta a ficar em branco se a página for recarregada ou reaberta.
   Isso é proposital. Para ver os números novamente, basta repetir o passo 5.
2. O campo "Mês" no cabeçalho deve permanecer em `05/2026` para que os números do
   kit de teste correspondam aos valores esperados.
3. Em caso de qualquer falha de acesso ou comportamento inesperado, registre o
   horário e a tela em que ocorreu e encaminhe à equipe técnica.

---

## 9. Resumo rápido

1. Acessar `http://72.61.59.127:5174`.
2. Manter o produto ELLO selecionado.
3. Ir em "Rodar Mês".
4. Enviar os 3 arquivos: veículos, eventos e serviços.
5. Clicar em "Calcular Rateio" e abrir na Visão Geral.
6. Navegar pelas abas e conferir que o Invariante está em R$ 0,00.

---

## Observacao

Este ambiente de teste (MVP) ficara disponivel por 24 horas a partir da
liberacao do acesso. Apos esse periodo, o endereco pode sair do ar.
