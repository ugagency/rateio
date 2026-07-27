---
name: mira-infographic
description: >
  Cria infograficos quadrados (1920x1920) usando D3.js para o livro. O foco e legibilidade:
  fontes grandes, hierarquia visual clara, fundo escuro (#222222) e cores do livro.
  Use esta skill SEMPRE que o usuario disser: "infografico", "infographic", "criar infografico",
  "fazer infografico", "gerar infografico", "infografico para o capitulo", "resumo visual",
  "quadro resumo", "overview visual", "mapa visual", "visual summary", ou qualquer variacao
  sobre criar infograficos ou resumos visuais quadrados para o livro.
---

# 19 - Infographic Creator: Infograficos Quadrados para o Livro

Cria infograficos quadrados (1920x1920px) usando D3.js com foco total em legibilidade.
Diferente das imagens NS5 (1920x800), infograficos sao quadrados e autossuficientes,
contendo titulo, secoes, dados e fonte em uma unica composicao visual.

---

## Por que esta skill existe (e nao a mira-illustrator)

A mira-illustrator gera imagens retangulares 1920x800 no formato NS5 (com ou sem painel
de titulo). Infograficos precisam de um canvas quadrado maior para acomodar mais informacao
de forma legivel. Esta skill gera o D3 diretamente em 1920x1920 e captura via Puppeteer,
sem passar pelo `finalize_ns5.py`.

---

## REGRA OBRIGATÓRIA — Revisão Gramatical em Português

**Todo texto em português inserido em SVG/HTML DEVE passar por revisão gramatical
antes da geração final.** Erros comuns que DEVEM ser evitados:

1. **Acentos:** Todas as palavras acentuadas devem estar corretas.
   - ção (não cao), é (não e), á (não a), ó (não o), í (não i)
   - Implementação, Prototipação, Manutenção, Avaliação
   - código, módulo, histórico, relatórios, rápido
   - previsível, reutilizáveis, inevitável
2. **Encoding:** Ao escrever HTML via Python, usar UTF-8 direto no string.
   **NÃO usar Unicode escapes** (`\u00e7`, `\u00e3`, etc.) — escrever os caracteres
   diretamente: ç, ã, é, á, ó, í, ú, â, ê, ô, à.
   O arquivo Python DEVE ter `encoding="utf-8"` no `open()`.
3. **Checklist antes de gerar:** Releia todo texto visível no SVG e verifique:
   - Cada palavra acentuada está correta?
   - Nenhum acento foi perdido ou trocado?
   - Frases fazem sentido gramatical em português brasileiro?

**Erros de acentuação em imagens do livro são inaceitáveis.**

---

## Configuracao Base

| Propriedade | Valor |
|-------------|-------|
| Canvas | **1920 x 1920 pixels** |
| Fundo | **#222222** |
| `primary_color` | ler do `.book-config.json` na raiz |
| Fonte principal | `'Segoe UI', 'Helvetica Neue', Arial, sans-serif` |
| Exportacao | PNG via Puppeteer screenshot |

Leia sempre `primary_color` do `.book-config.json`. Nao use cor hardcoded.

---

## REGRA DE OURO: Fontes Grandes e Legiveis

Em 1920x1920, o infografico sera exibido no livro impresso/PDF numa largura de ~15cm.
Textos pequenos ficam INVISIVEIS. Estas sao as regras minimas absolutas:

| Elemento | Tamanho minimo | Font-weight |
|----------|---------------|-------------|
| Titulo principal do infografico | **72px** | **800 (Extra Bold)** |
| Subtitulo / descricao | **40px** | 400 |
| Titulo de secao / bloco | **48px** | **700 (Bold)** |
| Texto de corpo / labels | **32px** | 400 |
| Valores numericos em destaque | **56px** | **800** |
| Menor texto permitido (fonte/credito) | **24px** | 300 |

**Nenhum texto pode ter menos de 24px.** Se algo precisa ser menor que 24px, ele nao
deve estar no infografico.

### Contraste de texto

- Texto principal: **#FFFFFF** (branco puro)
- Texto secundario: **#CCCCCC**
- Texto em destaque: `primary_color` do livro
- Texto sobre fundo claro: **#222222**

---

## Layouts Disponiveis

Escolha o layout mais adequado ao conteudo. Se o usuario nao especificar, use o que
melhor apresenta a informacao.

### Layout 1: Secoes Verticais (o mais comum)

```
+------------------------------------------+
|           TITULO DO INFOGRAFICO           |  ~200px
|           subtitulo explicativo           |
+------------------------------------------+
|                                          |
|  [SECAO 1]          [SECAO 2]           |
|  icone + dados      icone + dados        |  ~500px
|                                          |
+------------------------------------------+
|                                          |
|  [SECAO 3]          [SECAO 4]           |
|  icone + dados      icone + dados        |  ~500px
|                                          |
+------------------------------------------+
|                                          |
|         [SECAO DESTAQUE / FOOTER]        |  ~500px
|         dado principal em grande         |
|                                          |
+------------------------------------------+
|  Fonte: ...                    logo/ref  |  ~120px
+------------------------------------------+
```

Ideal para: comparativos, resumos de capitulo, "X coisas que voce precisa saber".

### Layout 2: Timeline / Fluxo Vertical

```
+------------------------------------------+
|           TITULO DO INFOGRAFICO           |
+------------------------------------------+
|     [1] -----> Etapa 1                   |
|                descricao                  |
|                    |                      |
|     [2] -----> Etapa 2                   |
|                descricao                  |
|                    |                      |
|     [3] -----> Etapa 3                   |
|                descricao                  |
|                    |                      |
|     [4] -----> Etapa 4                   |
|                descricao                  |
+------------------------------------------+
|  Fonte: ...                              |
+------------------------------------------+
```

Ideal para: processos, ciclos de vida, fluxos sequenciais, evolucao historica.

### Layout 3: Dado Central com Satelites

```
+------------------------------------------+
|           TITULO DO INFOGRAFICO           |
+------------------------------------------+
|                                          |
|     [sat1]              [sat2]           |
|          \              /                |
|           \            /                 |
|        +--[DADO CENTRAL]--+             |
|           /            \                 |
|          /              \                |
|     [sat3]              [sat4]           |
|                                          |
+------------------------------------------+
|  Fonte: ...                              |
+------------------------------------------+
```

Ideal para: conceito central com ramificacoes, ecossistemas, dependencias.

### Layout 4: Grid de Metricas / KPIs

```
+------------------------------------------+
|           TITULO DO INFOGRAFICO           |
+------------------------------------------+
|  +--------+  +--------+  +--------+     |
|  | VALOR  |  | VALOR  |  | VALOR  |     |
|  | label  |  | label  |  | label  |     |
|  +--------+  +--------+  +--------+     |
|  +--------+  +--------+  +--------+     |
|  | VALOR  |  | VALOR  |  | VALOR  |     |
|  | label  |  | label  |  | label  |     |
|  +--------+  +--------+  +--------+     |
+------------------------------------------+
|  Fonte: ...                              |
+------------------------------------------+
```

Ideal para: estatisticas, metricas, dados numericos, comparativos quantitativos.

---

## Fluxo de Execucao

### Passo 1 — Coleta de Informacoes

Pergunte ao usuario:
1. **Para qual capitulo?** (define path: `imgs/chXX/`)
2. **Nome do arquivo** (ex: `infografico-ciclo.png`)
3. **O que o infografico deve mostrar?** (tema, dados, conceito)
4. **Tem dados especificos?** (numeros, listas, comparativos)

### Passo 2 — Planejamento

Antes de gerar codigo:
1. Leia `primary_color` do `.book-config.json`
2. Escolha o layout mais adequado
3. Defina a hierarquia de informacao (o que e mais importante?)
4. Planeje a distribuicao espacial no canvas 1920x1920

### Passo 3 — Gerar codigo D3.js

Invoque o `mira-d3-expert` com estas instrucoes obrigatorias:

```
CONTEXTO: Infografico quadrado para livro tecnico.

DIMENSOES OBRIGATORIAS:
- SVG: viewBox="0 0 1920 1920", width="1920", height="1920"
- Fundo: rect fill="#222222" cobrindo todo o canvas

COR PRIMARIA: [primary_color do .book-config.json]

REGRAS DE FONTE (INEGOCIAVEIS):
- Titulo principal: >= 72px, font-weight 800, fill="#FFFFFF"
- Titulos de secao: >= 48px, font-weight 700
- Texto de corpo/labels: >= 32px, font-weight 400
- Valores numericos em destaque: >= 56px, font-weight 800, fill=[primary_color]
- NENHUM texto menor que 24px

PALETA DE CORES:
- Fundo: #222222
- Texto principal: #FFFFFF
- Texto secundario: #CCCCCC
- Destaque/acentos: [primary_color]
- Variacao clara do destaque: [primary_color com 50% opacidade]
- Cards/blocos: #2A2A2A ou #333333 com border-radius 16px

ESTILO VISUAL:
- Flat design, sem gradientes excessivos
- Cantos arredondados (border-radius >= 12px)
- Espacamento generoso entre elementos (padding >= 40px)
- Icones simples em SVG inline (linhas finas, estilo outline)
- Separadores sutis (#444444)

LAYOUT: [layout escolhido e estrutura de conteudo]

EXPORTAR: HTML completo com o SVG inline, pronto para screenshot.
O HTML deve ter margin:0, padding:0, background:#222222,
e o SVG centralizado no body.
```

### Passo 4 — Gerar HTML e capturar PNG

1. Salve o HTML gerado em: `imgs/tmp/infog_<nome>.html`
2. Execute o script de captura:

```bash
node "$(cygpath -w '.claude/skills/mira-infographic/scripts/capture.js')" \
    "imgs/tmp/infog_<nome>.html" \
    "imgs/chXX/<nome>.png"
```

3. Verifique se o PNG foi criado e mostre ao usuario.

### Passo 5 — LaTeX

Gere o bloco LaTeX para inclusao no capitulo:

```latex
\begin{figure}[h!]
    \centering
    \includegraphics[width=1\linewidth]{imgs/chXX/nome.png}
    \caption{Descricao do infografico}
    \label{fig:nome-descritivo}
\end{figure}
```

---

## Script de Captura

O script `scripts/capture.js` usa Puppeteer para renderizar o HTML e capturar
o PNG em 1920x1920. Ele ja esta incluso nesta skill — nao recrie.

```bash
node .claude/skills/mira-infographic/scripts/capture.js input.html output.png
```

---

## Checklist de Qualidade

Antes de entregar o infografico, verifique:

- [ ] Canvas e exatamente 1920x1920
- [ ] Fundo e #222222
- [ ] Nenhum texto menor que 24px
- [ ] Titulo principal >= 72px e visivel
- [ ] primary_color usada como cor de destaque
- [ ] Espacamento adequado (nada apertado ou cortado)
- [ ] Hierarquia visual clara (o olho sabe para onde ir)
- [ ] PNG salvo no path correto (`imgs/chXX/`)

---

## Diagnostico de Erros

| Situacao | Acao |
|----------|------|
| Texto cortado nas bordas | Aumentar padding interno (min 60px de margem) |
| Fontes parecem pequenas | Verificar se respeitou os minimos da tabela |
| Puppeteer nao encontrado | `npx puppeteer` ou instalar globalmente |
| PNG saiu com dimensoes erradas | Verificar viewBox e width/height do SVG |
| Cores erradas | Reler `.book-config.json` |
