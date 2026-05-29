# SPEC-003 — Cadastro de Veiculo e Cota

Status: rascunho. Data: 2026-05-29.
Responsavel: Engenheiro Backend.

---

## 1. Contexto

O veiculo e a unidade central do rateio. Cada veiculo pertence a um associado,
carrega um segmento (LEVES, MOTOS ou PESADOS) e uma cota calculada a partir
da faixa de valor FIPE. O segmento e exatamente o agrupador que o motor
aprovado usa para construir a BASE: cada coluna da BASE corresponde a um
segmento, e o denominador do rateio e a soma de cotas baixadas por segmento
na competencia (ver SPEC-000, secao 2 e secao 4).

A cota nao e um valor livre: ela e derivada da faixa de FIPE por uma tabela
parametrizavel que espelha a regra do motor aprovado (progressao por faixas
de 10 mil reais; cota especial para valores FIPE muito altos). O valor FIPE
informado no cadastro e o unico insumo necessario; o calculo e determinista
e reprodutivel a partir da tabela de parametros vigente.

A cobertura de terceiros (nenhuma, 50k, 100k) e um atributo do veiculo que
define o preco do produto Danos a Terceiros cobrado na competencia: nenhuma
corresponde ao preco zero, 50k ao preco 20, 100k ao preco 30 (valores de
referencia do motor, ADR-002 C5). A cobertura de terceiros NAO define o
envolvimento do evento no RATEIO; o marcador ASSOCIADOS ou TERCEIROS de cada
linha do RATEIO e determinado pelo proprio evento (SPEC-006), conforme
SPEC-000, secao 3 e ADR-002 C4.

Esta spec cobre apenas o cadastro do veiculo e o calculo da cota. A vistoria
que habilita o veiculo a admissao e tratada na SPEC-004. A situacao de boleto
por competencia e tratada na SPEC-005. Os eventos do mes que referenciam a
placa do veiculo sao tratados na SPEC-006.

O isolamento por associacao (tenant) e herdado da decisao de arquitetura
(ADR-001, item 2): toda tabela tem RLS vinculada ao tenant do operador logado.

---

## 2. Requisitos

Esta spec cobre os seguintes requisitos do MVP-SCOPE:

- RF-VEIC-01: O sistema DEVE cadastrar veiculo com placa, segmento, valor FIPE
  e cobertura de terceiros (nenhuma, 50k, 100k).
- RF-VEIC-02: O sistema DEVE validar a placa (padrao antigo e Mercosul).
- RF-VEIC-03: O sistema DEVE classificar o segmento em LEVES, MOTOS ou PESADOS.
- RF-VEIC-04: O sistema DEVE calcular a cota do veiculo pela faixa de FIPE,
  com a mesma regra do motor (parametrizavel).

Requisitos nao funcionais aplicaveis:

- RNF-01: Isolamento por associacao (RLS).
- RNF-02: Trilha de auditoria imutavel nas operacoes de admissao.
- RNF-04: Comunicacao por HTTPS; dados pessoais tratados conforme a LGPD.

---

## 3. Criterios de Aceite

### AC-001 — Cadastro com dados validos

Given um operador autenticado na associacao A e um associado cadastrado nessa
associacao,
When envia placa valida, segmento valido, valor FIPE positivo e cobertura de
terceiros valida para o endpoint de criacao,
Then o sistema calcula a cota pela tabela de faixas vigente, persiste o
veiculo com status `pendente_vistoria`, retorna HTTP 201 e o corpo contem
o `id` gerado, a placa, o segmento, o valor FIPE, a cobertura de terceiros
e a cota calculada.

### AC-002 — Placa no padrao antigo invalida

Given um operador autenticado,
When envia uma placa que nao segue nem o padrao antigo (tres letras e quatro
digitos, ex.: ABC-1234) nem o Mercosul (tres letras, um digito, uma letra e
dois digitos, ex.: ABC1D23),
Then o sistema rejeita com HTTP 422 e mensagem indicando placa invalida, sem
gravar registro.

### AC-003 — Placa no padrao antigo valida

Given um operador autenticado,
When envia uma placa no padrao antigo com tres letras e quatro digitos
(com ou sem hifen),
Then o sistema aceita e persiste normalmente.

### AC-004 — Placa no padrao Mercosul valida

