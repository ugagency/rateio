# Especificação de Insumos para a Geração do Rateio

## Objetivo

Para que a plataforma gere o rateio mensal de forma automática, é necessário
receber, a cada mês, um conjunto padronizado de planilhas. Este documento
especifica o conteúdo, o formato e as regras de preenchimento de cada arquivo, de
modo a permitir a construção de um processo interno recorrente na AutoTruck,
preferencialmente por exportação direta do sistema SGA, sem digitação manual.

A leitura da plataforma foi construída sobre o layout atualmente utilizado pela
AutoTruck. Os exemplos apresentados a seguir são recortes reais dos arquivos BASE e
RATEIO já fornecidos. Não se trata de um novo formato, e sim da geração recorrente
do mesmo padrão, mês a mês.

A plataforma valida automaticamente cada arquivo no momento do envio, conferindo a
assinatura do layout e sinalizando caso um arquivo seja enviado no campo incorreto.

## 1. Visão geral do pacote mensal

| Nº | Arquivo | Conteúdo | Obrigatório |
|---|---|---|---|
| 1 | BASE | Cotas e boletos por situação (baixado, aberto, cancelado), por segmento | Sim |
| 2 | RATEIO | Lista dos eventos (sinistros) do mês a serem rateados | Sim |
| 3 | PRODUTOS | Catálogo de produtos e serviços por fornecedor | A definir (ver seção 6) |

Padrões gerais, válidos para os três arquivos:

- Formato: Excel (.xlsx). Pode ser exportado do SGA ou de planilha equivalente.
- Periodicidade: mensal, referente ao mês de fechamento.
- Mês de referência: formato MM/AAAA, por exemplo 06/2026.
- Segmentos: sempre três, sendo LEVES, MOTOS e PESADOS.
- Datas no formato dd/mm/aaaa. Valores em reais, admitindo vírgula como separador decimal.
- Nomenclatura sugerida: BASE_AAAAMM.xlsx, RATEIO_AAAAMM.xlsx, PRODUTOS_AAAAMM.xlsx,
  por exemplo BASE_202606.xlsx.

## 2. Arquivo BASE: cotas e boletos por situação

É o insumo mais crítico, pois dele se obtém o denominador do rateio, ou seja, o
número de cotas que efetivamente dividem o custo. A estrutura é a mesma do relatório
"Valor/Cota por Situação de Boleto" já gerado pelo sistema, com os três segmentos
(PESADO, MOTO e LEVE) dispostos lado a lado.

<!--PRINT_BASE-->

### Informações que a plataforma extrai

| Informação | Origem | Utilização |
|---|---|---|
| Cotas BAIXADAS por segmento | Coluna BAIXADO de "Cota por Situação" | Denominador do rateio (cota igual a custo dividido pelas cotas baixadas) |
| Cotas ABERTAS por segmento | Coluna ABERTO de "Cota por Situação" | Informativo (inadimplência) |
| Boletos baixados e abertos | "Quantidade de Boletos" | Informativo e conferência |
| Valor recebido e inadimplência | "Resumo de Boletos" | Conferência financeira |

Observação importante. A plataforma utiliza a coluna BAIXADO, que representa as
cotas efetivamente pagas, e não a coluna TOTAL. No relatório, TOTAL e BAIXADO
divergem por definição: TOTAL corresponde ao valor nominal de tabela, enquanto
BAIXADO corresponde ao valor efetivamente cobrado e pago. O rateio deve ser
calculado sobre as cotas pagas. No print, as colunas BAIXADO aparecem destacadas.

Nota de leitura. Algumas células do bloco LEVE são exibidas como "#####" em razão da
largura de coluna no arquivo de origem. O valor existe e não afeta o cálculo, uma
vez que o denominador é obtido das contagens de cotas, localizadas em outro bloco da
planilha.

## 3. Arquivo RATEIO: eventos do mês

Lista dos sinistros ou eventos que entram no rateio, com uma linha por evento,
agrupados por marcador de seção (segmento e envolvimento) na coluna A.

<!--PRINT_RATEIO-->

### Organização da planilha

- A coluna A funciona como marcador de seção, combinando segmento e envolvimento,
  por exemplo PESADOS TERCEIROS, MOTOS ASSOCIADOS ou LEVES ASSOCIADOS.
  - ASSOCIADOS indica evento que representa custo do grupo, e portanto entra na conta.
  - TERCEIROS indica recuperação, ou seja, valor a receber de terceiro, destinado ao
    pote de Danos a Terceiros.
- A coluna B traz o tipo da indenização, INTEGRAL ou PARCIAL.

### Colunas por linha de evento (layout atual)

