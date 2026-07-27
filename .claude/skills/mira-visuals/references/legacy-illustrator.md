---
name: mira-illustrator
description: >
  Gera imagens para o livro no estilo NS5: painel esquerdo escuro com título + painel direito
  com conteúdo visual (foto realista, diagrama técnico ou gráfico de dados). Use esta skill
  SEMPRE que o usuário disser: "criar imagem", "fazer imagem", "gerar imagem", "image creator",
  "imagem para o capítulo", "imagem de capa", "ilustração", "diagrama", "gráfico", ou qualquer
  variação sobre criar elementos visuais para o livro.
---

# 11 - Image Creator: Criador de Imagens para o Livro

Gera imagens para o livro no estilo NS5: painel esquerdo escuro com título + painel direito
com conteúdo visual (foto realista, diagrama técnico ou gráfico de dados).

## Trigger

Ative quando o usuário disser: "criar imagem", "fazer imagem", "gerar imagem", "image creator",
"imagem para o capítulo", "imagem de capa", "ilustração", "diagrama", "gráfico", ou qualquer
variação sobre criar elementos visuais para o livro.

---

## REGRA OBRIGATÓRIA — Revisão Gramatical em Português

**Todo texto em português inserido em SVG/HTML DEVE passar por revisão gramatical
antes da geração final.** Erros comuns que DEVEM ser evitados:

1. **Acentos:** Todas as palavras acentuadas devem estar corretas.
   - ção (não cao), ção (não çao), é (não e), á (não a), ó (não o)
   - Implementação, Prototipação, Manutenção, Avaliação
   - código, módulo, histórico, relatórios, rápido
   - previsível, reutilizáveis, inevitável
2. **Encoding:** Ao escrever HTML via Python, usar UTF-8 direto no string.
   **NÃO usar Unicode escapes** (\u00e7, \u00e3, etc.) — escrever os caracteres
   diretamente: ç, ã, é, á, ó, í, ú, â, ê, ô, à.
   O arquivo Python DEVE ter `encoding="utf-8"` no open().
3. **Checklist antes de gerar:** Releia todo texto visível no SVG e verifique:
   - Cada palavra acentuada está correta?
   - Nenhum acento foi perdido ou trocado?
   - Frases fazem sentido gramatical em português brasileiro?

**Erros de acentuação em imagens do livro são inaceitáveis.**

---

## REGRA DE OURO — Conteúdo Visual Tem Prioridade Total

**O conteúdo do gráfico/diagrama SEMPRE tem prioridade sobre o título NS5.**
Textos, labels, legendas e elementos visuais do conteúdo devem ser grandes e legíveis.
O título NS5 (painel esquerdo) é OPCIONAL e só deve existir quando agrega valor real.

### Decisão: Fullwidth vs. Título NS5

Antes de gerar qualquer imagem, avalie:

```
O conteúdo visual já se explica sozinho?
(tem labels, legendas, título interno, ou é autoexplicativo)
        │
       Sim ──► FULLWIDTH (--fullwidth): conteúdo ocupa 1920x800 inteiro
        │        O \caption{} do LaTeX já fornece contexto suficiente.
       Não
        │
        ▼
É uma foto/cena abstrata que precisa de contexto textual?
        │
       Sim ──► TÍTULO NS5: painel esquerdo 40% + conteúdo 60%
        │
       Não ──► FULLWIDTH
```

**Quando usar FULLWIDTH (sem título):**
- Diagramas técnicos com labels nas setas/boxes (ex: fluxo REQUISITOS → DEPLOY)
- Gráficos de dados com eixos rotulados e legenda interna
- Qualquer conteúdo onde o título seria redundante com o `\caption{}` do LaTeX
- Quando o conteúdo tem muitos elementos que precisam de espaço para serem legíveis

**Quando usar TÍTULO NS5 (com painel esquerdo):**
- Fotos/cenas onde o conceito não é óbvio sem texto de apoio
- Imagens artísticas/metafóricas que precisam de contexto
- Capas de seção ou imagens decorativas

---

