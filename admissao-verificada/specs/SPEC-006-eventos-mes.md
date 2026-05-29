# SPEC-006 — Eventos do Mes

Status: rascunho. Data: 2026-05-29.
Responsavel: Engenheiro Backend.

---

## 1. Contexto

O arquivo RATEIO e o numerador do rateio: ele lista, mes a mes, cada evento
que gerou custo ou recuperacao para a associacao. O motor aprovado le esse
arquivo linha por linha, agrupando os eventos por marcador de secao (segmento
mais envolvimento), e usa os valores rateados para calcular o quanto cada
cota contribui.

Esta spec define o registro minimo de eventos que o app precisa capturar para
que a exportacao do RATEIO seja possivel e valida segundo o contrato descrito
em SPEC-000, secao 3. O calculo do rateio nao e responsabilidade do app; o
motor aprovado e o unico que calcula, a partir dos arquivos BASE e RATEIO
exportados.

Cada evento possui: marcador de secao (combinacao de segmento e envolvimento),
tipo de indenizacao (INTEGRAL ou PARCIAL), protocolo, motivo, placa, data de
comunicacao e valor rateado. Um evento sem protocolo ou com valor rateado
menor ou igual a zero nao deve ser exportado, conforme a regra do motor
(SPEC-000, secao 3). O app rejeita esses eventos ja na entrada, antes da
persistencia.

O marcador de secao combina o segmento do veiculo (LEVES, MOTOS ou PESADOS)
com o envolvimento do evento (ASSOCIADOS quando o custo e do proprio grupo;
TERCEIROS quando e recuperacao de danos a terceiros). O envolvimento e
informado pelo operador no momento do cadastro do evento; nao e derivado da
cobertura de terceiros do veiculo (ADR-002, C4; SPEC-000, secao 3). A
combinacao resulta nos seis valores canonicos aceitos pelo motor: LEVES
ASSOCIADOS, LEVES TERCEIROS, MOTOS ASSOCIADOS, MOTOS TERCEIROS, PESADOS
ASSOCIADOS, PESADOS TERCEIROS.

Nao entra no escopo desta spec nenhum workflow de sinistro (reparo, oficina,
pericia, acompanhamento de status). O registro e o minimo necessario para
compor o arquivo RATEIO da competencia.

O isolamento por associacao (tenant) segue ADR-002, C2: toda policy RLS usa
o claim `associacao_id` do JWT, sem subquery em `operadores`.

---

## 2. Requisitos

Esta spec cobre os seguintes requisitos do MVP-SCOPE:

- RF-EVT-01: O sistema DEVE cadastrar evento com marcador de secao (segmento
  mais envolvimento associado ou terceiro), tipo (INTEGRAL ou PARCIAL),
  protocolo, placa, data de comunicacao e valor rateado.
- RF-EVT-02: O sistema DEVE rejeitar evento sem protocolo ou com valor rateado
  menor ou igual a zero.

Requisitos nao funcionais aplicaveis:

- RNF-01: Isolamento por associacao (RLS).
- RNF-02: Trilha de auditoria imutavel nas operacoes de admissao.
- RNF-04: Comunicacao por HTTPS; dados pessoais tratados conforme a LGPD.

---

## 3. Criterios de Aceite

### AC-001 — Cadastro de evento valido

Given um operador autenticado na associacao A,
When envia marcador de secao valido, tipo valido, protocolo preenchido,
placa preenchida, data de comunicacao valida e valor rateado positivo,
Then o sistema persiste o evento com status `ativo`, retorna HTTP 201 e o
corpo contem o `id` gerado e todos os campos informados.

### AC-002 — Rejeicao por protocolo ausente

Given um operador autenticado,
When envia um evento sem o campo `protocolo` ou com `protocolo` vazio,
Then o sistema rejeita com HTTP 422 e mensagem indicando que o protocolo e
obrigatorio, sem gravar registro.

### AC-003 — Rejeicao por valor rateado zero

Given um operador autenticado,
When envia um evento com `valor_rateado` igual a zero,
Then o sistema rejeita com HTTP 422 e mensagem indicando que o valor rateado
deve ser maior que zero, sem gravar registro.

### AC-004 — Rejeicao por valor rateado negativo