Given um operador autenticado,
When envia uma placa no padrao Mercosul (tres letras, um digito, uma letra,
dois digitos),
Then o sistema aceita e persiste normalmente.

### AC-005 — Segmento invalido

Given um operador autenticado,
When envia um valor de segmento diferente de LEVES, MOTOS ou PESADOS,
Then o sistema rejeita com HTTP 422 e mensagem indicando segmento invalido,
sem gravar registro.

### AC-006 — Placa duplicada na mesma associacao

Given a associacao A ja possui um veiculo com a placa ABC1234,
When um operador da associacao A tenta cadastrar outro veiculo com a mesma
placa,
Then o sistema rejeita com HTTP 409 e mensagem indicando duplicidade de placa
na associacao.

### AC-007 — Calculo de cota por faixa de FIPE

Given a tabela de faixas parametrizavel esta vigente,
When o operador cadastra um veiculo com valor FIPE que se enquadra em uma
faixa especifica,
Then a cota calculada e exatamente o valor definido para aquela faixa na
tabela, sem arredondamento adicional pelo app.

### AC-008 — Cota especial para FIPE acima do limite de faixas

Given a tabela de faixas define um limite superior,
When o operador cadastra um veiculo com valor FIPE superior ao ultimo limite
de faixa,
Then o sistema aplica a cota especial definida para esse caso (faixa "acima
do limite") sem rejeitar o cadastro.

### AC-009 — Valor FIPE zero ou negativo rejeitado

Given um operador autenticado,
When envia valor FIPE menor ou igual a zero,
Then o sistema rejeita com HTTP 422 e mensagem indicando que o valor FIPE
deve ser positivo, sem gravar registro.

### AC-010 — Cobertura de terceiros invalida

Given um operador autenticado,
When envia um valor de cobertura de terceiros diferente de `nenhuma`, `50k`
ou `100k`,
Then o sistema rejeita com HTTP 422 e mensagem indicando cobertura invalida,
sem gravar registro.

### AC-011 — Veiculo vinculado ao associado correto

Given um operador da associacao A,
When cadastra um veiculo informando o `associado_id` de um associado da
associacao B,
Then o sistema rejeita com HTTP 404 (o associado nao e visivel pela RLS),
sem gravar o veiculo.

### AC-012 — Listagem filtrada por associacao

Given a associacao A possui tres veiculos e a associacao B possui dois,
When um operador da associacao A lista os veiculos,
Then recebe exatamente os tres da associacao A, sem nenhum dado da
associacao B.

### AC-013 — Contribuicao do veiculo para a BASE

Given um veiculo com segmento LEVES, vistoria finalizada (SPEC-004) e boleto
baixado na competencia (SPEC-005),
When o app exporta a BASE da competencia,
Then a cota do veiculo aparece na coluna BAIXADO do segmento LEVE do arquivo
BASE, e `detectar_tipo` reconhece o arquivo como BASE.

---

## 4. Modelo de Dados

### 4.1 Tabela `veiculos`

```sql
create table veiculos (
  id              uuid primary key default gen_random_uuid(),
  associacao_id   uuid not null references associacoes(id) on delete restrict,
  associado_id    uuid not null references associados(id) on delete restrict,
  placa           text not null,           -- normalizada: sem hifen, maiusculas
  segmento        text not null
                    check (segmento in ('LEVES', 'MOTOS', 'PESADOS')),
  fipe_valor      numeric(12,2) not null check (fipe_valor > 0),
  cobertura_terceiros text not null default 'nenhuma'
                    check (cobertura_terceiros in ('nenhuma', '50k', '100k')),
  cota            numeric(10,2) not null check (cota > 0),
  status          text not null default 'pendente_vistoria'
                    check (status in (
                      'pendente_vistoria',
                      'ativo',
                      'inativo'
                    )),
  criado_em       timestamptz not null default now(),
  atualizado_em   timestamptz not null default now()
);
```

Restricoes adicionais:

```sql
-- placa unica dentro da associacao
alter table veiculos
  add constraint veiculos_placa_associacao_unique
  unique (associacao_id, placa);

-- indice para buscas por placa dentro de uma associacao
create index veiculos_associacao_placa_idx
  on veiculos (associacao_id, placa);

-- indice para consultas por associado
create index veiculos_associado_idx
  on veiculos (associado_id);

-- indice para consultas por segmento (usado na geracao da BASE)
create index veiculos_associacao_segmento_idx
  on veiculos (associacao_id, segmento)
  where status = 'ativo';
```

Notas:
- A placa e armazenada sem hifen e em maiusculas. A normalizacao ocorre no
  backend antes da persistencia e antes da validacao de formato.
- O campo `cota` e calculado no momento do cadastro e recalculado se o valor
  FIPE for alterado. Ele espelha a regra da tabela `faixas_cota` vigente no
  momento da operacao.
- O enum de status e exatamente: `pendente_vistoria`, `ativo`, `inativo`.
  Nao existe o valor `admitido`. O veiculo nasce `pendente_vistoria`; a
  vistoria finalizada (SPEC-004) transiciona o veiculo para `ativo`. A
  admissao e o processo; o estado resultante e `ativo`. O status `inativo`
  retira o veiculo do denominador da BASE (ADR-002 C1).
- A placa e o identificador de negocio do veiculo no arquivo RATEIO (SPEC-000,
  secao 3). A unicidade por associacao garante que a placa identifica o
  veiculo sem ambiguidade dentro do tenant.

### 4.2 Tabela `faixas_cota`

Parametros de calculo da cota por faixa de FIPE. Administrada pelo operador
da associacao; alteracoes geram nova versao (ver nota de versionamento abaixo).

```sql
create table faixas_cota (
  id              uuid primary key default gen_random_uuid(),
  associacao_id   uuid not null references associacoes(id) on delete restrict,
  fipe_ate        numeric(12,2),           -- null indica "acima do ultimo limite"
  cota_valor      numeric(10,2) not null check (cota_valor > 0),
  vigente_desde   date not null,
  criado_em       timestamptz not null default now()
);
```

Notas:
- As faixas de uma associacao devem ser inseridas em ordem crescente de
  `fipe_ate`. A faixa com `fipe_ate` nulo representa o intervalo aberto
  superior (cota especial para FIPE muito alto), obrigatoria para que o
  calculo seja completo.
- A coluna `vigente_desde` permite alterar a tabela de faixas sem afetar
  cotas ja calculadas: o calculo usa as faixas cuja `vigente_desde` e menor
  ou igual a data de cadastro do veiculo.
- No MVP, a tabela de faixas e preenchida manualmente pelo operador da
  associacao antes do primeiro cadastro de veiculo. Nao ha interface de
  administracao da tabela no MVP; a insercao e por migration ou por script de
  seed.
- A logica de selecao da faixa: dado `fipe_valor` do veiculo, localizar a
  primeira linha (ordem crescente de `fipe_ate`) cuja `fipe_ate` e maior ou
  igual ao `fipe_valor`; se nenhuma linha satisfizer (todos os limites sao
  menores), usar a linha com `fipe_ate` nulo.
- Seed de referencia (ADR-002 C5, espelha `cotas_por_fipe` em `rules.py`):
  cota base 1,0 para FIPE ate 10.000; acrescimo de 0,5 por faixa de 10.000;
  cota especial de 20,0 para FIPE acima de 450.000 (faixa com `fipe_ate`
  nulo, sem progressao linear). O seed inicial do ambiente de teste DEVE
  reproduzir esses valores exatos. A tabela e parametrizavel, mas o default
  e identico ao motor.

### 4.3 Tabela `veiculos_audit`

Registro imutavel de cada operacao sobre `veiculos`, conforme RNF-02.

```sql
create table veiculos_audit (
  id              bigint generated always as identity primary key,
  veiculo_id      uuid not null,
  associacao_id   uuid not null,
  operador_id     uuid not null,   -- auth.uid() no momento da operacao
  operacao        text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes   jsonb,           -- null em INSERT
  payload_depois  jsonb,           -- null em DELETE
  ocorrido_em     timestamptz not null default now()
);
```

A trilha e preenchida por trigger na tabela `veiculos`. Nao ha endpoint de
escrita direta nessa tabela; ela e somente leitura para o app.

### 4.4 Politica RLS

```sql
-- habilitar RLS
alter table veiculos enable row level security;
alter table faixas_cota enable row level security;
alter table veiculos_audit enable row level security;

-- operadores so enxergam veiculos da propria associacao
create policy veiculos_isolamento on veiculos
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- operadores so enxergam faixas da propria associacao
create policy faixas_cota_isolamento on faixas_cota
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- auditoria: leitura restrita a operadores da mesma associacao
create policy veiculos_audit_leitura on veiculos_audit
  for select
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- auditoria: sem escrita direta pelo app (apenas via trigger)
create policy veiculos_audit_sem_insert on veiculos_audit
  for insert
  with check (false);
```

As policies usam o claim customizado `associacao_id` do JWT (ADR-002 C2).
Subquery em `operadores` dentro de policy e proibida para evitar N+1. O
claim e incluido no token pelo backend no momento da autenticacao.

---

## 5. API

Base de URL: `/api/veiculos`

Todas as rotas exigem sessao ativa. O `associacao_id` e inferido do operador
logado; nao e um parametro de URL.

### 5.1 POST /api/veiculos

Cria um novo veiculo e calcula a cota.

Request body:

```json
{
  "associado_id":         "uuid, obrigatorio",
  "placa":                "string, obrigatorio",
  "segmento":             "LEVES | MOTOS | PESADOS, obrigatorio",
  "fipe_valor":           "number > 0, obrigatorio",
  "cobertura_terceiros":  "nenhuma | 50k | 100k, obrigatorio"
}
```

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Criado. Body: `{ id, associado_id, placa, segmento, fipe_valor, cobertura_terceiros, cota, status, criado_em }` |
| 401  | Nao autenticado. |
| 404  | `associado_id` nao encontrado na associacao do operador. |
| 409  | Placa ja cadastrada na associacao. |
| 422  | Placa invalida, segmento invalido, FIPE <= 0, cobertura invalida, ou `associado_id` ausente. |
| 500  | Nenhuma faixa de cota vigente configurada para a associacao. |

Nota sobre o HTTP 500: a ausencia de faixas e um erro de configuracao, nao
de entrada. O response body deve conter uma mensagem clara orientando o
operador a configurar a tabela de faixas antes de cadastrar veiculos.

### 5.2 GET /api/veiculos

Lista os veiculos da associacao do operador logado.

Query params opcionais:

| Param          | Tipo   | Descricao |
|----------------|--------|-----------|
| `associado_id` | uuid   | Filtra por associado. |
| `segmento`     | string | Filtra por LEVES, MOTOS ou PESADOS. |
| `status`       | string | Filtra por status. Padrao: todos. |
| `q`            | string | Busca parcial por placa (case-insensitive). |
| `page`         | int    | Pagina (base 1). Padrao: 1. |
| `per_page`     | int    | Registros por pagina. Padrao: 50. Maximo: 200. |

Response 200:

```json
{
  "data": [
    {
      "id", "associado_id", "placa", "segmento",
      "fipe_valor", "cobertura_terceiros", "cota", "status", "criado_em"
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 50
}
```

### 5.3 GET /api/veiculos/:id

Retorna os dados de um veiculo pelo id.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Dados do veiculo. Mesmo shape do item em GET /api/veiculos. |
| 401  | Nao autenticado. |
| 404  | Veiculo nao encontrado na associacao do operador. |

A RLS garante que um id pertencente a outra associacao retorna 404, sem
vazar a existencia do registro.

### 5.4 PATCH /api/veiculos/:id

Atualiza campos editaveis do veiculo. A placa nao e editavel apos o cadastro.
Se `fipe_valor` for alterado, a cota e recalculada pela tabela de faixas
vigente no momento da edicao.

Campos editaveis: `segmento`, `fipe_valor`, `cobertura_terceiros`, `status`.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Atualizado. Body: dados atualizados no mesmo shape. |
| 401  | Nao autenticado. |
| 404  | Nao encontrado na associacao. |
| 422  | Segmento invalido, FIPE <= 0, cobertura invalida, ou status invalido. |

Nota: a alteracao de segmento ou FIPE de um veiculo ja ativo afeta o
denominador da BASE em competencias futuras. A auditoria registra o estado
anterior e o novo estado com o timestamp da operacao.

### 5.5 GET /api/veiculos/simular-cota

Calcula e retorna a cota para um valor FIPE informado, sem gravar nenhum
registro. Util para o frontend exibir a cota prevista antes do submit.

Query params:

| Param       | Tipo   | Descricao |
|-------------|--------|-----------|
| `fipe_valor`| number | Valor FIPE positivo. Obrigatorio. |

Response 200:

```json
{
  "fipe_valor": 85000.00,
  "cota": 320.00,
  "faixa_aplicada": "80000-90000"
}
```

Response 422: FIPE <= 0 ou ausente.
Response 500: nenhuma faixa configurada para a associacao.

### 5.6 Logica de calculo da cota (servico)

O calculo ocorre exclusivamente no backend. O frontend pode chamar
`/api/veiculos/simular-cota` para feedback imediato, mas o valor autoritativo
e o calculado no momento do POST ou do PATCH.

Algoritmo:

1. Buscar na tabela `faixas_cota` as faixas da associacao com
   `vigente_desde <= data_atual`, ordenadas por `fipe_ate` ascendente (linhas
   com `fipe_ate` nulo ficam ao final).
2. Percorrer as faixas em ordem. Selecionar a primeira cuja `fipe_ate` e maior
   ou igual ao `fipe_valor` do veiculo.
3. Se nenhuma faixa com `fipe_ate` finito cobrir o valor, usar a faixa com
   `fipe_ate` nulo (cota especial).
4. Se nenhuma faixa existir, sinalizar erro de configuracao (HTTP 500).
5. O valor de `cota_valor` da faixa selecionada e a cota do veiculo.

Esse algoritmo espelha a progressao por faixas do motor aprovado (`rules.py`,
`cotas_por_fipe`): faixas de 10 mil reais, cota base 1,0, acrescimo de 0,5
por faixa, cota especial 20,0 para FIPE acima de 450.000. Os valores
concretos de cada faixa sao parametros da associacao, nao constantes do
codigo, mas o seed inicial deve reproduzir os valores do motor (ADR-002 C5).

### 5.7 Validacao de placa (logica de servico)

A validacao ocorre no backend. O frontend pode replicar para feedback
imediato.

Normalizacao:
1. Remover espacos e hifens.
2. Converter para maiusculas.
3. Aplicar os testes de formato abaixo sobre a string normalizada.

Formatos aceitos:

- Padrao antigo: exatamente tres letras seguidas de quatro digitos
  (expressao regular: `^[A-Z]{3}[0-9]{4}$`).
- Padrao Mercosul: exatamente tres letras, um digito, uma letra e dois
  digitos (expressao regular: `^[A-Z]{3}[0-9][A-Z][0-9]{2}$`).

Qualquer string que nao se enquadre em nenhum dos dois padroes apos a
normalizacao e rejeitada.

---

## 6. UI

### 6.1 Tela: lista de veiculos

Rota sugerida: `/veiculos`

Elementos:
- Tabela paginada com colunas: Placa, Segmento, FIPE, Cota, Cobertura,
  Status.
- Campo de busca por placa.
- Filtros de segmento e status.
- Botao "Novo veiculo" que abre o formulario de cadastro.
- Linha clicavel que navega para o detalhe do veiculo.

### 6.2 Tela: formulario de cadastro

Rota sugerida: `/veiculos/novo`

Campos:
- Associado (seletor com busca por nome ou CPF mascarado; obrigatorio).
- Placa (obrigatorio): mascara aplicada no campo; validacao de formato inline
  sem disparar request ao servidor ate o submit.
- Segmento (seletor: LEVES, MOTOS, PESADOS; obrigatorio).
- Valor FIPE (numerico positivo; obrigatorio): ao sair do campo, o frontend
  chama GET /api/veiculos/simular-cota e exibe a cota prevista ao lado do
  campo, sem bloquear o submit.
- Cobertura de terceiros (seletor: nenhuma, 50k, 100k; obrigatorio).

Comportamento:
- Submit dispara POST /api/veiculos.
- Em caso de 409, exibe mensagem: "Placa ja cadastrada nesta associacao."
- Em caso de 422, exibe a mensagem do campo correspondente abaixo do input.
- Em caso de 500 (faixas nao configuradas), exibe aviso destacado orientando
  o administrador.
- Em caso de sucesso, redireciona para o detalhe do veiculo criado ou para a
  lista, conforme decisao de UX.
- A cota exibida no formulario e apenas uma previa; o valor definitivo vem no
  response do POST e deve ser exibido na tela de detalhe.

### 6.3 Tela: detalhe e edicao do veiculo

Rota sugerida: `/veiculos/:id`

Exibe os dados do veiculo. A placa e exibida e nao e editavel. Os campos
segmento, FIPE, cobertura de terceiros e status podem ser editados. Ao editar
o FIPE, a cota e recalculada e atualizada automaticamente no backend via PATCH.

Exibe tambem:
- O nome do associado vinculado (com link para o detalhe do associado,
  SPEC-002).
- O status da vistoria do veiculo (leitura, gerenciado pela SPEC-004).
- O historico de situacoes de boleto por competencia (leitura, gerenciado
  pela SPEC-005).

---

## 7. Observabilidade

- Logar no nivel INFO cada criacao e edicao de veiculo, com `veiculo_id`,
  `associacao_id`, `segmento` e a faixa de cota aplicada. Nao incluir
  `fipe_valor` em claro no log se a politica de privacidade da associacao
  considerar esse dado sensivel.
- Logar no nivel WARN cada tentativa rejeitada por placa duplicada (409),
  placa invalida ou FIPE invalido (422), com `associacao_id` e o tipo de
  rejeicao.
- Logar no nivel ERROR quando nenhuma faixa de cota estiver configurada
  (condicao que impede o cadastro).
- A tabela `veiculos_audit` e a trilha persistente; os logs de aplicacao sao
  complementares.
- Metrica recomendada: distribuicao de veiculos por segmento e por status,
  por associacao, para acompanhar o crescimento da base.

---

## 8. Seguranca e LGPD

- A placa e um dado do veiculo, nao diretamente pessoal, mas pode identificar
  o titular; deve ser tratada com o mesmo cuidado de dados de identificacao.
  Nao incluir placas em claro em logs de nivel INFO ou superior.
- O valor FIPE e considerado dado patrimonial do associado; nao expor em logs.
- O isolamento por RLS garante que dados de uma associacao nao vazam para
  operadores de outra (RNF-01).
- A trilha de auditoria e imutavel: sem endpoint de DELETE ou UPDATE em
  `veiculos_audit`; a policy RLS bloqueia insercao direta pelo app (RNF-02).
- A comunicacao e exclusivamente por HTTPS (RNF-04).
- A placa aparece no arquivo RATEIO exportado (SPEC-000, secao 3). O uso da
  placa na exportacao deve ser documentado como finalidade legitima no
  mapeamento de dados da LGPD do produto.
- A tabela `faixas_cota` contem apenas parametros operacionais (valores de
  cota por faixa), sem dados pessoais. O acesso e restrito por RLS ao tenant.

---

## 9. Testes

### 9.1 Testes unitarios (validacao de placa e calculo de cota)

Validacao de placa:
- Placa antiga valida: ao menos tres exemplos (ex.: ABC1234, ZZZ9999, XYZ0000).
- Placa Mercosul valida: ao menos tres exemplos (ex.: ABC1D23, XYZ2E34).
- Placa com hifen (ex.: ABC-1234): deve ser normalizada e aceita como antigo.
- Placa com letras minusculas (ex.: abc1234): deve ser normalizada e aceita.
- Placa antiga com cinco digitos: deve ser rejeitada.
- Placa Mercosul com dois digitos no lugar da letra central: deve ser rejeitada.
- String vazia: deve ser rejeitada.
- Placa com caracteres especiais: deve ser rejeitada.

Calculo de cota:
- FIPE no inicio de uma faixa intermediaria: retorna a cota da faixa correta.
- FIPE no limite exato de uma faixa (igual ao `fipe_ate`): retorna a cota
  daquela faixa, nao da proxima.
- FIPE acima do ultimo limite finito: retorna a cota especial (faixa com
  `fipe_ate` nulo).
- Nenhuma faixa configurada: sinaliza erro de configuracao.
- Tabela com uma unica faixa (fipe_ate nulo): todos os FIPE retornam aquela
  cota.
- FIPE zero ou negativo: rejeitado antes de consultar a tabela.

### 9.2 Testes de integracao (API)

- POST com dados validos retorna 201 e payload com cota calculada.
- POST com placa duplicada na mesma associacao retorna 409.
- POST com placa duplicada em associacao diferente retorna 201 (isolamento
  de tenant).
- POST com placa invalida retorna 422.
- POST com segmento invalido retorna 422.
- POST com FIPE <= 0 retorna 422.
- POST com cobertura invalida retorna 422.
- POST com `associado_id` de outra associacao retorna 404.
- GET /api/veiculos retorna somente veiculos da associacao do operador.
- GET /api/veiculos/:id de outra associacao retorna 404.
- PATCH com novo `fipe_valor` recalcula a cota e persiste o novo valor.
- PATCH com `placa` no payload nao altera a placa persistida.
- GET /api/veiculos/simular-cota retorna a cota prevista sem gravar registro.

### 9.3 Ligacao com o oraculo do motor aprovado

O calculo de cota desta spec alimenta diretamente o denominador da BASE:
cada cota de veiculo com status `ativo` e boleto baixado na competencia
compoe a coluna BAIXADO do segmento correspondente (ver SPEC-000, secao 4).

Teste de ponta a ponta (harness de reconciliacao, SPEC-000, secao 6):

1. Configurar faixas de cota com valores conhecidos na associacao de teste.
2. Cadastrar N veiculos com placas, segmentos e FIPE definidos; verificar
   que as cotas calculadas correspondem aos valores esperados pela tabela
   de faixas.
3. Concluir vistoria de cada veiculo (SPEC-004) e registrar boleto baixado
   na competencia (SPEC-005).
4. Exportar a BASE (SPEC-000) e verificar que:
   a. `detectar_tipo` reconhece o arquivo como BASE.
   b. A soma de cotas na coluna BAIXADO de cada segmento confere com a soma
      das cotas dos veiculos ativos com boleto baixado naquele segmento.
5. Rodar o motor aprovado sobre BASE e RATEIO e confirmar invariante de
   fechamento igual a zero.

A regra de calculo de cota implementada no app DEVE produzir os mesmos
valores que o motor aprovado utilizaria para a mesma tabela de faixas.
Qualquer divergencia entre a cota gravada no app e a cota que o motor
esperaria invalida o aceite.

---

## 10. Rollout

1. Aplicar as migrations de banco (`veiculos`, `faixas_cota`,
   `veiculos_audit`, constraints, indices, RLS, trigger de auditoria) em
   ambiente de desenvolvimento. A migration de `veiculos` depende da migration
   de `associados` (SPEC-002) estar aplicada.
2. Inserir a tabela de faixas de cota do ambiente de teste via script de seed,
   com valores espelhando a regra do motor aprovado.
3. Rodar os testes unitarios de placa e cota.
4. Rodar os testes de integracao da API.
5. Revisar a policy RLS com um segundo operador de tenant diferente (teste
   manual de isolamento).
6. Aprovar a spec com o Tech Lead e o Spec Lead antes de prosseguir para
   implementacao do frontend.
7. Apos o frontend concluir as telas de cadastro e detalhe, realizar o aceite
   funcional manual com base nos criterios da secao 3.
8. A SPEC-004 (vistoria) pode ser iniciada em paralelo apos a aprovacao desta
   spec; ela depende da tabela `veiculos` estar migrada, nao do frontend
   concluido.

---

## 11. Questoes em aberto

- Granularidade das faixas de cota: o MVP assume faixas de 10 mil reais
  espelhando o motor aprovado. Se a associacao operar com granularidade
  diferente, a tabela `faixas_cota` suporta qualquer intervalo, mas o seed
  inicial precisa ser confirmado com o responsavel pela configuracao.
- Alteracao de segmento de veiculo ativo: se o segmento for alterado apos o
  veiculo estar ativo, as competencias futuras refletem o novo segmento, mas
  as competencias passadas ja exportadas nao sao retroativamente corrigidas.
  Definir se a alteracao de segmento de veiculo ativo deve ser bloqueada ou
  apenas alertada.
- Placa duplicada entre associacoes distintas: atualmente permitida (isolamento
  por tenant). Confirmar se ha algum requisito de negocio que exija unicidade
  global de placa entre associacoes.
- Cota em competencias com tabela de faixas alterada: o campo `cota` e gravado
  no cadastro e recalculado apenas em PATCH explicito. Se a tabela de faixas
  for alterada, os veiculos existentes mantem a cota antiga ate edicao manual.
  Definir se deve haver um processo de recalculo em lote ao alterar as faixas
  ou se o comportamento atual e aceitavel para o MVP.
- Interface de administracao das faixas de cota: no MVP, as faixas sao
  inseridas por migration ou script de seed. Avaliar se uma tela simples de
  administracao (listar, inserir, desativar faixas) e necessaria antes do
  primeiro uso em producao.
