# ADR-003 — Semântica da BASE: o denominador é a soma de cotas

Status: aceito. Data: 2026-05-29. Resolve o ponto P3 da revisão de UI.

## Contexto

A revisão apontou uma divergência: o app calcula a cota por veículo de forma
fracionária (progressão por FIPE, passos de 0,5, conforme ADR-002 C5), mas o
arquivo BASE carrega a coluna BAIXADO, que o motor consome como contagem inteira
de cotas (o caminho de ingestão por arquivo sintetiza veículos de 1 cota a
partir de um inteiro). Para dados reais, somas fracionárias seriam truncadas.

## Fato verificado no motor

O motor aprovado lida nativamente com cotas fracionárias quando recebe veículos
reais com FIPE (caminho de fonte por objeto, não por arquivo). Teste executado
sobre `engine.calcular_rateio_at` com FIPE variado:

- cotas por veículo 1,0 / 3,0 / 5,5 / 13,0 / 20,0, soma 42,5
- denominador apurado pelo motor = 42,5; cota = custo dividido por 42,5;
  invariante de fechamento igual a zero.

Conclusão: o denominador fracionário é correto e suportado pelo motor. O
truncamento ocorre apenas na ponte por arquivo, que representa o denominador
como número inteiro de cotas (síntese de veículos de 1 cota).

## Identidade contábil que fixa a decisão

O boleto de cada associado é cota por reais vezes a quantidade de cotas do
veículo. Para o rateio arrecadar exatamente o custo, a soma sobre os associados
de (valor da cota vezes quantidade de cotas) tem de igualar o custo a ratear.
Isso só fecha se o denominador for a soma das cotas, não a contagem de veículos.

## Decisão

1. O denominador do rateio é a soma das cotas dos veículos pagos por segmento,
   não a contagem de veículos. A coluna BAIXADO da BASE representa essa soma de
   cotas (idem ABERTO e CANCELADO, informativos).

2. No caminho atual por arquivo, a BASE carrega o valor inteiro mais próximo da
   soma de cotas por segmento (arredondamento da soma), porque a ingestão do
   motor por arquivo representa o denominador como número inteiro de cotas.
   Como as cotas progridem em passos de 0,5, o resíduo de arredondamento por
   segmento é de no máximo 0,5 cota, imaterial frente a denominadores na casa
   das centenas ou milhares. O invariante permanece igual a zero, pois o motor
   é consistente sobre o inteiro que recebe.

3. Quando a integração direta com o SGA estiver ativa (fonte por API,
   `FonteSGAHttp`), o app fornece os veículos reais com FIPE e o denominador
   passa a ser a soma exata das cotas, sem arredondamento. O arredondamento é,
   portanto, uma limitação conhecida e temporária da ponte por arquivo, não do
   modelo.

## Consequências e alinhamento de código

- O gerador da BASE (`lib/export/xlsx.ts`) escreve o inteiro arredondado da
  soma de cotas por situação. Comportamento já presente; agora documentado.
- A consolidação (`/api/situacoes-boleto/consolidacao`) passa a expor, além da
  soma de cotas fracionária, o denominador inteiro arredondado por segmento,
  para que a tela e o arquivo exportado mostrem o mesmo número.
- O harness deve ganhar um caso com cotas fracionárias para exercitar o
  arredondamento, quando o ambiente Node permitir rodar o caminho TypeScript.

## Alternativas descartadas

- Denominador igual à contagem de veículos: quebra a identidade contábil quando
  os veículos têm cotas diferentes de 1.
- Alterar o motor para aceitar soma fracionária pela ponte de arquivo:
  descartado por não tocar o motor; e desnecessário, pois a fonte por API já
  resolve sem arredondamento.