## Layout NS5 — Dois Modos

### Modo FULLWIDTH (preferencial para diagramas e gráficos)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│            [CONTEÚDO VISUAL — 100% da largura]                      │
│                                                                     │
│    Diagrama / gráfico / chart ocupa todo o canvas                   │
│    Todos os textos do conteúdo ficam grandes e legíveis             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
  ←──────────────────── 1920 × 800 ──────────────────────────────────→
```

Dimensões do conteúdo: **1920 × 800px** (canvas inteiro)

### Modo TÍTULO NS5 (para fotos e cenas)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ██████████████████████  ┃  [CONTEÚDO VISUAL — foto/cena            │
│                          ┃                                          │
│  Título linha 1          ┃    (ocupa ~60% da largura direita)       │
│  TÍTULO LINHA 2          ┃                                          │
│  (na cor primária)       ┃                                          │
│                          ┃                                          │
└─────────────────────────────────────────────────────────────────────┘
  ←── ~40% largura ──────→   ←────────── ~60% largura ──────────────→
```

Dimensões do conteúdo: **1152 × 800px** (painel direito)

**Especificações comuns:**

| Propriedade | Valor |
|-------------|-------|
| Resolução final | **1920 × 800 pixels** |
| Fundo | **#222222** |
| `primary_color` | ler do `.book-config.json` |

Leia sempre `primary_color` do `.book-config.json` na raiz. Não use a cor hardcoded.

---

## Fluxo de Decisão — Tipo de Conteúdo Visual

```
Usuário pede imagem
        │
        ▼
É fotorrealista? (pessoa, robô, cena, ambiente real)
        │
       Sim ──► Pipeline A: Gemini (Nano Banana) → finalize_ns5.py
        │
       Não
        │
        ▼
É diagrama técnico com setas e ícones?
(arquitetura, fluxo de dados, pipeline, RAG, MCP, agentes...)
        │
       Sim ──► Pipeline B: D3.js (mira-d3-expert) → finalize_ns5.py
        │
       Não
        │
        ▼
É gráfico de dados / chart / plot / visualização?
        │
       Sim ──► Pipeline C: D3.js (mira-d3-expert) → finalize_ns5.py
```

### Quando usar cada pipeline

| Situação | Estilo | Pipeline |
|----------|--------|----------|
| Foto de pessoa/robô/ambiente real | **A** | Gemini → finalize_ns5 |
| Fluxo de dados com ícones e setas | **B** | D3 diagrama → finalize_ns5 |
| Hierarquia / alerta / formas geométricas | **C** | D3 SVG → finalize_ns5 |
| Knowledge graph / rede de entidades | **D** | D3 force-simulation → finalize_ns5 |
| Screenshot de interface anotado | **E** | Screenshot + composição |
| Conceito abstrato / metáfora visual | **F** | Gemini artístico → finalize_ns5 |

Consulte o `STYLE_CATALOG.md` para especificações detalhadas de cada estilo.

---

## FASE 1 — Análise de Referências (primeira vez ou quando solicitado)

### Catálogo de estilos — leitura obrigatória

**NÃO analise imagens individualmente a cada invocação.** O catálogo já foi gerado.
Leia apenas este arquivo:

```
C:\_MEUS LIVROS\TEMPLATE_LIVRO\referencias\STYLE_CATALOG.md
```

Ele documenta **6 estilos visuais** identificados nos livros anteriores do autor,
com especificações técnicas, exemplos reais e decisão de pipeline para cada um.

Só releia imagens da pasta `referencias/imgs/` se o usuário pedir explicitamente
para "atualizar o catálogo de estilos".

---

## FASE 2 — Coleta de Informações

Pergunte ao usuário:
1. **Para qual capítulo?** (define path: `imgs/chXX/`)
2. **Nome do arquivo** (ex: `capa.png`, `agentes.png`)
3. **O que a imagem transmite?** (conceito, cena, emoção)

### FASE 2.5 — Avaliação: Precisa de Título NS5?

**Antes de criar a imagem, avalie automaticamente:**

