# Revisao de QA das fatias de UI do MVP Admissao Verificada

Documento de revisao de consistencia das cinco fatias verticais recem-criadas
(veiculos, vistorias, situacoes de boleto, eventos do mes e exportacao) entre si,
contra a fatia de referencia (associados) e contra a fundacao (helpers, ADR-002 e
migrations).

Data da revisao: 2026-05-29.

## Escopo conferido

Route handlers, schemas zod, exportador TypeScript, paginas de lista e de
cadastro, layout de navegacao e migrations correspondentes. Itens verificados:

1. Checagem de sessao (401), validacao (422) e inferencia do `associacao_id` do
   operador, no mesmo padrao de associados.
2. Uso de `lib/competencia.ts` e `lib/dominio.ts` sem redefinicao local.
3. Marcadores de secao e segmentos coerentes com ADR-002 C4.
4. Finalizacao de vistoria levando `veiculos.status` para `ativo` (ADR-002 C1).
5. Exportador TypeScript espelhando `reference/exportador.py` (rotulos singulares
   na BASE, marcadores no RATEIO, cabecalho com VALOR RATEADO).
6. Nomes de tabela e coluna coerentes com as migrations.

## Inconsistencias encontradas

### 1. BASE trunca cotas fracionarias para inteiro (semantica de dado real)

Em `lib/export/xlsx.ts`, `gerarBase` grava a linha TOTAL com
`Math.round(d.baixadas)`, espelhando o `int(...)` de `exportador.py`. O harness
passa cotas inteiras na fixture, entao a paridade com o oraculo se mantem. Porem
o route handler `app/api/export/competencia/route.ts` calcula `baixadas` como a
soma de `veiculos.cota` (numeric fracionario, conforme ADR-002 C5: 1,0; 1,5; 2,0;
e assim por diante) arredondada a duas casas. Ao gravar na BASE, `Math.round`
descarta a fracao. Para dados reais com cotas fracionarias, o denominador
exportado divergira da soma de cotas consolidada. E preciso confirmar contra
SPEC-007 se a BASE espera a contagem inteira de veiculos por situacao ou a soma
de cotas; o nome interno (`baixadas` somando `cota`) e o destino (TOTAL inteiro)
estao em conflito conceitual. Item de maior atencao desta revisao.

### 2. Consolidacao usa soma de cotas, BASE usa contagem implicita

Relacionado ao item 1. `app/api/situacoes-boleto/consolidacao/route.ts` devolve
`soma_cotas` (fracionario) e `qtd_veiculos` (inteiro) por segmento e situacao,
deixando a escolha para o consumidor. Ja o gerador da BASE recebe apenas a soma
de cotas e a trunca. As duas leituras do mesmo dado (consolidacao e BASE) nao
expoem o mesmo numero, o que dificulta a conferencia visual entre a tela de
consolidacao e o arquivo exportado.

### 3. Ordenacao do RATEIO por data textual (nao cronologica)

`gerarRateio` ordena por `data.localeCompare`, com `data` no formato
`dd/mm/aaaa`. O `exportador.py` faz `sorted(..., key=lambda e: e["data"])`, tambem
sobre `dd/mm/aaaa`. Ambos ordenam lexicograficamente, nao cronologicamente, de
modo que a paridade entre TypeScript e Python se mantem (que e o requisito do
harness). Registra-se apenas que a ordem FIFO comentada no codigo nao corresponde
a ordem cronologica real quando os dias cruzam meses; nao e divergencia entre os
dois exportadores, e sim entre o comentario e o comportamento.

### 4. Finalizacao de veiculo nao reverte vistoria em caso de falha parcial

`app/api/vistorias/[id]/finalizar/route.ts` cumpre o ADR-002 C1: leva
`veiculos.status` para `ativo` apos marcar a vistoria como `finalizada`. Porem as
operacoes nao sao transacionais (sao chamadas sequenciais via service_role). Se a
atualizacao do veiculo falhar, a vistoria fica `finalizada` e o veiculo permanece
`pendente_vistoria`, exigindo correcao manual. O proprio codigo documenta a
escolha e apenas registra o erro em log. Para o MVP e aceitavel, mas convem expor
como limite conhecido, ja que a tela de situacao de boleto bloqueia veiculo nao
`ativo` (AC-007), criando dependencia entre as duas fatias.

### 5. Divergencia menor de estilo nos comentarios (acentuacao e cabecalho)