Given um operador autenticado,
When envia um evento com `valor_rateado` negativo,
Then o sistema rejeita com HTTP 422 e mensagem indicando que o valor rateado
deve ser maior que zero, sem gravar registro.

### AC-005 — Rejeicao por marcador de secao invalido

Given um operador autenticado,
When envia um valor de `marcador_secao` diferente dos seis valores aceitos
(LEVES ASSOCIADOS, LEVES TERCEIROS, MOTOS ASSOCIADOS, MOTOS TERCEIROS,
PESADOS ASSOCIADOS, PESADOS TERCEIROS),
Then o sistema rejeita com HTTP 422 e mensagem indicando marcador invalido,
sem gravar registro.

### AC-006 — Rejeicao por tipo invalido

Given um operador autenticado,
When envia um valor de `tipo` diferente de INTEGRAL ou PARCIAL,
Then o sistema rejeita com HTTP 422 e mensagem indicando tipo invalido, sem
gravar registro.

### AC-007 — Isolamento por associacao

Given a associacao A possui dois eventos e a associacao B possui tres,
When um operador da associacao A lista os eventos da competencia,
Then recebe exatamente os dois da associacao A, sem nenhum dado da
associacao B.

### AC-008 — Filtro por competencia

Given a associacao A possui eventos em 2025-11 e em 2025-12,
When o operador lista eventos com competencia 2025-12,
Then recebe apenas os eventos da competencia 2025-12.

### AC-009 — Protocolo duplicado na mesma competencia e associacao

Given a associacao A ja possui um evento com protocolo P001 na competencia
2025-12,
When um operador da associacao A tenta cadastrar outro evento com o mesmo
protocolo na mesma competencia,
Then o sistema rejeita com HTTP 409 e mensagem indicando duplicidade de
protocolo na competencia.

### AC-010 — Contribuicao do evento para o RATEIO exportado

Given a associacao A possui eventos validos na competencia 2025-12,
When o app exporta o RATEIO da competencia 2025-12,
Then cada evento aparece como uma linha sob o marcador de secao
correspondente, com tipo, protocolo, placa, data de comunicacao e valor
rateado, e `detectar_tipo` reconhece o arquivo como RATEIO.

### AC-011 — Invariante de fechamento

Given BASE e RATEIO gerados a partir da base do app para uma competencia
de teste,
When o harness de reconciliacao roda o motor aprovado sobre os dois arquivos,
Then o motor processa sem erro e o invariante de fechamento e igual a zero.

---

## 4. Modelo de Dados

### 4.1 Tabela `eventos_mes`

```sql
create table eventos_mes (
  id                uuid primary key default gen_random_uuid(),
  associacao_id     uuid not null references associacoes(id) on delete restrict,
  competencia       date not null,
    -- primeiro dia do mes de referencia; ex.: 2025-12-01 para dez/2025
  marcador_secao    text not null
                      check (marcador_secao in (
                        'LEVES ASSOCIADOS',
                        'LEVES TERCEIROS',
                        'MOTOS ASSOCIADOS',
                        'MOTOS TERCEIROS',
                        'PESADOS ASSOCIADOS',
                        'PESADOS TERCEIROS'
                      )),
  tipo              text not null
                      check (tipo in ('INTEGRAL', 'PARCIAL')),
  protocolo         text not null,
  motivo            text,
  placa             text not null,
  data_comunicacao  date not null,
  valor_rateado     numeric(14,2) not null check (valor_rateado > 0),
  status            text not null default 'ativo'
                      check (status in ('ativo', 'cancelado')),
  criado_em         timestamptz not null default now(),
  atualizado_em     timestamptz not null default now()
);
```

Restricoes adicionais:

```sql
-- protocolo unico dentro de uma competencia e associacao
alter table eventos_mes
  add constraint eventos_mes_protocolo_competencia_unique
  unique (associacao_id, competencia, protocolo);

-- indice para exportacao do RATEIO (filtra por associacao e competencia)
create index eventos_mes_associacao_competencia_idx
  on eventos_mes (associacao_id, competencia)
  where status = 'ativo';

-- indice para buscas por placa dentro de uma associacao
create index eventos_mes_associacao_placa_idx
  on eventos_mes (associacao_id, placa);

-- indice para buscas por protocolo
create index eventos_mes_associacao_protocolo_idx
  on eventos_mes (associacao_id, protocolo);
```