O conteúdo é um diagrama, gráfico ou chart com labels próprios?
- **SIM** → usar `--fullwidth`. Gerar o conteúdo em **1920x800**. Não perguntar título.
- **NÃO** (foto, cena, metáfora) → perguntar título e subtítulo ao usuário.

**Regra:** na dúvida, use fullwidth. O `\caption{}` do LaTeX já contextualiza a imagem.

---

## PIPELINE A — Fotorrealismo via Gemini (Nano Banana)

**Use quando:** a imagem precisa de pessoa, robô, ambiente real, cena fotográfica.
**Modo padrão:** TÍTULO NS5 (fotos geralmente precisam de contexto textual).

### A1 — Invocar `mira-image-prompt`

Passe como contexto:
- Resumo de estilo das referências
- Conceito/cena desejado
- Aspect ratio do painel direito: **~3:2** (o painel ocupa 60% de 1920px = ~1152x800px)
- Orientação: conteúdo deve "olhar" ou "apontar" para a esquerda (em direção ao texto)
- Fundo da cena deve ser compatível com transição para `#222222`

### A2 — Invocar `15-gemini-image-gen`

- Salvar imagem bruta em: `imgs/tmp/raw_<nome>.png`
- Modelo padrão: `gemini-3.1-flash-image-preview`
- Para qualidade máxima: `gemini-3-pro-image-preview`

### A3 — Finalização

Execute `imgs/finalize_ns5.py`:

```bash
# Modo TÍTULO NS5 (padrão para fotos)
.claude/skills/15-gemini-image-gen/.venv/Scripts/python imgs/finalize_ns5.py \
    imgs/tmp/raw_<nome>.png \
    imgs/chXX/<nome>.png \
    --title1 "Título linha um" \
    --title2 "Destaque" \
    --subtitle "Frase de apoio do conceito apresentado"
```

---

## PIPELINE B — Diagrama Técnico com Setas via D3.js

**Use quando:** fluxos de dados, arquiteturas, pipelines, RAG, MCP, sequências de agentes.
É o estilo "Agentic RAG" — ícones representando componentes ligados por setas coloridas.
**Modo padrão:** FULLWIDTH (diagramas já têm labels e são autoexplicativos).

### B1 — Invocar `mira-d3-expert`

Passe as seguintes instruções obrigatórias:

**Estilo visual (obrigatório):**
- Fundo: `#222222` (sem transparência)
- Setas principais: `primary_color` (ler do `.book-config.json`)
- Setas secundárias / de retorno: cor de contraste (ex: verde `#00C853` ou laranja `#FF6D00`)
- Ícones: SVG inline limpos, fundo circular escuro com borda `primary_color`
- Labels nas setas: texto pequeno, cor `primary_color` ou branca
- Boxes agrupadores: borda arredondada, stroke `primary_color`, fundo semitransparente escuro
- Sem gradientes excessivos — visual flat e clean
- **PRIORIDADE:** labels, legendas e textos do diagrama devem ser GRANDES e legíveis

**Componentes típicos a usar como ícones:**
- Usuário: silhueta humana simples
- Agente/Robô: ícone de robô ou engrenagem
- Banco de dados / Vector DB: ícone de cilindro
- LLM / Modelo: chip ou circuito
- Ferramentas / Tools: ícone de chave/ferramenta
- Web: ícone de globo ou `www://`

**Dimensões do conteúdo:**
- FULLWIDTH (padrão): `1920 × 800px` (canvas inteiro)
- TÍTULO NS5 (raro): `1152 × 800px` (painel direito)

**Exportar como:** PNG via screenshot do HTML renderizado no browser

### B2 — Capturar output

O `mira-d3-expert` gerará HTML/SVG. Execute no browser e capture como PNG.
Salve em `imgs/tmp/diag_<nome>.png`.

### B3 — Finalização

