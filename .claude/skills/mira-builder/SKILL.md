---
name: mira-builder
description: Motor de montagem atômica para criar apresentações interativas em HTML/Tailwind usando componentes Glassmorphism modulares com navegação card-a-card.
---

# Skill: Apresentação de Dados em Cards Animados

## REGRA ZERO — OBRIGATÓRIO ANTES DE QUALQUER GERAÇÃO

**ANTES de gerar qualquer slide, LEIA pelo menos 2 dos 3 arquivos da pasta `/exemplos_de_sucesso/` (01.html, 02.html, 03.html).** Esses arquivos foram editados manualmente junto com o usuario e representam o padrao de qualidade esperado. NAO gere output one-shot sem consulta-los. O objetivo e REPLICAR o nivel de qualidade visual e estrutural desses exemplos.

**ATENCAO sobre cores nos exemplos:** Os exemplos de sucesso usam cores historicas diferentes (`#e47d5b`, `#FFA203`, `#222222`). IGNORE essas cores. Use SEMPRE as cores definidas na secao "Regras de Estilo": `#FF904D` (primaria) e `#000000` (fundo). Os exemplos servem como referencia de ESTRUTURA, LAYOUT e QUALIDADE VISUAL, nao de cores.

## REGRA DE IDIOMA — PORTUGUÊS CORRETO

Siga integralmente `agents/_shared/idioma.md` (regra compartilhada de todos os agentes do Mira): todo texto visível em português brasileiro com acentuação 100% correta, revisado antes de finalizar.


## 📝 Instruções de Execução

Você deve atuar como um engenheiro de front-end especializado em UX/UI. Seu objetivo é transformar dados brutos em uma página HTML única e elegante, selecionando e injetando componentes da pasta `/templates`.

### Passo 0: Planejamento de Conteudo (OBRIGATORIO)

**ANTES de qualquer montagem visual, chame a skill `/mira-planner`.**

O planejador analisa o conteudo do capitulo e gera um plano estruturado de slides (quantidade, tipo de card, conteudo de cada um). Apos aprovacao, o plano passa pelo `/mira-copywriter` que refina titulos, descricoes e selecao de imagens usando tecnicas de copywriting.

- Se o usuario pediu para criar "sem feedback", "direto", "sem confirmacao" ou similar: o pipeline inteiro roda sem pedir aprovacao.
- Se o usuario NAO pediu isso: o planejador apresenta o plano, e apos aprovacao o copywriter refina e apresenta as mudancas antes de continuar.

Use o plano refinado pelo copywriter como guia para os passos seguintes. Nao invente slides fora do plano.

### Passo 1: Leitura Obrigatoria de Referencias
1. **Leia 2+ exemplos** da pasta `exemplos_de_sucesso/` para absorver o padrao visual
2. **Leia as imagens disponiveis** em `decks/<deck>/assets/` (ja inventariadas pelo planejador)
3. **Identifique a logo** em `logo_canal/canal_sandeco_logo.png` (sera copiada para a pasta de destino)
4. **Leia `video_lista.md`** para confirmar o video escolhido pelo planejador

### Passo 2: Montagem dos Cards conforme o Plano
Para cada slide do plano aprovado, use o template indicado:
- **Demonstração de Código:** `card_code.html`
- **Dados Tabulares:** `card_tabela.html`
- **Comparativos/Preços:** `card_destaques.html`
- **Cronogramas/Processos:** `card_timeline.html`
- **Estatísticas/Listas:** `card_lista.html`
- **Destaque Visual:** `card_imagem.html`
- **Grids/Categorias:** `card_grid.html`
- **Metas/Progresso:** `card_progresso.html`
- **Citações/Insights:** `card_citacao.html`
- **Chamada para Acao (CTA):** `card_cta.html` (OBRIGATORIO: Inserir sempre no meio da apresentacao)
- **Graficos D3.js Interativos:** `card_d3.html`
- **Card com Video de Fundo:** `card_video_bg.html`

