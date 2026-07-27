---
name: mira-visuals
description: >
  Gerador unificado de imagens estáticas para os slides do Mira: painéis retangulares
  (1920x800), infográficos quadrados (1920x1920), diagramas técnicos e gráficos de dados —
  tudo via D3.js com captura em PNG, ou fotorrealismo via prompt JSON (mira-image-prompt).
  Use esta skill SEMPRE que o usuário disser: "criar imagem", "gerar imagem", "ilustração",
  "diagrama", "gráfico estático", "infográfico", "resumo visual", "quadro resumo",
  "imagem para o slide", "visual para o deck", ou qualquer variação sobre criar elementos
  visuais estáticos. Para ANIMAÇÕES use /mira-animator; esta skill produz imagens PARADAS.
---

# Skill: Mira Visuals — Imagens Estáticas para Slides

Fusão das antigas `mira-illustrator` (painéis 1920x800) e `mira-infographic` (quadrados 1920x1920). Uma única porta de entrada que escolhe formato e pipeline conforme o pedido.

## Regras herdadas (obrigatórias)

1. **Idioma**: siga `agents/_shared/idioma.md` — todo texto visível revisado, acentuação 100% correta.
2. **Regra de ouro**: o conteúdo visual tem prioridade total sobre molduras e títulos decorativos.
3. **Legibilidade**: fontes grandes (mínimo 28px em canvas 1920), hierarquia clara, contraste alto.
4. **Cores**: use as CSS variables do tema do deck (`--mira-primary` etc.), nunca hardcoded.
5. **Output**: salve SEMPRE em `decks/<nome-do-deck>/assets/`. Nunca escreva em fontes vinculadas.

## Decisão de formato

| Pedido | Formato | Detalhes em |
|---|---|---|
| Imagem para slide horizontal, cena, foto | Painel 1920×800 | `references/legacy-illustrator.md` |
| Resumo visual, quadro denso, overview | Infográfico 1920×1920 | `references/legacy-infographic.md` |
| Diagrama com setas, arquitetura | Fullwidth no formato do slide | `references/legacy-illustrator.md` (Pipeline B) |
| Gráfico de dados estático | Fullwidth no formato do slide | `references/legacy-illustrator.md` (Pipeline C) |

## Pipelines

**A — Fotorrealismo**: invoque `/mira-image-prompt` para montar o prompt JSON e entregue ao usuário para gerar no serviço de imagem (Gemini/Nano Banana, Midjourney etc.). Se houver skill de geração instalada, encadeie.

**B — Diagrama técnico (D3)**: gere HTML+D3 com o layout fullwidth, setas e labels legíveis. Consulte as diretrizes D3 em `agents/mira-animator/references/`.

**C — Gráfico de dados (D3)**: idem, com escalas comentadas e eixos limpos.

**D — Infográfico (D3)**: canvas 1920×1920, um dos 4 layouts (seções verticais, timeline, dado central com satélites, grid de KPIs) — código de exemplo em `references/legacy-infographic.md`.

## Captura

Para converter HTML em PNG use `scripts/capture.js` (Puppeteer):

```bash
node scripts/capture.js <input.html> <output.png> <largura> <altura>
```

## Checklist final

- [ ] Texto revisado (idioma.md)
- [ ] Formato correto para o destino (slide 16:9 ou quadrado)
- [ ] Cores do tema do deck
- [ ] PNG salvo em `decks/<deck>/assets/`
- [ ] Nada escrito em fontes vinculadas