Notas:

- O campo `competencia` armazena o primeiro dia do mes de referencia
  (day = 01). O backend normaliza qualquer data fornecida para o primeiro
  dia do mes antes de persistir.
- O campo `motivo` e opcional na entrada: o motor aprovado usa o valor se
  presente e tolera celulas vazias (SPEC-000, secao 3).
- O campo `placa` e armazenado sem hifen e em maiusculas, seguindo a mesma
  normalizacao da tabela `veiculos` (SPEC-003). A placa nao precisa
  necessariamente existir na tabela `veiculos` da associacao no momento do
  cadastro do evento (pode ser um terceiro envolvido, por exemplo).
- O campo `status` permite cancelar um evento sem apaga-lo, preservando a
  trilha. Eventos com status `cancelado` nao sao incluidos na exportacao
  do RATEIO.
- A restricao de protocolo unico por competencia e associacao impede
  duplicatas. Se o mesmo protocolo precisar gerar duas linhas no RATEIO
  (INTEGRAL e um ajuste PARCIAL, por exemplo), o operador deve usar
  protocolos distintos.

### 4.2 Tabela `eventos_mes_audit`

Registro imutavel de cada operacao sobre `eventos_mes`, conforme RNF-02.

```sql
create table eventos_mes_audit (
  id              bigint generated always as identity primary key,
  evento_id       uuid not null,
  associacao_id   uuid not null,
  operador_id     uuid not null,   -- auth.uid() no momento da operacao
  operacao        text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes   jsonb,           -- null em INSERT
  payload_depois  jsonb,           -- null em DELETE
  ocorrido_em     timestamptz not null default now()
);
```

A trilha e preenchida por trigger na tabela `eventos_mes`. Nao ha endpoint
de escrita direta nessa tabela; ela e somente leitura para o app.

### 4.3 Politica RLS

Forma unica de isolamento (ADR-002, C2): claim customizado `associacao_id`
no JWT. As policies usam `auth.jwt() ->> 'associacao_id'`. Proibido subquery
em `operadores` dentro de policy para evitar N+1.

```sql
-- habilitar RLS
alter table eventos_mes enable row level security;
alter table eventos_mes_audit enable row level security;

-- operadores so enxergam eventos da propria associacao
create policy eventos_mes_isolamento on eventos_mes
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- auditoria: leitura restrita a operadores da mesma associacao
create policy eventos_mes_audit_leitura on eventos_mes_audit
  for select
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- auditoria: sem escrita direta pelo app (apenas via trigger)
create policy eventos_mes_audit_sem_insert on eventos_mes_audit
  for insert
  with check (false);
```

---

## 5. API

Base de URL: `/api/eventos`

Todas as rotas exigem sessao ativa. O `associacao_id` e inferido do operador
logado; nao e um parametro de URL.

### 5.1 POST /api/eventos

Cria um novo evento do mes.

Request body:

```json
{
  "competencia":        "AAAA-MM, obrigatorio",
  "marcador_secao":     "LEVES ASSOCIADOS | LEVES TERCEIROS | MOTOS ASSOCIADOS | MOTOS TERCEIROS | PESADOS ASSOCIADOS | PESADOS TERCEIROS, obrigatorio",
  "tipo":               "INTEGRAL | PARCIAL, obrigatorio",
  "protocolo":          "string nao vazia, obrigatorio",
  "motivo":             "string, opcional",
  "placa":              "string nao vazia, obrigatorio",
  "data_comunicacao":   "YYYY-MM-DD, obrigatorio",
  "valor_rateado":      "number > 0, obrigatorio"
}
```

O campo `competencia` aceita o formato `AAAA-MM` (ex.: `2025-12`) e e
convertido internamente para `AAAA-MM-01` antes da persistencia.

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Criado. Body: `{ id, competencia, marcador_secao, tipo, protocolo, motivo, placa, data_comunicacao, valor_rateado, status, criado_em }` |
| 401  | Nao autenticado. |
| 409  | Protocolo ja existe nesta competencia e associacao. |
| 422  | Protocolo ausente ou vazio, valor_rateado menor ou igual a zero, marcador_secao invalido, tipo invalido, placa ausente, data_comunicacao invalida, ou competencia invalida. |

### 5.2 GET /api/eventos

