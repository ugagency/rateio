# Mut — Pasta de criação de slides (Mira)

Esta pasta é uma instalação do **Mira**: agentes e templates para criar apresentações HTML animadas com D3.js. Trate Dudu pelo nome e interaja em pt-br.

## Regras para o agente

1. **Fontes vinculadas**: o conteúdo das apresentações vem das fontes listadas em `mira.config.json` (`sources[]`). Leia das fontes, mas NUNCA crie, edite ou apague arquivos dentro delas. Todo output vai para `decks/`.
2. **Pipeline**: para criar slides, siga a ordem: `/mira-extract` → `/mira-planner` → `/mira-copywriter` → `/mira-builder` + `/mira-animator` → `/mira-validator`.
3. **Regra zero de animação**: toda animação ENTRA com coreografia e DEPOIS continua em loop interno perpétuo. Animação estática é proibida.
4. **Tema**: o tema padrão deste projeto é `mira-dark`. Use SEMPRE as CSS variables do tema (`var(--mira-primary)` etc.) — nunca cores hardcoded. Temas em `mira-templates/themes/`.
5. **Idioma**: siga `_shared/idioma.md` — todo texto visível em português brasileiro com acentuação 100% correta.
6. **Templates**: blueprints de slides em `mira-templates/slides/`, decks completos em `mira-templates/decks/`, cards atômicos em `mira-builder/templates/` (dentro das skills).

## Estrutura

```
mira.config.json     fontes vinculadas, tema padrão, decks criados
decks/               apresentações geradas (uma pasta por deck)
mira-templates/      themes, slides e decks de referência
.mira/               estado da instalação (não editar manualmente)
```
