# Blueprints de slides do Mira

Fragmentos HTML prontos para serem montados num deck (o `<head>` com Tailwind, AOS, Lucide e D3 v7 vem do deck). Todos seguem a **regra zero** da skill `mira-animator`: nenhuma animação é estática — toda animação ENTRA com coreografia e DEPOIS continua em **loop interno perpétuo**.

| Blueprint | Uso | Loop interno |
|---|---|---|
| `card_capa.html` | Abertura da apresentação | Partículas orbitando o título |
| `card_comparacao.html` | Versus / antes-depois | Spotlight alternando entre os lados |
| `card_metricas.html` | KPIs e números | Contadores na entrada + anéis orbitais girando |
| `card_fluxo.html` | Pipeline / etapas | Partícula viajando pela linha + pulso em cascata |
| `card_escada.html` | Evolução / maturidade | Orbe subindo os degraus e recomeçando |
| `card_orbital.html` | Conceito central + satélites | Satélites orbitando + pulso radial do núcleo |
| `card_encerramento.html` | CTA final | Gradiente de fundo respirando |

Os 12 cards originais da skill `mira-builder` (citação, código, tabela, timeline, grid, etc.) continuam disponíveis em `agents/mira-builder/templates/` e se combinam com estes.

## Convenções

- Placeholders em `[CAIXA_ALTA]` são substituídos pelo agente na montagem.
- Cores SEMPRE via CSS variables do tema (`var(--mira-primary)` etc.) — nunca hardcoded.
- Texto visível SEMPRE em português com acentuação correta.
- Cada stage D3 usa `viewBox` 960×540 (16:9) e IDs únicos por slide.
