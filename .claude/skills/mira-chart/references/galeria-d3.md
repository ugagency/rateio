# Galeria D3: matriz de recomendação de gráficos

Baseada na galeria oficial do D3 (observablehq.com/@d3/gallery). Use a pergunta que o dado responde, não a estética, para escolher o tipo.

## Matriz: forma dos dados → gráfico

| Pergunta dos dados | Forma típica | Gráfico principal | Alternativas | APIs D3 chave |
|---|---|---|---|---|
| Comparar valores entre poucas categorias (até ~12) | categórico + 1 quantitativo | Barras (horizontal se labels longos) | Lollipop, dot plot | `scaleBand`, `scaleLinear` |
| Comparar muitas categorias (>12) | categórico + 1 quantitativo | Barras horizontais ordenadas com scroll/top-N | Treemap | `scaleBand`, ordenar por valor |
| Evolução no tempo | temporal + quantitativo | Linha | Área (1 série), slope chart (2 pontos no tempo) | `scaleTime`, `line`, `area` |
| Evolução de várias séries no tempo (>4) | temporal + categórico + quantitativo | Linhas com destaque em 1 série | Small multiples, streamgraph | `line`, facetas |
| Parte de um todo (3 a 6 fatias) | categórico + proporção | Rosca (donut) com número central | Barras 100% empilhadas, waffle | `pie`, `arc` |
| Parte de um todo (muitas partes ou hierarquia) | hierárquico | Treemap | Sunburst, icicle, circle packing | `treemap`, `partition`, `hierarchy` |
| Correlação entre 2 variáveis | 2 quantitativos | Scatter | Scatter + regressão, hexbin (muitos pontos) | `scaleLinear` x2 |
| Correlação com 3ª dimensão | 3 quantitativos | Bubble (área = 3ª variável) | Scatter com cor | `scaleSqrt` para raio |
| Distribuição de 1 variável | quantitativo | Histograma | Density plot, box plot, violin | `bin` |
| Comparar distribuições entre grupos | categórico + quantitativo | Box plot | Violin, beeswarm, ridgeline | `bin`, `forceSimulation` (beeswarm) |
| Ranking que muda no tempo | temporal + categórico + ordem | Bump chart | Bar chart race (animado, encadear /mira-animator) | `line`, `scalePoint` |
| Fluxo entre estados/etapas | origem-destino + volume | Sankey | Chord (fluxos mútuos) | `d3-sankey`, `chord` |
| Relações em rede | nós + arestas | Force-directed graph | Arc diagram, matriz de adjacência | `forceSimulation` |
| Valores por região geográfica | geográfico + quantitativo | Choropleth | Símbolos proporcionais no mapa | `geoPath`, `geoMercator` |
| Intensidade em 2 dimensões categóricas | 2 categóricos + quantitativo | Heatmap | Matriz de pontos | `scaleBand` x2, `interpolate*` |
| Progresso até uma meta | 1 valor + alvo | Barra de bullet / gauge minimalista | Número grande + sparkline | `arc` |
| Funil de conversão | etapas ordenadas + quantidade | Barras horizontais decrescentes | Funil de área | `scaleBand` |

## Regras de veto (avisar o usuário)

- **Pizza com mais de 6 fatias**: humanos não comparam ângulos; sugerir barras ou treemap.
- **Linha para categorias sem ordem natural**: linha implica continuidade; usar barras.
- **Eixo Y truncado em barras**: barras codificam pelo comprimento, truncar mente; em linhas, truncar é aceitável com aviso no eixo.
- **Dois eixos Y**: quase sempre confunde; preferir small multiples ou indexar as séries (base 100).
- **3D de qualquer tipo**: distorce a leitura, nunca usar.

## Paletas recomendadas

| Situação | Paleta |
|---|---|
| 1 série, destaque no tema do deck | `--mira-primary` no foco + cinzas neutros |
| Categóricas (até 6) | `d3.schemeTableau10` (cortar nas N primeiras), recolorindo a 1ª para o tema |
| Sequencial (heatmap, choropleth) | `d3.interpolateViridis` ou `d3.interpolateInferno` (tema escuro) |
| Divergente (positivo/negativo) | `d3.interpolateRdBu` invertido conforme o tema |

Em temas escuros (mira-dark), clarear os tons mínimos das paletas sequenciais para não sumirem no fundo.
