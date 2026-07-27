# Agent Skills, especificação do formato

Fonte: https://agentskills.io/specification
Índice da documentação: https://agentskills.io/llms.txt
Capturado em: 16 de junho de 2026

A especificação completa do formato Agent Skills.

## Estrutura de diretórios

Uma skill é um diretório que contém, no mínimo, um arquivo `SKILL.md`:

```
skill-name/
├── SKILL.md          # Obrigatório: metadados + instruções
├── scripts/          # Opcional: código executável
├── references/       # Opcional: documentação
├── assets/           # Opcional: templates, recursos
└── ...               # Quaisquer outros arquivos ou diretórios
```

## Formato do `SKILL.md`

O arquivo `SKILL.md` precisa conter um frontmatter YAML seguido de conteúdo em Markdown.

### Frontmatter

| Campo           | Obrigatório | Restrições                                                                                                     |
| --------------- | ----------- | -------------------------------------------------------------------------------------------------------------- |
| `name`          | Sim         | Máx. 64 caracteres. Apenas letras minúsculas, números e hífens. Não pode começar nem terminar com hífen.       |
| `description`   | Sim         | Máx. 1024 caracteres. Não vazio. Descreve o que a skill faz e quando usá-la.                                   |
| `license`       | Não         | Nome da licença ou referência a um arquivo de licença incluído.                                                |
| `compatibility` | Não         | Máx. 500 caracteres. Indica requisitos de ambiente (produto-alvo, pacotes do sistema, acesso à rede, etc.).    |
| `metadata`      | Não         | Mapa arbitrário chave-valor para metadados adicionais.                                                         |
| `allowed-tools` | Não         | String separada por espaços com ferramentas pré-aprovadas que a skill pode usar. (Experimental)                |

Exemplo mínimo:

```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

Exemplo com campos opcionais:

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

#### Campo `name`

- Deve ter de 1 a 64 caracteres
- Só pode conter caracteres alfanuméricos minúsculos unicode (`a-z`, `0-9`) e hífens (`-`)
- Não pode começar nem terminar com hífen (`-`)
- Não pode conter hífens consecutivos (`--`)
- Precisa coincidir com o nome do diretório pai

Válidos: `pdf-processing`, `data-analysis`, `code-review`.
Inválidos: `PDF-Processing` (maiúscula), `-pdf` (começa com hífen), `pdf--processing` (hífens consecutivos).

#### Campo `description`

- Deve ter de 1 a 1024 caracteres
- Deve descrever tanto o que a skill faz quanto quando usá-la
- Deve incluir palavras-chave específicas que ajudem os agentes a identificar tarefas relevantes

Bom exemplo:

```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

Exemplo fraco:

```yaml
description: Helps with PDFs.
```

#### Campo `license`

- Especifica a licença aplicada à skill
- Recomenda-se mantê-lo curto (o nome da licença ou o nome de um arquivo de licença incluído)

```yaml
license: Proprietary. LICENSE.txt has complete terms
```

#### Campo `compatibility`

- Deve ter de 1 a 500 caracteres, se fornecido
- Só deve ser incluído se a skill tiver requisitos específicos de ambiente
- Pode indicar produto-alvo, pacotes de sistema exigidos, necessidade de acesso à rede, etc.

```yaml
compatibility: Designed for Claude Code (or similar products)
compatibility: Requires git, docker, jq, and access to the internet
compatibility: Requires Python 3.14+ and uv
```

A maioria das skills não precisa do campo `compatibility`.

#### Campo `metadata`

- Um mapa de chaves string para valores string
- Clientes podem usá-lo para guardar propriedades adicionais não definidas pela spec
- Recomenda-se usar nomes de chave razoavelmente únicos para evitar conflitos acidentais

```yaml
metadata:
  author: example-org
  version: "1.0"
```

#### Campo `allowed-tools`

- Uma string separada por espaços com ferramentas pré-aprovadas para rodar
- Experimental. O suporte a este campo pode variar entre implementações de agente

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

### Conteúdo do corpo

O corpo em Markdown após o frontmatter contém as instruções da skill. Não há restrições de formato. Seções recomendadas:

- Instruções passo a passo
- Exemplos de entradas e saídas
- Casos de borda comuns

O agente carrega o arquivo inteiro assim que decide ativar a skill. Considere dividir conteúdos longos do `SKILL.md` em arquivos referenciados.

## Diretórios opcionais

### `scripts/`

Código executável que os agentes podem rodar. Scripts devem:

- Ser autocontidos ou documentar claramente suas dependências
- Incluir mensagens de erro úteis
- Tratar casos de borda com elegância

As linguagens suportadas dependem da implementação do agente. Opções comuns: Python, Bash e JavaScript.

### `references/`

Documentação adicional que os agentes leem quando necessário:

- `REFERENCE.md`, referência técnica detalhada
- `FORMS.md`, templates de formulário ou formatos de dados estruturados
- Arquivos por domínio (`finance.md`, `legal.md`, etc.)

Mantenha cada arquivo de referência focado. Os agentes os carregam sob demanda, então arquivos menores significam menos uso de contexto.

### `assets/`

Recursos estáticos:

- Templates (de documentos, de configuração)
- Imagens (diagramas, exemplos)
- Arquivos de dados (tabelas de lookup, schemas)

## Disclosure progressivo

Os agentes carregam skills de forma progressiva, puxando mais detalhe só conforme a tarefa exige. As skills devem ser estruturadas para aproveitar isso:

1. Metadados (cerca de 100 tokens): os campos `name` e `description` são carregados na inicialização para todas as skills
2. Instruções (recomendado abaixo de 5000 tokens): o corpo completo do `SKILL.md` é carregado quando a skill é ativada
3. Recursos (conforme necessário): arquivos (por exemplo, em `scripts/`, `references/` ou `assets/`) são carregados só quando exigidos

Mantenha o `SKILL.md` principal abaixo de 500 linhas. Mova material de referência detalhado para arquivos separados.

## Referências de arquivo

Ao referenciar outros arquivos na skill, use caminhos relativos a partir da raiz da skill:

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

Mantenha as referências de arquivo a um nível de profundidade do `SKILL.md`. Evite cadeias de referência muito aninhadas.

## Validação

Use a biblioteca de referência `skills-ref` para validar suas skills:

```bash
skills-ref validate ./my-skill
```

Isso verifica se o frontmatter do `SKILL.md` é válido e segue as convenções de nomes. Repositório: https://github.com/agentskills/agentskills/tree/main/skills-ref