| Coluna | Campo | Obrigatório | Observação |
|---|---|---|---|
| A | Marcador de seção | Sim | Define segmento e envolvimento (associado ou terceiro) |
| B | Tipo de indenização | Sim | Contém "INTEGRAL" ou "PARCIAL" |
| Protocolo | Protocolo | Sim | Identificador do sinistro |
| Motivo | Motivo | Desejável | Descrição |
| Placa | Placa | Sim | Identificação do veículo |
| Data Comunic | Data de aviso | Sim | dd/mm/aaaa, define a ordem FIFO |
| Valor Rateado | Valor rateado | Sim | Valor do evento em reais, maior que zero (coluna destacada no print) |

### Regras de preenchimento

- INTEGRAL (perda total): o valor rateado corresponde ao valor cheio do evento.
- PARCIAL (reparo): o valor rateado corresponde ao custo de oficina ou orçamento.
- Toda linha de evento exige Protocolo e Valor rateado maior que zero; caso
  contrário, a linha é ignorada.
- O marcador da coluna A é o que define à plataforma o segmento do evento e se ele
  representa custo (ASSOCIADOS) ou recuperação (TERCEIROS).

## 4. Como a plataforma utiliza cada insumo

1. A BASE determina quantas cotas pagantes existem por segmento, compondo o denominador.
2. O RATEIO fornece os custos dos eventos por segmento, sobre os quais o motor aplica
   as regras de cálculo (regra dos 75% de perda total, ordem FIFO por data,
   segregação dos pesados em valor fixo e recuperação de terceiros em pote à parte).
3. O cálculo da cota é dado por custo total a ratear dividido pelas cotas baixadas,
   por segmento.
4. A plataforma gera os boletos e o consolidado do mês, com trilha de auditoria e o
   invariante de fechamento (custo apurado menos custo alocado igual a zero).

## 5. Integração direta com o sistema SGA

A entrega manual de planilhas descrita acima corresponde ao modo de operação atual.
A plataforma, contudo, já foi projetada para integrar-se diretamente ao SGA. A
arquitetura, o contrato de dados e o pipeline de fechamento já estão implementados e
cobertos por testes automatizados. Quando o endpoint do SGA estiver disponível, a
substituição do arquivo pela chamada de API não exige alteração no motor de rateio.

### Contrato único de ingestão

Toda a ingestão ocorre por meio de um contrato único, denominado FonteRateio. O motor
de rateio não depende da origem dos dados; a única operação que ele executa é a
chamada do método de carregamento. Por esse motivo, a integração constitui um
encaixe, e não uma reformulação do sistema.

```python
# backend/app/autotruck/fontes.py
@runtime_checkable
class FonteRateio(Protocol):
    """Contrato único de ingestão. carregar() devolve a base do mês."""
    nome: str
    def carregar(self) -> tuple[list[VeiculoAT], list[EventoAT], dict]:
        # (veículos, eventos, metadados do mês)
        ...
```

### Implementações já presentes no código

| Fonte de dados | Estado | Papel |
|---|---|---|
| Arquivo de fechamento (FonteFechamentoXlsx) | Em produção | Caminho manual atual, correspondente às planilhas deste documento |
| Conector SGA via API (FonteSGAHttp) | Implementado, aguardando endpoint | Adaptador dedicado; depende apenas da disponibilização do endpoint do SGA |
| Memória (FonteMemoria) | Em uso nos testes | Garante, em teste automatizado, que a troca de fonte não altera o resultado |

Observação técnica. O adaptador de integração com o SGA já existe como componente do
sistema, com interface definida e cobertura por teste automatizado que comprova a
independência do motor de rateio em relação à origem dos dados. Trata-se de componente
existente, cuja ativação depende exclusivamente da disponibilização do endpoint pela
AutoTruck, não constituindo item de planejamento futuro.

### O que muda e o que permanece ao ativar a integração

```
Atual:  SGA  ->  exportação de planilha  ->  envio manual  ->  FonteFechamentoXlsx  ->  Motor de Rateio
Futuro: SGA  ->  API autenticada  ------------------------->  FonteSGAHttp         ->  Motor de Rateio (idêntico)
```

- Permanecem inalterados: o motor de rateio, as regras (75%, FIFO, potes), a
  auditoria, o fechamento de D+0 a D+5, o invariante e a geração de boletos. Todo o
  processamento posterior ao contrato permanece igual.
- Altera-se apenas a origem dos dados, que deixa de ser um arquivo e passa a ser uma
  chamada autenticada à API do SGA, eliminando a entrega manual mensal.

### Requisitos para ativação, a serem fornecidos pelo SGA