Lista os eventos da associacao do operador logado.

Query params opcionais:

| Param              | Tipo   | Descricao |
|--------------------|--------|-----------|
| `competencia`      | string | Filtra por competencia no formato AAAA-MM. |
| `marcador_secao`   | string | Filtra por marcador de secao. |
| `tipo`             | string | Filtra por INTEGRAL ou PARCIAL. |
| `placa`            | string | Busca parcial por placa (case-insensitive). |
| `status`           | string | Filtra por status. Padrao: `ativo`. |
| `page`             | int    | Pagina (base 1). Padrao: 1. |
| `per_page`         | int    | Registros por pagina. Padrao: 50. Maximo: 200. |

Response 200:

```json
{
  "data": [
    {
      "id", "competencia", "marcador_secao", "tipo", "protocolo",
      "motivo", "placa", "data_comunicacao", "valor_rateado",
      "status", "criado_em"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 50
}
```

### 5.3 GET /api/eventos/:id

Retorna os dados de um evento pelo id.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Dados do evento. Mesmo shape do item em GET /api/eventos. |
| 401  | Nao autenticado. |
| 404  | Evento nao encontrado na associacao do operador. |

A RLS garante que um id pertencente a outra associacao retorna 404, sem
vazar a existencia do registro.

### 5.4 PATCH /api/eventos/:id

Atualiza campos editaveis de um evento. Campos editaveis: `marcador_secao`,
`tipo`, `motivo`, `placa`, `data_comunicacao`, `valor_rateado`, `status`.

O campo `protocolo` nao e editavel apos o cadastro, pois serve como
identificador de negocio. O campo `competencia` tambem nao e editavel; para
mover um evento de competencia, o operador deve cancelar e recriar.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Atualizado. Body: dados atualizados no mesmo shape. |
| 401  | Nao autenticado. |
| 404  | Nao encontrado na associacao. |
| 422  | Valor_rateado menor ou igual a zero, marcador_secao invalido, tipo invalido, ou status invalido. |

Nota: a alteracao do campo `status` para `cancelado` retira o evento da
exportacao do RATEIO. Essa operacao e auditada.

### 5.5 Logica de exportacao (servico interno)

Este endpoint nao e exposto diretamente; e chamado pelo modulo de exportacao
da SPEC-000.

Contrato interno:

```
listar_eventos_para_rateio(associacao_id, competencia) ->
  lista de eventos com status = 'ativo',
  ordenados por marcador_secao e depois por data_comunicacao (FIFO),
  com os campos: marcador_secao, tipo, protocolo, motivo, placa,
  data_comunicacao, valor_rateado
```

A ordenacao por `data_comunicacao` dentro de cada secao implementa a
regra FIFO descrita em SPEC-000, secao 3.

---

## 6. UI

### 6.1 Tela: lista de eventos da competencia

Rota sugerida: `/eventos`

Elementos:
- Seletor de competencia (mes e ano) no topo, com valor padrao no mes
  anterior ao atual.
- Tabela paginada com colunas: Protocolo, Placa, Marcador de Secao, Tipo,
  Data de Comunicacao, Valor Rateado, Status.
- Campo de busca por placa ou protocolo.
- Filtros de marcador de secao e tipo.
- Botao "Novo evento" que abre o formulario de cadastro.
- Linha clicavel que navega para o detalhe do evento.
- Total de valor rateado da competencia exibido como rodape da tabela
  (soma dos eventos ativos filtrados na tela).

### 6.2 Tela: formulario de cadastro de evento

Rota sugerida: `/eventos/novo`

Campos:
- Competencia (seletor de mes e ano, exibido como MM/AAAA; padrao: mes anterior; obrigatorio).
- Marcador de secao (seletor com os seis valores validos; obrigatorio).
- Tipo (seletor: INTEGRAL, PARCIAL; obrigatorio).
- Protocolo (texto; obrigatorio): campo de texto livre sem mascara.
- Motivo (texto; opcional).
- Placa (texto; obrigatorio): normalizacao aplicada no campo (sem hifen,
  maiusculas); sem validacao de formato exigida, pois a placa pode ser de
  um terceiro.
- Data de comunicacao (data; obrigatorio): formato dd/mm/aaaa na UI.
- Valor rateado (numerico positivo; obrigatorio).

