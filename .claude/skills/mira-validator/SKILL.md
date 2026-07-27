---
name: mira-validator
description: Analisa e valida o HTML gerado pela skill /mira-builder, verificando conformidade visual, estrutural e de assets. Use esta skill SEMPRE que a /mira-builder terminar de gerar um index.html, ou quando o usuario quiser verificar a qualidade de uma apresentacao existente, revisar se os slides seguem o padrao, ou diagnosticar problemas visuais em slides ja criados.
---

# Skill: Validador de Slides

## Objetivo

Inspecionar o arquivo `index.html` gerado pela `/mira-builder` e produzir um relatorio de conformidade. O validador checa regras de estilo, presenca de assets, estrutura HTML e boas praticas definidas no padrao do projeto.

## Quando esta skill e chamada

1. **Automaticamente** pela `/mira-builder` apos gerar o HTML final
2. **Manualmente** pelo usuario para validar uma apresentacao existente

## Fluxo de Execucao

### Passo 1: Localizar o arquivo

Identifique o `index.html` a validar:
- Se chamado pela `/mira-builder`, o caminho ja e conhecido: `decks/<deck>/index.html`
- Se chamado pelo usuario, pergunte qual capitulo ou aceite o caminho direto

### Passo 2: Ler o HTML completo

Leia o conteudo inteiro do `index.html` gerado.

### Passo 3: Executar as verificacoes

Execute cada verificacao abaixo e registre o resultado como PASS ou FAIL com detalhes.

---

## Checklist de Verificacoes

### A. Cores (critico)

| # | Verificacao | Como checar |
|---|------------|-------------|
| A1 | Cor primaria e `#FF904D` | Buscar ocorrencias de `#FF904D` (deve existir). Buscar `#FFA203` ou `#e47d5b` (nao deve existir) |
| A2 | Fundo e `#000000` | Buscar `background: #000000` no body. Buscar `#222222` ou `#1a1a2e` (nao deve existir) |
| A3 | rgba usa `255, 144, 77` | Buscar `rgba(255, 144, 77` (deve existir). Buscar `rgba(255, 162, 3` (nao deve existir) |

### B. Identidade Visual (critico)

| # | Verificacao | Como checar |
|---|------------|-------------|
| B1 | Logo no header | Buscar `<img` com `canal_sandeco_logo.png` dentro do `<header>` |
| B2 | Logo no footer | Buscar `<img` com `canal_sandeco_logo.png` apos o `</main>` |
| B3 | Arquivo logo existe | Verificar se `canal_sandeco_logo.png` existe na pasta do slide |
| B4 | Nenhum SVG generico no lugar da logo | Buscar `<svg` proximo de "sandeco" ou "logo" (nao deve existir) |

### C. Videos (critico)

| # | Verificacao | Como checar |
|---|------------|-------------|
| C1 | Video no header | Buscar `<video` dentro do `<header>` com `src="header-bg.mp4"` |
| C2 | Arquivo header-bg.mp4 existe | Verificar se o arquivo existe na pasta do slide |
| C3 | Atributos obrigatorios | Todo `<video` deve ter `autoplay`, `loop`, `muted`, `playsinline` |
| C4 | Opacidade 50% | Todo `<video` deve ter `opacity: 0.5` ou `opacity-50` |
| C5 | Overlay gradient | Apos cada `<video`, deve haver um `<div` com `linear-gradient` |

### D. Layout dos Cards (importante)

| # | Verificacao | Como checar |
|---|------------|-------------|
| D1 | Largura `max-w-5xl` | Cards devem usar `max-w-5xl`. Buscar `max-w-3xl`, `max-w-2xl`, `max-w-6xl` em cards (nao deve existir, exceto dentro de paragrafos `<p>` onde `max-w-3xl` e permitido) |
| D2 | Padding adequado | Cards devem usar `p-8` ou `p-10`. Buscar `p-16` em cards (nao deve existir) |
| D3 | Gap entre cards | `<main>` deve ter `gap-[60vh]` |
| D4 | Glassmorphism | Deve existir `backdrop-filter: blur(10px)` no CSS |

### E. Tipografia (importante)

| # | Verificacao | Como checar |
|---|------------|-------------|
| E1 | Fonte Inter | Buscar `fonts.googleapis.com` com `Inter` no `<head>` |
| E2 | Titulos de card | Titulos `<h3>` dentro de cards devem usar `text-3xl` ou `text-4xl`. Buscar `text-5xl` em `<h3>` (nao deve existir) |
| E3 | Titulo principal | O `<h1>` do header pode usar `text-5xl` ou `text-7xl` (permitido) |

