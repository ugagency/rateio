# Briefing: Agent Skills

**Fonte:** agent-skills (texto, capturado da web) — decks/agent-skills/references/ (agent-skills-home.md, agent-skills-specification.md)
**Data da extração:** 16 de junho de 2026

## Essência em uma frase

Agent Skills é um formato aberto e leve para dar a qualquer agente de IA conhecimento especializado e fluxos de trabalho, empacotados numa pasta com um `SKILL.md`, que o agente carrega só quando a tarefa pede.

## Conceitos-chave (candidatos a slide)

1. O problema: agente capaz, mas sem contexto. Modelos cada vez mais fortes que ainda erram porque não têm o procedimento nem o contexto específico da empresa, do time, do usuário. (sugestão visual: comparacao)
2. A skill é só uma pasta. No mínimo um `SKILL.md` com frontmatter (name, description) e instruções. Pode trazer scripts, references e assets. (sugestão visual: codigo / d3-fluxo)
3. Disclosure progressivo em 3 estágios. Descoberta (só name + description no startup), Ativação (lê o SKILL.md inteiro quando casa com a tarefa), Execução (roda scripts e abre referências sob demanda). É o coração do formato. (sugestão visual: d3-fluxo / camadas)
4. Pegada de contexto pequena. Muitas skills à mão custando quase nada, porque a instrução completa só entra quando é usada. (sugestão visual: metricas / comparacao)
5. Frontmatter mínimo vs completo. Obrigatórios: name (kebab-case, máx 64, igual ao nome da pasta) e description (máx 1024, o que faz e quando usar). Opcionais: license, compatibility, metadata, allowed-tools. (sugestão visual: codigo)
6. A description é o gatilho. É o que o agente lê no startup para decidir relevância. Bom exemplo cita o que faz e quando usar, com palavras-chave; exemplo fraco ("ajuda com PDFs") não dispara. (sugestão visual: comparacao)
7. Construa uma vez, use em qualquer lugar. Padrão aberto adotado por dezenas de clientes: Claude e Claude Code, Cursor, VS Code, GitHub Copilot, Gemini CLI, OpenAI Codex, Goose, OpenHands, e muitos outros. (sugestão visual: d3-fluxo / grade de logos)
8. Origem e abertura. Criado pela Anthropic, lançado como padrão aberto, mantido com a comunidade no GitHub e Discord. (sugestão visual: timeline)
9. Boas práticas de estrutura. SKILL.md abaixo de 500 linhas, instruções abaixo de ~5000 tokens, referências a um nível de profundidade, material detalhado movido para references/. (sugestão visual: codigo / camadas)

## Dados e números

- name: 1 a 64 caracteres; só `a-z`, `0-9` e hífen; não começa nem termina com hífen; sem `--`; igual ao nome da pasta.
- description: 1 a 1024 caracteres.
- compatibility: até 500 caracteres (opcional, raro).
- Disclosure: metadados cerca de 100 tokens; corpo do SKILL.md recomendado abaixo de 5000 tokens; recursos sob demanda.
- SKILL.md principal: manter abaixo de 500 linhas.
- 3 estágios de carregamento: Descoberta, Ativação, Execução.
- Dezenas de clientes compatíveis no ecossistema.

## Trechos de código emblemáticos

Frontmatter mínimo:
```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

Frontmatter com campos opcionais:
```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

Estrutura de pasta:
```
my-skill/
├── SKILL.md          # Obrigatório: metadados + instruções
├── scripts/          # Opcional: código executável
├── references/       # Opcional: documentação
├── assets/           # Opcional: templates, recursos
└── ...
```

Validação:
```bash
skills-ref validate ./my-skill
```

## Narrativa sugerida

Arco: problema (agente capaz, sem contexto) → solução (a skill como pasta portátil com SKILL.md) → como funciona (disclosure progressivo em 3 estágios, pegada pequena) → anatomia (frontmatter, a description como gatilho, diretórios opcionais) → alcance (padrão aberto, dezenas de clientes, origem Anthropic) → CTA (crie a sua: quickstart e spec).

## Lacunas

- O conteúdo do Quickstart (`/skill-creation/quickstart`) não foi capturado; se quisermos um slide de passo a passo prático de criação, vale puxar essa página.
- Sem números de adoção (quantidade exata de clientes, datas). O carrossel de logos é qualitativo.
