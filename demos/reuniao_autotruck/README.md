# Kit de demonstracao — AutoTruck (Modelo Elo Ajustado)

Objetivo: provar ao vivo que o motor da AutoTruck le os arquivos de verdade e
reage ao conteudo deles, sem nada combinado ou simulado. Este kit e isolado:
nao toca o motor do ELLO nem os dados reais da AutoTruck.

A AutoTruck recebe 3 arquivos na aba "Rodar Mes":

- BASE: cotas adimplentes e inadimplentes por segmento. E o denominador, ou
  seja, quem divide o custo do mes.
- RATEIO: eventos sinistrados do mes. E o numerador, ou seja, o custo a ratear.
- PRODUTOS: catalogo de fornecedor. E opcional e apenas informativo, nao entra
  no calculo.

Os tres segmentos sao LEVES (automoveis), MOTOS e PESADOS (caminhoes). A cota
variavel se aplica a LEVES e MOTOS. Eventos de terceiros sao rastreados em
separado e nao abatem a cota dos associados.

## Arquivos

- `BASE_completa.xlsx` cotas por segmento (LEVES 1.000, MOTOS 2.000, PESADOS 300 adimplentes)
- `BASE_reduzida.xlsx` igual a completa, mas com metade dos MOTOS adimplentes (1.000)
- `RATEIO_completo.xlsx` 7 eventos do mes (associados e terceiros, LEVES, MOTOS e PESADOS)
- `RATEIO_reduzido.xlsx` igual ao completo, sem o evento parcial de MOTOS
- `PRODUTOS.xlsx` catalogo de fornecedor (opcional)
- `FOLHA_DE_APOIO.md` numeros esperados de cada cenario, para conferir ao vivo
- `gerar_kit_demo.py` script que regenera tudo e revalida os numeros no motor

## Como demonstrar (aba "Rodar Mes")

Primeiro, o cenario base:

1. Selecione o produto AutoTruck no topo da tela.
2. Va em "Rodar Mes".
3. Envie `BASE_completa.xlsx` no campo BASE, `RATEIO_completo.xlsx` no campo
   RATEIO e `PRODUTOS.xlsx` no campo PRODUTOS.
4. Confirme o mes de referencia (por exemplo 05/2026) e calcule.
   Cota MOTOS esperada: R$ 20,00. Cota LEVES esperada: R$ 60,00.
   Invariante de auditoria: Delta R$ 0,00.

Demonstracao 1, mover a COTA (troca o arquivo de BASE):

1. Mantenha `RATEIO_completo.xlsx` e `PRODUTOS.xlsx`.
2. Troque apenas a BASE por `BASE_reduzida.xlsx` e calcule de novo.
   A cota de MOTOS deve dobrar, de R$ 20,00 para R$ 40,00, porque o mesmo custo
   passa a ser dividido pela metade dos motociclistas adimplentes.

Demonstracao 2, mover o CUSTO A RATEAR (troca o arquivo de RATEIO):

1. Volte a `BASE_completa.xlsx` e mantenha `PRODUTOS.xlsx`.
2. Troque apenas o RATEIO por `RATEIO_reduzido.xlsx` e calcule de novo.
   O custo a ratear de MOTOS cai de R$ 40.000,00 para R$ 30.000,00, a cota de
   MOTOS cai de R$ 20,00 para R$ 15,00 e os eventos lidos caem de 7 para 6.

## Reforco

- No resultado e na aba Eventos, confira a contagem de eventos lida do arquivo.
  Abra o xlsx ao lado e verifique que bate.
- Deixe um gestor ditar na hora quantos MOTOS adimplentes colocar na BASE ou
  qual evento remover do RATEIO. Como o numero nao foi combinado, nenhuma tela
  simulada acompanharia o resultado.

## Observacao

O comportamento de tela inicial em branco foi aplicado apenas ao ELLO. O produto
AutoTruck permanece como antes.

## Regenerar

    backend/.venv/bin/python3 demos/reuniao_autotruck/gerar_kit_demo.py