Os arquivos de associados, vistorias e parte de veiculos usam acentuacao plena em
comentarios (por exemplo, "validacao autoritativa" com til e cedilha), enquanto
situacoes-boleto, eventos e trechos de veiculos usam comentarios sem acento. Nao
afeta funcionamento, mas quebra a uniformidade do padrao de referencia. Recomenda-
se padronizar a acentuacao dos comentarios em toda a base.

## Itens verificados sem divergencia

- Todas as cinco fatias e os endpoints auxiliares (`simular-cota`,
  `scripts-vistoria`, `consolidacao`, `capturas`, `finalizar`) chamam
  `supabase.auth.getUser()` e retornam 401 quando nao ha sessao, no mesmo formato
  de associados (`{ error: "nao autenticado" }`).
- Validacao de payload com schema zod e retorno 422 com
  `{ error: "dados invalidos", detalhes: parsed.error.flatten() }` em todas as
  rotas de escrita, identico a associados. As variacoes de 422 adicionais
  (competencia, fipe_valor, multipart) sao especificas e justificadas.
- Inferencia do `associacao_id`: todas leem `operadores` pelo `user.id` e
  retornam 401 "operador sem associacao" quando ausente. Nenhuma fatia aceita
  `associacao_id` vindo da URL ou do corpo. O isolamento por tenant e a unicidade
  (409 em codigo 23505) ficam a cargo da RLS e das constraints, conforme ADR-002
  C2 e o padrao de associados.
- `lib/competencia.ts` e usado por situacoes-boleto, eventos e exportacao
  (`competenciaValida`, `competenciaParaDate`, `competenciaParaExibicao`). Nenhuma
  fatia redefine validacao ou conversao de competencia localmente.
- `lib/dominio.ts` e a fonte unica de `SEGMENTOS`, `MARCADORES_SECAO`,
  `SEGMENTO_SINGULAR`, `COBERTURAS_TERCEIROS`. Os schemas de veiculo e evento e o
  exportador consomem essas constantes sem recriar listas. O enum de situacoes
  fica em `lib/schemas/situacao-boleto.ts` (`SITUACOES`) e e reutilizado pela
  consolidacao, sem duplicacao.
- Marcadores de secao: o enum de `marcador_secao` na migration 0006, a constante
  `MARCADORES_SECAO` e o `parsearMarcador` da exportacao geram exatamente os seis
  marcadores do ADR-002 C4 (LEVES/MOTOS/PESADOS x ASSOCIADOS/TERCEIROS).
- Conversao plural para singular do segmento na BASE usa `SEGMENTO_SINGULAR`
  (LEVES para LEVE, MOTOS para MOTO, PESADOS para PESADO), igual ao
  `SEG_SINGULAR` do `exportador.py`. Ordem dos blocos e colunas iniciais batem
  (`SEG_ORDER` PESADOS/MOTOS/LEVES; `BLOCK_START` 1/6/11).
- Finalizacao de vistoria: confirma transicao para `ativo` (ADR-002 C1) e e
  idempotente quanto a imutabilidade (403 quando ja `finalizada` ou `expirada`,
  CA-004-11).
- Exportador TypeScript x Python: cabecalho do RATEIO identico, incluindo
  PROTOCOLO (col 1), MOTIVO (col 3), ENVOLVIMENTO (col 4), PLACA (col 6),
  DATA COMUNIC (col 8), TIPO EVENTO (col 9) e VALOR RATEADO (col 11). Marcador na
  coluna A na primeira linha de cada grupo. Protocolo numerico como inteiro,
  alfanumerico como texto. Filtro de protocolo ausente ou valor menor ou igual a
  zero presente nos dois lados.
- Nomes de tabela e coluna conferem com as migrations: `veiculos`,
  `faixas_cota`, `scripts_vistoria`, `etapas_script`, `vistorias`,
  `capturas_vistoria`, `timeline_vistoria`, `situacoes_boleto`, `eventos_mes`,
  `exportacoes`. Colunas referenciadas nos handlers (por exemplo
  `substituida_por`, `token_sessao`, `marcador_secao`, `valor_rateado`,
  `data_comunicacao`, `cota`, `cobertura_terceiros`) existem nos respectivos
  esquemas. A trilha `timeline_vistoria` recebe escrita apenas via service_role,
  coerente com a politica que so libera SELECT pelo operador.

## Pendencias

