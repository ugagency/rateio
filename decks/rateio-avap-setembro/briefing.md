# Briefing: Rateio AVAP, setembro ao centavo
**Fonte:** referências do deck (texto), decks/rateio-avap-setembro/references/ (guia da reunião e fonte única das regras)
**Data da extração:** 22/10/2026

## Essência em uma frase
Para quem fecha o rateio da AVAP: o motor reproduziu o fechamento real de setembro/2026 com diferença zero, segue as mesmas regras que a associação já usa e deixa o operador no comando, organizando, conferindo e registrando cada decisão.

## Conceitos-chave (candidatos a slide)
1. Setembro reproduzido ao centavo: 103 eventos, R$ 1.802.067,92, R$ 7,78 por cota, diferença zero. Prova central. Visual: metricas.
2. Pote único: custo dos eventos + linhas de soma - linhas de dedução, dividido pelas cotas dos veículos ativos. Sem categoria, sem risco, sem FIFO. Visual: d3-fluxo (afluentes desaguando num pote, saída dividida em cotas).
3. Os três relatórios que entram: base de veículos (39.242), foto de eventos (3.095), planilha de fechamento. Conferência com o rodapé do próprio relatório. Visual: fluxo de entrada.
4. Quem paga: veículo ativo. 22.530 no denominador, 16.683 inadimplentes fora, compensados pelas linhas de inadimplência e recuperados. Visual: comparacao (barras).
5. Seleção dos eventos: o campo Valor Rateado do relatório não define o fechamento. 79 da fila + 24 incluídos pelo operador = 103. Integrais rateadas inteiras (32, R$ 1.288.358,60, 74% do custo). Visual: d3-fluxo (fila e inclusões convergindo).
6. Linhas de soma e dedução de setembro: E-SAÚDE, rastreamento, inadimplência (somas); recuperados, salvados (deduções). Digitadas pelo operador. Visual: cascata (waterfall).
7. Alertas que pedem decisão: A1 a A6. O motor não exclui sozinho. Visual: radar/cards pulsando.
8. O mês a mês na tela: rodar, seleção, lançamentos, resultado, boletos. Visual: timeline de 5 passos.
9. O que vem a seguir: outubro em paralelo, lacre do fechamento, layout de cobrança, split da Res. 491. Visual: timeline.
10. Três respostas que ajudam a operação: critério das integrais de fora, fórmula da inadimplência, layout de cobrança. Visual: cards.

## Dados e números
- Total a ratear setembro: R$ 1.802.067,92 = eventos R$ 1.733.393,65 + somas R$ 243.448,76 - deduções R$ 174.774,49.
- Somas: E-SAÚDE 16.239,82; RASTREAMENTO 118.173,45; INADIMPLÊNCIA 109.035,49.
- Deduções: RECEBIDOS (recuperados) 45.521,49; linha de salvados 129.253,00.
- Cotas no denominador: 231.556; veículos ativos: 22.530; valor por cota R$ 7,78.
- Base: 39.242 veículos; fora: 16.683 inadimplentes, 24 associado pendente, 5 peso zero.
- Eventos lidos: 3.095; selecionados 103 (79 da fila + 24 por decisão do operador).
- Integrais: 32, R$ 1.288.358,60 (74% do custo dos eventos).
- Leitura de 39 mil veículos em cerca de 5 segundos.
- Cota: 1 a cada R$ 5 mil de FIPE; peso lido do relatório, não recalculado.

## Trechos de código emblemáticos
Não se aplica ao público (operacional). A fórmula vale como "código" visual.

## Narrativa sugerida
Prova (setembro bateu) → como funciona (pote único, quem paga, quais eventos, linhas) → o operador no comando (alertas, mês a mês) → o que falta e próximo passo (outubro em paralelo, três respostas).

## Lacunas
- Valor do salvado de setembro aparece sem descrição na planilha (provável salvados); no deck tratar como "salvados (linha sem descrição)".
- Proibido no deck: nomes de pessoas, placas, protocolos, temas comerciais.
