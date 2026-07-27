---
name: mira-img-animator
description: >
  Cria animações D3.js a partir de imagens fornecidas pelo usuário. Transforma fotos, diagramas,
  logos ou qualquer imagem em visualizações animadas e interativas usando D3.js + Canvas/SVG.
  Use este skill sempre que o usuário pedir para animar uma imagem, criar efeitos visuais a partir
  de uma imagem, transformar imagem em partículas, criar animações baseadas em imagem, gerar
  visualizações interativas de uma imagem, ou qualquer combinação de "imagem + animação + D3".
  Também deve ser usado quando o usuário mencionar termos como "partículas", "dissolve",
  "explode", "morph", "wave", "pixel art animado", "imagem animada com D3", "efeito visual
  em imagem", "animação interativa de imagem", ou pedir para transformar uma imagem estática
  em algo dinâmico e interativo. Funciona com JPG, PNG, SVG, GIF e WebP.
---

# D3 Image Animator

Transforma imagens em animações D3.js interativas. Foco principal em **fotos e imagens reais
(JPG, PNG)**, gerando sempre um **HTML standalone** (arquivo único, self-contained, com D3 via CDN
e imagem embutida em base64).

## Fluxo de Trabalho

### 1. Receber a Imagem

A imagem pode vir de:

- **Upload direto** → arquivo em `/mnt/user-data/uploads/`
- **URL da web** → baixar via `web_fetch`
- **Imagem no contexto** → Claude já vê a imagem e pode analisar seus elementos

**Formatos suportados:** JPG e PNG são os formatos primários. WebP, GIF, SVG e BMP
também funcionam mas podem precisar de conversão via `scripts/image_to_base64.py --convert-to png`.

**Otimização para fotos:** Fotos reais tendem a ser grandes e com muitos pixels relevantes.
Sempre redimensionar para max 800px de largura antes de processar para partículas.
Usar `scripts/resize_image.py` antes de `scripts/extract_pixels.py`.

### 2. Analisar a Imagem

Antes de gerar código, analisar a imagem visualmente para decidir a melhor abordagem:

- **Tipo de conteúdo**: foto, logo, diagrama, ilustração, ícone, gráfico, texto
- **Complexidade**: simples (poucas formas), média, complexa (foto detalhada)
- **Cores dominantes**: extrair paleta de cores para usar na animação
- **Elementos identificáveis**: formas geométricas, texto, contornos, regiões

### 3. Escolher o Tipo de Animação

Consultar `references/ANIMATION_CATALOG.md` para ver o catálogo completo de efeitos disponíveis.
A escolha depende do tipo de imagem e do efeito desejado pelo usuário.

**Regra geral de decisão:**

| Tipo de imagem | Animação recomendada |
|----------------|---------------------|
| Logo/ícone simples | Partículas, morph, draw-on |
| Foto/imagem complexa | Partículas (sampled), wave, dissolve, pixelate |
| Diagrama/fluxograma | Force-directed, draw-on, highlight |
| Texto/tipografia | Partículas de texto, scramble, typewriter |
| Gráfico/chart | Transições de dados, staggered bars |

Se o usuário não especificou o tipo de animação, perguntar mostrando 2-3 opções
que fazem sentido para a imagem fornecida, com uma breve descrição visual de cada.

### 4. Gerar o Código

Consultar `references/D3_PATTERNS.md` para padrões de código D3.js testados e otimizados.

**Regras fundamentais para o código gerado:**

1. **HTML standalone** — Arquivo único `.html` com tudo embutido (CSS, JS, D3 via CDN)
2. **D3.js v7** — Sempre usar a versão 7 via CDN: `https://d3js.org/d3.v7.min.js`
3. **Canvas para performance** — Usar Canvas (não SVG) quando houver mais de 5.000 elementos
4. **SVG para interatividade** — Usar SVG quando precisar de hover/click em elementos individuais
5. **Imagem como base64** — Converter a imagem para base64 e embutir no HTML para ser self-contained
6. **Responsivo** — Animação deve se adaptar ao tamanho da tela
7. **Controles** — Incluir botões de play/pause/reset quando relevante
8. **Performance** — Usar `requestAnimationFrame` para loops, limitar partículas a ~50.000

Para converter a imagem em base64, usar o script auxiliar:

```bash
python scripts/image_to_base64.py <caminho_da_imagem>
```

Para extrair a paleta de cores dominantes:

```bash
python scripts/extract_palette.py <caminho_da_imagem> --colors 6
```

Para extrair dados de pixels (posição + cor) da imagem para animação de partículas:

```bash
python scripts/extract_pixels.py <caminho_da_imagem> --sample-rate 4 --min-alpha 128
```

### 5. Estrutura do HTML Gerado

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Nome da Animação]</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        /* Reset + estilos da animação */
        /* Controles de UI quando aplicável */
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        // 1. Configuração (dimensões, dados da imagem)
        // 2. Setup do Canvas ou SVG
        // 3. Extração/processamento de pixels
        // 4. Lógica da animação
        // 5. Controles e interatividade
        // 6. Função de resize responsiva
    </script>
</body>
</html>
```

### 6. Salvar e Entregar

O output é **sempre HTML standalone** — arquivo único com tudo embutido.

Salvar o HTML gerado e usar `present_files` para entregar:

```python
output_path = "/mnt/user-data/outputs/animacao_d3_[nome].html"
```

**Nota:** Se por algum motivo o usuário pedir React (.jsx), consultar `references/REACT_PATTERNS.md`
para adaptação, mas o padrão é sempre HTML standalone.

## Diretrizes de Qualidade

- **Estética importa**: seguir princípios do skill `frontend-design` — cores coesas, tipografia elegante, backgrounds atmosféricos
- **Animação fluida**: mínimo 30fps, idealmente 60fps. Testar performance com imagens grandes
- **Interatividade significativa**: mouse hover, click, drag devem fazer algo visualmente satisfatório
- **Código limpo**: comentários claros em português, variáveis com nomes descritivos
- **Fallback gracioso**: se a imagem não carregar, mostrar mensagem amigável

## Tratamento de Erros

Consultar `references/ERRORS.md` para cenários de erro e como tratá-los.
