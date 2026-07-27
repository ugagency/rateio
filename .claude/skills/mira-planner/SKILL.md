---
name: mira-planner
description: Planejador de conteudo para apresentacoes em slides HTML. Analisa o conteudo de um capitulo (LaTeX, PDF ou texto) e gera um plano detalhado de slides antes da montagem visual. Use esta skill SEMPRE que a skill /mira-builder for acionada, ou quando o usuario quiser planejar o conteudo de uma apresentacao, definir quantos slides criar, ou revisar a estrutura antes de gerar o HTML.
---

# Skill: Planejador de Conteudo para Slides

## Objetivo

Analisar o conteudo-fonte de um capitulo e produzir um plano estruturado de slides que sera usado pela skill `/mira-builder` para montar o HTML final. O plano garante que o conteudo seja bem distribuido, visualmente variado e aprovado pelo usuario antes da geracao.

## Quando esta skill e chamada

1. **Automaticamente** pela `/mira-builder` antes de gerar qualquer HTML
2. **Diretamente** pelo usuario quando quer planejar uma apresentacao

## Fluxo de Execucao

### Passo 1: Identificar a fonte de conteudo

Localize o conteudo do capitulo. As fontes possiveis sao:
- `decks/<deck>/briefing.md` (gerado pelo /mira-extract a partir de uma fonte vinculada — PREFERENCIAL)
- Arquivo apontado diretamente pelo usuario (LaTeX, PDF, Markdown ou texto)
- PDF do capitulo na raiz do projeto
- Texto fornecido diretamente pelo usuario

Leia o conteudo completo para entender os temas, secoes e subsecoes.

### Passo 2: Inventariar os assets visuais

1. **Imagens:** Liste as imagens disponiveis em `decks/<deck>/assets/` e as sugeridas no briefing
2. **Videos:** Leia `video_lista.md` (dentro da skill `/mira-builder`) e selecione:
   - 1 video para o header (o mais adequado ao tema do capitulo)
   - 0-3 videos opcionais para cards internos (os menos distrativos)
3. **Imagens faltantes:** Identifique se algum slide precisa de uma imagem que nao existe. Anote para que a `/mira-builder` possa chamar a `/mira-visuals`

### Passo 3: Gerar o plano de slides

Para cada slide proposto, defina:

```
## Slide N: [Titulo do Slide]
- **Template:** card_XXXX.html
- **Conteudo resumido:** 2-3 frases descrevendo o que vai no slide
- **Dados visuais:** icone Lucide, imagem, video, grafico D3 (se aplicavel)
- **Fonte no capitulo:** secao/subsecao de onde vem o conteudo
```

### Regras de composicao

- **Quantidade:** Sugira entre 8 e 20 slides, proporcional ao tamanho do capitulo
- **Variedade:** Use pelo menos 4 tipos diferentes de template
- **Ritmo:** Alterne entre cards densos (tabela, codigo, D3) e cards leves (citacao, imagem, CTA)
- **Sequencia proibida:** Nunca 2 cards do mesmo tipo seguidos
- **CTA obrigatorio:** Posicione um `card_cta.html` entre os slides 4-8
- **Abertura forte:** O primeiro card deve ser impactante (grid com numeros, citacao marcante, ou D3)
- **Fechamento forte:** O penultimo card deve ser um resumo ou conclusao visual

### Templates disponiveis

| Template | Quando usar |
|----------|------------|
| `card_lista.html` | Estatisticas, listas com numeros |
| `card_grid.html` | Grids de 2-4 itens, categorias |
| `card_destaques.html` | Comparativos lado a lado (2-3 opcoes) |
| `card_timeline.html` | Cronogramas, processos sequenciais |
| `card_tabela.html` | Dados tabulares, comparacoes detalhadas |
| `card_code.html` | Trechos de codigo, comandos |
| `card_imagem.html` | Destaque de uma imagem com legenda |
| `card_citacao.html` | Citacoes, frases de impacto |
| `card_progresso.html` | Barras de progresso, metricas % |
| `card_cta.html` | Chamada para acao (livro, canal, etc.) |
| `card_d3.html` | Graficos interativos D3.js |
| `card_video_bg.html` | Card com video de fundo |

### Passo 4: Apresentar o plano ao usuario

Formate o plano como uma tabela resumida e apresente ao usuario:

```
# Plano de Slides: [Nome do Capitulo]

**Video header:** [N].mp4 - [descricao]
**Total de slides:** XX

| # | Titulo | Template | Conteudo Resumido |
|---|--------|----------|-------------------|
| 1 | ...    | card_grid | ... |
| 2 | ...    | card_lista | ... |
| ... | | | |
```

Pergunte ao usuario:
- "Este plano tem **XX slides**. Quer ajustar a quantidade?"
- "Quer trocar algum tipo de card ou reorganizar a ordem?"
- "Posso prosseguir com a geracao?"

### Passo 5: Modo sem feedback

Se o usuario pediu para criar "sem feedback", "direto", "sem confirmacao", "crie tudo", ou expressao similar:
- **Gere o plano normalmente** (ele e necessario para a qualidade do output)
- **NAO apresente ao usuario** para aprovacao
- **Prossiga direto** para o `/mira-copywriter` com o plano pronto
- Neste modo, use as regras de composicao como guia autonomo

### Passo 6: Refinamento de Copy (OBRIGATORIO)

Apos o plano ser aprovado (ou gerado em modo sem feedback), **chame a skill `/mira-copywriter`** para refinar titulos, descricoes e selecao de imagens antes de passar para o `/mira-builder`.

## Saida

O plano de slides e um documento intermediario. Ele nao e salvo em arquivo; e passado para o `/mira-copywriter` para refinamento e depois para a `/mira-builder` como contexto de geracao. O plano deve conter:

1. Video escolhido para o header
2. Lista ordenada de slides com template + conteudo
3. Imagens a usar (existentes e a gerar)
4. Videos adicionais para cards internos (se houver)