Comportamento:
- Submit dispara POST /api/eventos.
- Em caso de 409, exibe mensagem: "Protocolo ja cadastrado nesta
  competencia."
- Em caso de 422, exibe a mensagem do campo correspondente abaixo do input.
- Em caso de sucesso, redireciona para a lista de eventos da competencia
  ou para o detalhe do evento criado, conforme decisao de UX.

### 6.3 Tela: detalhe e edicao do evento

Rota sugerida: `/eventos/:id`

Exibe os dados do evento. O protocolo e a competencia sao exibidos e nao
sao editaveis. Os demais campos podem ser editados pelo operador. O campo
`status` pode ser alterado para `cancelado` para retirar o evento da
exportacao.

Exibe tambem o historico de alteracoes do evento (leitura da trilha de
auditoria), com data, operador (referencia anonimizada se necessario pela
LGPD) e os campos alterados.

---

## 7. Observabilidade

- Logar no nivel INFO cada criacao e cancelamento de evento, com
  `evento_id`, `associacao_id`, `competencia` e `marcador_secao`. Nao
  incluir `valor_rateado` em claro no log.
- Logar no nivel WARN cada tentativa rejeitada por protocolo duplicado
  (409) ou validacao de entrada (422), com `associacao_id` e o tipo de
  rejeicao.
- Metrica recomendada: total de eventos ativos por competencia e por
  marcador de secao, por associacao, para acompanhar o volume do numerador
  do rateio.
- A tabela `eventos_mes_audit` e a trilha persistente; os logs de aplicacao
  sao complementares.

---

## 8. Seguranca e LGPD

- A placa e um dado de identificacao do veiculo; pode vincular
  indiretamente o associado. Nao incluir placas em claro em logs.
- O `protocolo` e um identificador de negocio do evento; nao contem dados
  pessoais por definicao, mas deve ser tratado com controle de acesso por
  RLS para evitar exposicao a outros tenants.
- O `valor_rateado` e um dado financeiro do evento; nao expor em logs de
  nivel INFO ou superior.
- O isolamento por RLS garante que eventos de uma associacao nao sao
  visiveis para operadores de outra (RNF-01).
- A trilha de auditoria e imutavel: sem endpoint de DELETE ou UPDATE em
  `eventos_mes_audit`; a policy RLS bloqueia insercao direta pelo app
  (RNF-02).
- A comunicacao e exclusivamente por HTTPS (RNF-04).
- Os campos `marcador_secao`, `tipo`, `protocolo`, `placa`,
  `data_comunicacao` e `valor_rateado` aparecem no arquivo RATEIO exportado
  (SPEC-000, secao 3). O uso desses campos na exportacao deve ser
  documentado como finalidade legitima no mapeamento de dados da LGPD do
  produto.

---

## 9. Testes

### 9.1 Testes unitarios (validacoes de entrada)

- Protocolo ausente: rejeitado com mensagem clara.
- Protocolo como string vazia: rejeitado.
- Valor rateado igual a zero: rejeitado.
- Valor rateado negativo: rejeitado.
- Valor rateado positivo: aceito.
- Marcador de secao com valor fora do conjunto de seis: rejeitado.
- Cada um dos seis marcadores validos: aceito.
- Tipo diferente de INTEGRAL e PARCIAL: rejeitado.
- INTEGRAL e PARCIAL: aceitos.
- Competencia no formato AAAA-MM: normalizada para AAAA-MM-01.
- Competencia com formato invalido: rejeitada com 422.
- Placa com hifen ou minusculas: normalizada (hifen removido, maiusculas)
  antes de persistir.

### 9.2 Testes de integracao (API)

- POST com dados validos retorna 201 com o evento persistido.
- POST sem protocolo retorna 422.
- POST com protocolo vazio retorna 422.
- POST com valor_rateado = 0 retorna 422.
- POST com valor_rateado negativo retorna 422.
- POST com marcador_secao invalido retorna 422.
- POST com tipo invalido retorna 422.
- POST com protocolo duplicado na mesma competencia e associacao retorna
  409.
- POST com protocolo duplicado em associacao diferente retorna 201
  (isolamento de tenant).
- GET /api/eventos retorna somente eventos da associacao do operador.
- GET /api/eventos?competencia=2025-12 retorna somente eventos dessa
  competencia.