Para implementar o conector, a plataforma depende de informações que apenas o SGA
pode fornecer:

1. Especificação do endpoint: URL, método, autenticação (token ou credenciais) e
   formato da resposta (JSON ou relatório).
2. Campos por registro, os mesmos já consumidos pelo motor: Placa, Valor FIPE,
   Status de pagamento em D+0, Data de aviso do sinistro, Status de liquidação do
   salvado, Tipo e Envolvimento do evento.
3. Desejável: a base de veículos no mesmo retorno, com FIPE e status de pagamento por
   veículo. Com esses dados, obtém-se o denominador purista de forma automática
   (cotas de veículos ativos e pagos), dispensando a BASE manual descrita na seção 2.

Em síntese, do lado da plataforma, integrar ao SGA significa implementar um componente
já previsto, e não refazer o sistema. O que resta é a especificação da API do SGA.

## 6. Ponto em aberto para decisão: arquivo PRODUTOS

É necessário alinhar com a AutoTruck, na condição de responsável pelo processo, como
tratar o arquivo de PRODUTOS, pois há hoje um descasamento que pode gerar expectativa
incorreta.

Situação atual. O arquivo PRODUTOS é lido apenas como catálogo de referência. A
plataforma contabiliza quantos itens ele contém, mas não utiliza os valores das
colunas de preço no cálculo do rateio. Em consequência, hoje, alterar o valor de um
produto nesse arquivo não altera o rateio nem o boleto.

Os valores que de fato entram no cálculo têm outras origens:

| Valor | Origem atual | Alterável por planilha |
|---|---|---|
| Custo de cada evento | Coluna "Valor rateado" do RATEIO | Sim |
| Preço de Danos a Terceiros (50k e 100k) | Parâmetro interno do motor | Não (configuração) |
| Valor fixo do casco caminhão | Parâmetro interno do motor | Não (configuração) |
| Cotas por faixa de valor (FIPE) | Parâmetro interno do motor | Não (configuração) |
| Serviços adicionais (assistência 24h, vidros) | Campo do veículo | Existe no modelo, porém hoje não é alimentado por planilha |

Decisão a tomar com a AutoTruck: como o preço dos produtos e serviços deve chegar ao
boleto?

- Opção A: o arquivo PRODUTOS permanece como referência e não afeta o rateio. Nesse
  caso, mantém-se o comportamento atual e a definição fica explícita no processo.
- Opção B: o preço dos produtos e serviços (assistências, vidros, rastreador,
  terceiros por faixa) deve valer no boleto a partir de uma planilha mantida pela
  AutoTruck. Nesse caso, trata-se de uma evolução a desenvolver, que consiste em
  associar as colunas de preço (do PRODUTOS ou de uma nova tabela de preços) aos
  serviços e coberturas de cada veículo e ao boleto.

Enquanto essa definição não for tomada, o arquivo PRODUTOS permanece opcional e
tratado como informativo.

## 7. Checklist de entrega mensal

A cada fechamento, a AutoTruck fornece:

- BASE do mês, contendo as cotas baixadas por segmento (LEVES, MOTOS e PESADOS).
- RATEIO do mês, com os eventos contendo Protocolo, Placa, Data, Tipo
  (INTEGRAL ou PARCIAL) e Valor rateado, agrupados por marcador de segmento e
  envolvimento.
- PRODUTOS, conforme a definição da seção 6.
- Todos os arquivos em formato .xlsx, nomeados TIPO_AAAAMM.xlsx e referentes ao
  mesmo mês.

### Processo interno sugerido

1. Origem única: exportar BASE e RATEIO diretamente do SGA, evitando digitação e erro
   de transcrição, a partir do mesmo relatório já utilizado internamente.
2. Conferência antes do envio: verificar se as cotas baixadas de cada segmento na BASE
   conferem com o relatório do mês e se a soma dos valores rateados no RATEIO confere
   com o total de eventos do mês.
3. Canal e prazo: definir um dia útil fixo do mês para a entrega e um canal único.
4. Versionamento: havendo correção, reenviar o arquivo completo com sufixo de versão,
   por exemplo BASE_202606_v2.xlsx, sem editar parcialmente o arquivo anterior.

## Síntese

A cada mês, a entrega da BASE (cotas baixadas por segmento) e do RATEIO (eventos com
valor, tipo, data e segmento), no layout já em uso, permite que a plataforma gere o
rateio completo. A plataforma já está preparada para integrar-se diretamente ao SGA,
conforme a seção 5, o que elimina a entrega manual. O único ponto pendente de decisão
é o papel do arquivo PRODUTOS, conforme a seção 6.
