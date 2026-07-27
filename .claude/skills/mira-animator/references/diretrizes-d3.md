# Diretrizes D3 (ex-skill mira-d3-expert)

Referência técnica usada por mira-animator e mira-visuals.

# Instruções de Uso
1. Antes de gerar código D3, verifica a pasta `./references/` para garantir conformidade com a v7.
2. Para gráficos hierárquicos, consulta obrigatoriamente `references/layouts-complexos.md`.
3. Prioriza o uso de escalas flexíveis descritas em `references/api-core.md`.

## CAPACIDADES PRINCIPAIS:
1. **Análise de Dados:** Identificar se os dados são categóricos, temporais, quantitativos ou hierárquicos para sugerir o melhor gráfico.
2. **Tradução Visual:** Converter descrições de imagens ou mockups em código D3.js funcional e responsivo.
3. **Padrões de Design:** Aplicar escalas de cores acessíveis, eixos limpos, tooltips interativos e transições suaves (`d3.transition`).

## DIRETRIZES DE CÓDIGO:
1. **Modularidade:** Sempre use o padrão de "Reusable Charts" ou funções modulares.
2. **DOM:** Use as seleções do D3 (`select`, `selectAll`) de forma eficiente com o padrão `join`.
3. **SVG/Canvas:** Priorizar SVG para interatividade e Canvas para datasets massivos (>5000 pontos).
4. **Clean Code:** Comentar as escalas (`d3.scaleLinear`, `d3.scaleTime`) e os domínios.

## WORKFLOW DE EXECUÇÃO:
- **Passo 1:** Analisar a estrutura dos dados (JSON/CSV) ou a imagem de dados.
- **Passo 2:** Propor o tipo de visualização (Bar, Scatter, Force-Directed, Sunburst, etc.).
- **Passo 3:** Gerar o código HTML/JavaScript completo incluindo o container SVG.
- **Passo 4:** Colocar sempre dentro de um container DOM.