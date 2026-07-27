# Agent Skills, visão geral

Fonte: https://agentskills.io/home
Capturado em: 16 de junho de 2026

Uma forma padronizada de dar novas capacidades e expertise a agentes de IA.

## O que são Agent Skills

Agent Skills são um formato aberto e leve para estender as capacidades de um agente de IA com conhecimento especializado e fluxos de trabalho.

No núcleo, uma skill é uma pasta que contém um arquivo `SKILL.md`. Esse arquivo traz metadados (`name` e `description`, no mínimo) e instruções que dizem ao agente como executar uma tarefa específica. Skills também podem empacotar scripts, materiais de referência, templates e outros recursos.

```
my-skill/
├── SKILL.md          # Obrigatório: metadados + instruções
├── scripts/          # Opcional: código executável
├── references/       # Opcional: documentação
├── assets/           # Opcional: templates, recursos
└── ...               # Quaisquer outros arquivos ou diretórios
```

## Por que Agent Skills

Os agentes estão cada vez mais capazes, mas muitas vezes não têm o contexto de que precisam para fazer trabalho real de forma confiável. As skills resolvem isso empacotando conhecimento procedural e contexto específico de empresa, time e usuário em pastas portáteis e versionadas, que o agente carrega sob demanda. Isso dá ao agente:

- Expertise de domínio: capturar conhecimento especializado, de processos de revisão jurídica a pipelines de análise de dados e formatação de apresentações, como instruções e recursos reutilizáveis.
- Fluxos repetíveis: transformar tarefas de múltiplos passos em procedimentos consistentes e auditáveis.
- Reuso entre produtos: construir uma skill uma vez e usá-la em qualquer agente compatível.

## Como funcionam

Os agentes carregam skills por disclosure progressivo, em três estágios:

1. Descoberta: na inicialização, o agente carrega só o nome e a descrição de cada skill disponível, o suficiente para saber quando ela pode ser relevante.
2. Ativação: quando uma tarefa casa com a descrição de uma skill, o agente lê as instruções completas do `SKILL.md` para o contexto.
3. Execução: o agente segue as instruções, opcionalmente rodando código empacotado ou carregando arquivos referenciados conforme a necessidade.

As instruções completas só entram no contexto quando a tarefa exige, então o agente mantém muitas skills à mão com uma pegada de contexto pequena.

## Onde usar

O formato é suportado por um grande número de ferramentas de IA e clientes agênticos. Entre os que adotaram o padrão aparecem, por exemplo: Claude e Claude Code, Cursor, VS Code e GitHub Copilot, Gemini CLI, OpenAI Codex, OpenHands, OpenCode, Goose, Roo Code, Amp, Factory, Kiro, Letta, Tabnine, Qodo, Laravel Boost, Spring AI, Databricks Genie Code, Snowflake Cortex Code, entre outros.

## Desenvolvimento aberto

O formato Agent Skills foi originalmente desenvolvido pela Anthropic, lançado como padrão aberto, e vem sendo adotado por um número crescente de produtos de agente. O padrão é aberto a contribuições do ecossistema. Discussão no GitHub (https://github.com/agentskills/agentskills) e no Discord (https://discord.gg/MKPE9g8aUy).

## Começando

- Quickstart: criar a primeira Agent Skill e vê-la em ação (/skill-creation/quickstart).
- Specification: a especificação completa do formato (/specification), capturada em `agent-skills-specification.md`.