```bash
# FULLWIDTH (padrão para diagramas — conteúdo ocupa tudo)
.claude/skills/15-gemini-image-gen/.venv/Scripts/python imgs/finalize_ns5.py \
    imgs/tmp/diag_<nome>.png \
    imgs/chXX/<nome>.png \
    --fullwidth

# TÍTULO NS5 (usar apenas se avaliação indicar necessidade)
.claude/skills/15-gemini-image-gen/.venv/Scripts/python imgs/finalize_ns5.py \
    imgs/tmp/diag_<nome>.png \
    imgs/chXX/<nome>.png \
    --title1 "Título" --title2 "Destaque" --subtitle "Frase"
```

---

## PIPELINE C — Gráfico de Dados via D3.js

**Use quando:** charts, plots, visualizações de dados, comparativos numéricos.
**Modo padrão:** FULLWIDTH (gráficos já têm eixos, labels e legendas).

### C1 — Invocar `mira-d3-expert`

Passe:
- Tipo de gráfico (bar chart, line chart, scatter, heatmap, etc.)
- Os dados ou estrutura de dados
- Paleta: fundo `#222222`, elementos na `primary_color` e variações
- **PRIORIDADE:** eixos, labels, legendas e valores devem ser GRANDES e legíveis
- Dimensões: **1920 × 800px** (fullwidth) ou **1152 × 800px** (se usar título NS5)
- Exportar como PNG

### C2 — Finalização

```bash
# FULLWIDTH (padrão para gráficos — conteúdo ocupa tudo)
.claude/skills/15-gemini-image-gen/.venv/Scripts/python imgs/finalize_ns5.py \
    imgs/tmp/chart_<nome>.png \
    imgs/chXX/<nome>.png \
    --fullwidth

# TÍTULO NS5 (usar apenas se avaliação indicar necessidade)
.claude/skills/15-gemini-image-gen/.venv/Scripts/python imgs/finalize_ns5.py \
    imgs/tmp/chart_<nome>.png \
    imgs/chXX/<nome>.png \
    --title1 "Título" --title2 "Destaque" --subtitle "Frase"
```

---

## Script de Finalização NS5

O script `imgs/finalize_ns5.py` já existe no projeto. Ele suporta dois modos:

```bash
# FULLWIDTH — conteúdo ocupa 100% do canvas (padrão para diagramas e gráficos)
python imgs/finalize_ns5.py input.png output.png --fullwidth

# TÍTULO NS5 — painel esquerdo com título + conteúdo à direita (para fotos)
python imgs/finalize_ns5.py input.png output.png \
    --title1 "Linha 1" --title2 "Linha 2" --subtitle "Subtítulo"
```

**NÃO recrie o script.** Use o que já existe. Se precisar de alterações, edite o arquivo existente.

---

## FASE FINAL — LaTeX

```latex
\begin{figure}[h!]
    \centering
    \includegraphics[width=1\linewidth]{imgs/chXX/nome.png}
    \caption{Descrição da figura}
    \label{fig:nome-descritivo}
\end{figure}
```

---

## Tabela de Decisão Rápida

| Conteúdo | Pipeline | Modo padrão | Skill invocada |
|----------|----------|-------------|----------------|
| Pessoa / robô / ambiente / cena | A | TÍTULO NS5 | `mira-image-prompt` → `15-gemini-image-gen` |
| Diagrama de arquitetura / fluxograma | B | **FULLWIDTH** | `mira-d3-expert` |
| Chart, plot, visualização de dados | C | **FULLWIDTH** | `mira-d3-expert` |

**Em todos os casos:** o resultado passa por `finalize_ns5.py` para gerar a imagem final.
**Regra de ouro:** conteúdo visual tem prioridade total. Na dúvida, use `--fullwidth`.

---

## Diagnóstico de Erros

| Situação | Ação |
|----------|------|
| `referencias/imgs/` vazia | Avisar e pedir imagens de referência |
| `.book-config.json` sem `primary_color` | Fallback `#ffffff` |
| Gemini retorna sem imagem | Reformular prompt, tentar novamente |
| D3 não exporta PNG direto | Usar puppeteer ou screenshot do browser |
| Texto cortado no painel esquerdo | Reduzir tamanho da fonte ou encurtar título |