- GET /api/eventos/:id de outra associacao retorna 404.
- PATCH com status=cancelado persiste e retira o evento da listagem padrao
  (status=ativo).
- PATCH tentando alterar o protocolo nao altera o valor persistido.
- PATCH tentando alterar a competencia nao altera o valor persistido.

### 9.3 Ligacao com o oraculo do motor aprovado

O conjunto de eventos ativos de uma competencia e o numerador do RATEIO.
A ligacao com o motor aprovado e verificada pelo harness de reconciliacao
(SPEC-000, secao 6):

1. Configurar uma associacao de teste com veiculos ativos e boletos baixados
   na competencia (SPEC-003, SPEC-005).
2. Cadastrar N eventos com marcadores de secao, tipos, protocolos, placas,
   datas e valores conhecidos e deterministicos.
3. Exportar BASE e RATEIO da competencia (SPEC-000).
4. Verificar que `detectar_tipo` reconhece cada arquivo com o tipo correto:
   BASE para o arquivo de cotas e RATEIO para o arquivo de eventos.
5. Verificar que cada evento ativo aparece no RATEIO sob o marcador de
   secao correto, com os campos exatos, na ordem FIFO por
   `data_comunicacao` dentro de cada secao.
6. Rodar o motor aprovado sobre BASE e RATEIO e confirmar que o invariante
   de fechamento e igual a zero.

A verificacao do invariante zero confirma que o numerador (eventos do RATEIO)
e o denominador (cotas baixadas da BASE) estao consistentes e no layout que
o motor espera. Qualquer divergencia de formato, ordem ou valor invalida o
aceite.

---

## 10. Rollout

1. Aplicar as migrations de banco (`eventos_mes`, `eventos_mes_audit`,
   constraints, indices, RLS, trigger de auditoria) em ambiente de
   desenvolvimento. A migration depende das migrations de `associacoes`
   (SPEC-001) e de `operadores` (SPEC-001) estarem aplicadas. Nao ha
   dependencia direta da tabela `veiculos` no schema, embora os dados
   estejam relacionados semanticamente.
2. Rodar os testes unitarios de validacao de entrada.
3. Rodar os testes de integracao da API.
4. Revisar a policy RLS com um segundo operador de tenant diferente (teste
   manual de isolamento).
5. Aprovar a spec com o Tech Lead e o Spec Lead antes de prosseguir para
   implementacao do frontend.
6. Apos o frontend concluir as telas de lista e cadastro, realizar o aceite
   funcional manual com base nos criterios da secao 3.
7. Executar o harness de reconciliacao (SPEC-000, secao 6) com eventos
   cadastrados via frontend para confirmar o aceite de ponta a ponta antes
   de declarar o modulo concluido.

---

## 11. Questoes em aberto

- Protocolo como identificador de negocio: a restricao de unicidade por
  protocolo, competencia e associacao impede que o mesmo protocolo gere
  duas linhas distintas (por exemplo, uma INTEGRAL e um ajuste PARCIAL).
  Definir se o caso de uso de ajuste parcial sobre um evento existente
  exige protocolos distintos ou se a unicidade deve ser relaxada para
  permitir multiplas linhas com o mesmo protocolo.
- Placa de terceiro: o app nao valida se a placa de um evento existe na
  tabela `veiculos` da associacao, pois o evento pode envolver um veiculo
  de terceiro. Confirmar se ha necessidade de distinguir, na tela, eventos
  de veiculos proprios versus terceiros, ou se o marcador de secao
  (ASSOCIADOS vs. TERCEIROS) e suficiente.
- Cancelamento versus exclusao: o MVP usa `status = cancelado` para
  desativar eventos, sem remocao fisica. Confirmar se o operador precisa
  de uma funcionalidade de exclusao logica com reversao ou se o
  cancelamento definitivo e suficiente.
- Importacao em lote: o MVP prev entrada manual evento a evento. Se o
  volume de eventos for alto, uma funcionalidade de importacao por planilha
  pode ser necessaria antes do primeiro uso em producao; avaliar se entra
  no MVP ou fica para fase posterior.
- Motivo obrigatorio ou opcional: o campo `motivo` e opcional no MVP, pois
  o motor tolera celulas vazias. Confirmar se a operacao exige o motivo
  como campo de controle interno antes da exportacao.