### P1. Validacao de build com pnpm (bloqueante para fechar a revisao)

As dependencias nao foram instaladas (`node_modules` ausente). Nao foi possivel
rodar `pnpm install`, `pnpm typecheck` (`tsc --noEmit`) nem `pnpm build`. Os
scripts existem no `package.json` e `exceljs` consta nas dependencias. Antes de
qualquer aprovacao definitiva, executar:

```
pnpm install
pnpm typecheck
pnpm build
```

Pontos de TypeScript a observar no typecheck, por dependerem de tipagem gerada do
Supabase que ainda nao existe no repo: os `select` com joins aninhados em
vistorias e situacoes-boleto usam castings manuais (`as { ... }`) que mascaram a
ausencia de tipos gerados; sem os tipos do banco o compilador aceita, mas convem
gerar os tipos e revisar.

### P2. Paridade do exportador TypeScript contra o harness

O `reference/harness.py` so exercita o `exportador.py` (Python). Nao existe ainda
um harness que rode o exportador TypeScript (`lib/export/xlsx.ts`) e compare os
arquivos gerados, ou que alimente os arquivos do TypeScript ao motor para checar
`invariante_ok`. A paridade entre os dois esta verificada apenas por inspecao de
codigo nesta revisao. Pendente: gerar BASE e RATEIO pelo caminho TypeScript com a
mesma fixture do harness e confirmar `detectar_tipo`, roundtrip de cotas e
`invariante_ok`. Atencao ao item 1 das inconsistencias, que so aparece com cotas
fracionarias (a fixture atual usa inteiros e nao o exercita).

### P3. Confirmar semantica da BASE (contagem x soma de cotas)

Resolver os itens 1 e 2 das inconsistencias contra SPEC-007: definir se a linha
TOTAL da BASE carrega numero de veiculos (inteiro) ou soma de cotas (fracionario)
e alinhar `gerarBase`, o route handler de exportacao e a consolidacao a essa
decisao unica.

### P4. Atomicidade da finalizacao de vistoria

Avaliar mover a dupla atualizacao (vistoria e veiculo) e o registro de timeline
para uma RPC transacional no banco, eliminando o estado parcial descrito no item
4. Pode ficar para fase posterior, mas precisa estar registrado como limite
conhecido do MVP.

### P5. Padronizacao de acentuacao nos comentarios

Uniformizar a acentuacao dos comentarios entre as fatias (item 5).

## Parecer por fatia

- Veiculos: go com ressalva. Sessao, validacao, inferencia de tenant, uso de
  `dominio.ts` e nomes de coluna corretos; calculo de cota por faixas vigente
  coerente com SPEC-003. Ressalva: depende de P1 (build) e da decisao de P3 nao
  alterar a semantica de cota usada na exportacao.
- Vistorias: go com ressalva. Fluxo de inicio, captura, finalizacao e timeline
  corretos; finalizacao leva veiculo a `ativo` (ADR-002 C1). Ressalva: P4
  (atomicidade) e P1 (build, castings manuais sem tipos gerados).
- Situacoes de boleto: go com ressalva. Padrao identico a associados, uso de
  `competencia.ts`, bloqueio de veiculo nao `ativo` (AC-007) e consolidacao por
  segmento coerentes. Ressalva: P3 (alinhamento da semantica de cota com a BASE).
- Eventos do mes: go com ressalva. Marcadores conferem com ADR-002 C4 e a
  migration; unicidade de protocolo por competencia tratada como 409. Ressalva:
  apenas P1 (build).
- Exportacao: go com ressalva. Exportador TypeScript espelha o Python por
  inspecao (rotulos singulares na BASE, seis marcadores no RATEIO, cabecalho com
  VALOR RATEADO). Ressalva: P2 (harness do caminho TypeScript ainda nao roda) e
  P3/itens 1 e 2 (truncamento de cotas fracionarias), que sao os pontos de maior
  risco antes da aprovacao definitiva.

## Veredito geral

Go com ressalva. As cinco fatias seguem fielmente o padrao da fatia de referencia
em sessao, validacao, isolamento por tenant e reuso dos helpers, e os layouts da
BASE e do RATEIO espelham o oraculo Python por inspecao. A liberacao definitiva
depende de fechar P1 (build com pnpm) e P2 (paridade do exportador TypeScript
contra o harness e o motor), alem de resolver a semantica de cota da BASE (P3).