### F. Estrutura e Navegacao (importante)

| # | Verificacao | Como checar |
|---|------------|-------------|
| F1 | Barra de progresso | Buscar `id="reading-progress"` |
| F2 | Botao proximo card | Buscar `id="next-card"` |
| F3 | Botao comecar no header | Buscar `id="header-next-btn"` |
| F4 | AOS inicializado | Buscar `AOS.init` |
| F5 | Lucide inicializado | Buscar `lucide.createIcons` |
| F6 | D3.js carregado | Buscar `d3.v7` no `<head>` (se houver cards D3) |
| F7 | setupFullScreenWrappers | Buscar `setupFullScreenWrappers` |

### G. Conteudo e Composicao (qualidade)

| # | Verificacao | Como checar |
|---|------------|-------------|
| G1 | Minimo de cards | Contar elementos `glass-card` ou cards dentro de `<main>`. Minimo: 8 |
| G2 | Variedade de templates | Identificar tipos de cards usados. Minimo: 3 tipos diferentes |
| G3 | CTA presente | Buscar indicadores de card CTA (botao de acao, link para livro/canal) |
| G4 | Sem cards repetidos em sequencia | Verificar se nao ha 2 cards do mesmo tipo seguidos |
| G5 | Sem placeholders residuais | Buscar `[TITULO]`, `[DESCRICAO]`, `[DELAY]`, `[ICONE]` e outros placeholders nao substituidos |
| G6 | Sem numero de slides no header | Buscar `[DESTAQUE_NUMERICO]` (nao deve existir) |

### H. Assets do Capitulo (importante)

| # | Verificacao | Como checar |
|---|------------|-------------|
| H1 | Imagens referenciadas existem | Para cada `<img src="...">` no HTML, verificar se o arquivo existe na pasta |
| H2 | Videos referenciados existem | Para cada `<source src="...mp4">`, verificar se o arquivo existe na pasta |

### I. Seguranca (importante)

| # | Verificacao | Como checar |
|---|------------|-------------|
| I1 | Codigo escapado | Em blocos `<code>` ou `<pre>`, buscar `<` e `>` nao escapados (exceto tags HTML internas). Deve usar `&lt;` e `&gt;` |

---

## Passo 4: Gerar o Relatorio

Apresente o relatorio no seguinte formato:

```
# Relatorio de Validacao: [Capitulo]

**Arquivo:** slides/<tema>/index.html
**Data:** YYYY-MM-DD
**Total de verificacoes:** XX
**Passou:** XX | **Falhou:** XX | **Avisos:** XX

## Resultados

### Criticos (devem ser corrigidos)
- [FAIL] A1: Cor #FFA203 encontrada nas linhas 45, 112
- [PASS] B1: Logo presente no header

### Importantes (recomendado corrigir)
- [FAIL] D1: Card na linha 89 usa max-w-3xl em vez de max-w-5xl
- [PASS] E1: Fonte Inter carregada

### Qualidade (sugestoes)
- [WARN] G4: Cards 3 e 4 sao ambos card_lista
- [PASS] G1: 12 cards encontrados

## Correcoes Sugeridas

Para cada FAIL, indique:
1. **Linha(s):** onde esta o problema
2. **Atual:** o que esta escrito
3. **Correto:** o que deveria estar
4. **Como corrigir:** instrucao especifica de edicao
```

### Niveis de severidade

- **Critico** (categorias A, B, C): Problemas visuais graves ou assets faltantes. A apresentacao nao deve ser publicada sem corrigir.
- **Importante** (categorias D, E, F, H, I): Desvios do padrao que afetam qualidade mas nao impedem o uso.
- **Qualidade** (categoria G): Sugestoes de composicao e variedade que melhoram a experiencia.

## Passo 5: Oferecer correcao automatica

Apos apresentar o relatorio, pergunte:

> "Encontrei **X problemas**. Quer que eu corrija automaticamente os itens criticos e importantes?"

Se o usuario aceitar, aplique as correcoes diretamente no `index.html` usando edicoes pontuais (Edit tool). Apos corrigir, rode a validacao novamente para confirmar que tudo passou.

## Notas

- Esta skill NAO modifica o conteudo textual dos slides, apenas corrige problemas tecnicos e de conformidade
- Se um problema e ambiguo (ex: um card poderia ser lista ou grid), classifique como WARN em vez de FAIL
- Placeholders residuais (G5) sao sempre FAIL critico porque indicam montagem incompleta