### Passo 3: Configuração de Componentes
Para cada template selecionado:
1. **Placeholders:** Substitua termos entre colchetes pelos dados reais
2. **Ícones:** Use nomes compatíveis com [Lucide](https://lucide.dev/icons)
3. **Animações:** Incremente `data-aos-delay` em 100ms por card (100, 200, 300...)

### Passo 4: Montagem do Arquivo Final

**Destino:** `decks/<deck>/index.html`

**Arquivos a copiar para a pasta de destino ANTES de gerar o HTML:**
1. `logo_canal/canal_sandeco_logo.png` (ou logo definido no mira.config.json) → `decks/<deck>/logo.png`
2. Um video de `videos_header/` escolhido via `video_lista.md` → `decks/<deck>/header-bg.mp4`
3. Videos adicionais para cards internos (opcional) → `decks/<deck>/video-card-N.mp4`
4. Imagens de `decks/<deck>/assets/` relevantes ao conteudo (referenciar com caminho relativo)

**Concatenação:**
1. **Layout Base (Início):** `layout_base.html` até `<body>`
2. **Abertura:** `header.html` com vídeo local e logo Sandeco
3. **Corpo:** Sequência de cards dos Passos 2 e 3
4. **Encerramento:** `footer.html` com logo Sandeco + fechamento de `layout_base.html`

## 🎯 Regras de Composicao

### Quantidade e Variedade de Cards
- **Minimo:** 8 cards por apresentacao
- **Maximo:** 20 cards por apresentacao
- **Variedade:** Usar pelo menos 3 tipos diferentes de template (nao repetir o mesmo tipo em sequencia)
- **Ritmo visual:** Alternar entre cards densos (tabela, codigo, D3) e cards leves (citacao, imagem, CTA)
- **CTA obrigatorio:** Inserir `card_cta.html` no meio da apresentacao (entre os cards 4-8)

### Geracao de Imagens
- Se o conteudo do slide precisa de uma imagem que nao existe em `decks/<deck>/assets/`, chame a skill `/mira-visuals` para gerar a imagem antes de montar o slide.

### Passo 5: Validacao Automatica (OBRIGATORIO)

Apos gerar o `index.html` e copiar todos os assets, **chame a skill `/mira-validator`** para verificar a conformidade do arquivo gerado. O validador checa cores, logos, videos, layout e estrutura. Se houver falhas criticas, corrija antes de apresentar ao usuario.

## 🎨 Regras de Estilo e Design

### Cores (OBRIGATÓRIO — usar exatamente estas)
- **Fundo:** `#000000` (preto puro)
- **Cor primária:** `#FF904D` (coral/laranja)
- **rgba equivalente:** `rgba(255, 144, 77, ...)`
- **Cor de erro/vibe coding:** `#FF6464`

### Identidade Visual (OBRIGATÓRIO)
- **Logo Canal Sandeco:** `canal_sandeco_logo.png` como `<img>` no header E no footer. NUNCA usar SVG genérico.
- **Video de fundo no header:** Sempre um arquivo `.mp4` LOCAL na mesma pasta do HTML, com `opacity-50` (50%) e overlay gradient.

### Layout dos Cards
- **Largura:** `max-w-5xl` (NÃO `max-w-3xl`, NÃO `max-w-6xl`)
- **Padding:** `p-8` ou `p-10` (NÃO `p-16`)
- **Gap entre slides:** `gap-[60vh]`
- **Glassmorphism:** `backdrop-filter: blur(10px)` e bordas semi-transparentes

### Tipografia
- **Fonte:** Inter (Google Fonts) — adicionar no `<head>`
- **Títulos de card:** `text-3xl` ou `text-4xl` (NÃO `text-5xl`)
- **Corpo:** `text-base` ou `text-lg`

### Imagens do Capítulo
- **OBRIGATÓRIO:** Verificar `decks/<deck>/assets/` e incluir as imagens relevantes nos slides correspondentes
- Usar `class="w-full rounded-lg"` para imagens de largura total
- Copiar imagens para a pasta de destino do slide

### Videos (OBRIGATORIO)
- **Selecao de video:** Consultar `video_lista.md` para escolher o video mais adequado ao tema
- **Header:** Sempre incluir um video de fundo no header (copiado como `header-bg.mp4`)
- **Cards internos:** Opcionalmente usar videos adicionais como fundo de cards ao longo da apresentacao
- **Atributos obrigatorios:** `autoplay loop muted playsinline`
- **Opacidade:** Sempre `opacity: 0.5` (50% de transparencia) via `style="opacity: 0.5;"` ou `class="opacity-50"`
- **Overlay:** Sempre com gradient overlay por cima para garantir legibilidade do texto

Exemplo de video em card interno:
```html
<div class="relative overflow-hidden rounded-2xl">
    <video autoplay loop muted playsinline class="absolute inset-0 w-full h-full object-cover" style="opacity: 0.5;">
        <source src="video-card-1.mp4" type="video/mp4">
    </video>
    <div class="absolute inset-0" style="background: linear-gradient(to bottom, rgba(0,0,0,0.7), rgba(0,0,0,0.5));"></div>
    <div class="relative z-10 p-8">
        <!-- conteudo do card -->
    </div>
</div>
```

### Seguranca
- No `card_code.html`, converter `<` e `>` em `&lt;` e `&gt;`
- Tabelas: colunas do `<thead>` devem bater com `<tbody>`

## 🧭 Navegação Card-a-Card

### Comportamento
- **Espaçamento:** `setupFullScreenWrappers()` envolve cada card em container `min-h-screen`
- **Botão "Começar":** No header, leva ao primeiro card
- **Botão flutuante:** `#next-card` fixo no canto inferior direito, aparece após 300px de scroll
- **Barra de progresso:** Fixa no topo
- **Teclado:** Seta Direita/Baixo/PageDown avança; Seta Esquerda/Cima/PageUp retrocede

### Implementação
Já integrado nos templates `layout_base.html` e `header.html`.

## 🖼️ Checklist de Assets por Slide

Para cada apresentação gerada, garantir:
- [ ] `canal_sandeco_logo.png` copiada para pasta de destino
- [ ] `header-bg.mp4` (video escolhido via `video_lista.md`) copiado para pasta de destino
- [ ] Videos adicionais para cards internos copiados (se aplicavel)
- [ ] Imagens de `decks/<deck>/assets/` relevantes referenciadas
- [ ] Logo aparece no header (dentro do `<div>` central, após subtítulo)
- [ ] Logo aparece no footer (antes do copyright)
- [ ] Video toca no fundo do header com overlay gradient e `opacity: 0.5`
- [ ] Todos os videos usam `autoplay loop muted playsinline` com `opacity: 0.5`
- [ ] Cores usam #FF904D (NÃO #FFA203)
- [ ] Fundo usa #000000 (NÃO #222222)
- [ ] NÃO há número de slides no header (remover `[DESTAQUE_NUMERICO]`)

## 🚀 Saída Esperada
Um arquivo `index.html` completo, autossuficiente, com:
- Vídeo de fundo no header
- Logo Canal Sandeco no header e footer
- Imagens do capítulo nos slides relevantes
- Scripts de animação (AOS), ícones (Lucide), navegação card-a-card
- Qualidade visual compatível com os exemplos de sucesso