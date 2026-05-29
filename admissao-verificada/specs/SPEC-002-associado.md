# SPEC-002 — Cadastro de Associado

Status: rascunho. Data: 2026-05-29.
Responsavel: Engenheiro Backend.

---

## 1. Contexto

O cadastro de associado e a primeira entidade da cadeia de admissao verificada.
Um associado representa a pessoa fisica que solicita a entrada na associacao.
Antes de ter veiculos, vistoria e situacao de boleto, o associado precisa existir
no sistema com dados minimos de identificacao e contato.

Esta spec define apenas o cadastro do associado (identidade e contato). O
vinculo com veiculos e tratado na SPEC-003. A vistoria e tratada na SPEC-004.
O associado cadastrado aqui ainda nao e considerado "admitido"; a admissao
verificada so se conclui apos a vistoria do veiculo (SPEC-004).

O isolamento por associacao (tenant) e herdado da decisao de arquitetura
(ADR-001, item 2): toda tabela tem RLS vinculada ao tenant do operador logado.

---

## 2. Requisitos

Esta spec cobre os seguintes requisitos do MVP-SCOPE:

- RF-ASSOC-01: O sistema DEVE cadastrar associado com nome e CPF.
- RF-ASSOC-02: O sistema DEVE validar o CPF pelo algoritmo oficial (dois
  digitos verificadores, rejeitar sequencias uniformes como 000.000.000-00).
- RF-ASSOC-03: O sistema DEVE impedir CPF duplicado na mesma associacao.

Requisitos nao funcionais aplicaveis:

- RNF-01: Isolamento por associacao (RLS).
- RNF-02: Trilha de auditoria imutavel nas operacoes de admissao.
- RNF-04: Comunicacao por HTTPS; dados pessoais tratados conforme a LGPD.

---

## 3. Criterios de Aceite

### AC-001 — Cadastro com dados validos

Given um operador autenticado na associacao A,
When envia nome nao vazio e CPF valido (formato e algoritmo) para o endpoint
de criacao,
Then o sistema persiste o associado com status `ativo`, retorna HTTP 201 e o
corpo contem o `id` gerado, o nome e o CPF (mascarado no response).

### AC-002 — CPF com formato invalido

Given um operador autenticado,
When envia um CPF com menos ou mais de 11 digitos numericos, ou com letras,
Then o sistema rejeita com HTTP 422 e mensagem indicando formato invalido, sem
gravar registro.

### AC-003 — CPF que falha no algoritmo de verificacao

Given um operador autenticado,
When envia um CPF com 11 digitos numericos porem com digitos verificadores
incorretos, ou uma sequencia uniforme (ex.: 111.111.111-11),
Then o sistema rejeita com HTTP 422 e mensagem indicando CPF invalido pelo
algoritmo, sem gravar registro.

### AC-004 — CPF duplicado na mesma associacao

Given a associacao A ja possui o associado com CPF 123.456.789-09,
When um operador da associacao A tenta cadastrar outro associado com o mesmo
CPF,
Then o sistema rejeita com HTTP 409 e mensagem indicando duplicidade de CPF
na associacao.

### AC-005 — CPF repetido em associacao diferente e permitido

Given a associacao A possui associado com CPF 123.456.789-09,
When um operador da associacao B cadastra associado com o mesmo CPF,
Then o sistema aceita e persiste normalmente (o isolamento e por tenant).

### AC-006 — Listagem filtrada por associacao

Given a associacao A possui tres associados e a associacao B possui dois,
When um operador da associacao A lista os associados,
Then recebe exatamente os tres da associacao A, sem nenhum dado da
associacao B.

### AC-007 — Edicao de dados de contato

Given um associado cadastrado com e-mail e telefone,
When o operador edita o e-mail,
Then o sistema atualiza o campo, registra o evento de auditoria com timestamp
e id do operador, e retorna HTTP 200.

### AC-008 — CPF nao pode ser alterado apos o cadastro

Given um associado ja cadastrado,
When o operador tenta alterar o CPF via endpoint de edicao,
Then o sistema ignora o campo CPF no payload (ou rejeita com HTTP 422 caso a
spec de implementacao opte por rejeitar), mantendo o CPF original inalterado.

---

## 4. Modelo de Dados

### 4.1 Tabela `associados`

```sql
create table associados (
  id            uuid primary key default gen_random_uuid(),
  associacao_id uuid not null references associacoes(id) on delete restrict,
  nome          text not null check (char_length(trim(nome)) > 0),
  cpf           char(11) not null,           -- apenas digitos, sem mascara
  email         text,
  telefone      text,
  status        text not null default 'ativo'
                  check (status in ('ativo', 'inativo')),
  criado_em     timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
```

Restricoes adicionais:

```sql
-- unicidade de CPF dentro da associacao
alter table associados
  add constraint associados_cpf_associacao_unique
  unique (associacao_id, cpf);

-- indice para buscas por CPF dentro de uma associacao
create index associados_associacao_cpf_idx
  on associados (associacao_id, cpf);
```

Notas:
- O CPF e armazenado somente com os 11 digitos numericos, sem pontos ou traco.
  A formatacao e responsabilidade da camada de apresentacao.
- O campo `status` e reservado para desativacao futura; no MVP todos os
  associados criados nascem como `ativo`.
- `email` e `telefone` sao opcionais no MVP (dados de contato desejados mas
  nao obrigatorios para o fluxo de admissao e rateio).

### 4.2 Tabela `associados_audit`

Registro imutavel de cada operacao sobre `associados`, conforme RNF-02.

```sql
create table associados_audit (
  id              bigint generated always as identity primary key,
  associado_id    uuid not null,
  associacao_id   uuid not null,
  operador_id     uuid not null,   -- auth.uid() no momento da operacao
  operacao        text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes   jsonb,           -- null em INSERT
  payload_depois  jsonb,           -- null em DELETE
  ocorrido_em     timestamptz not null default now()
);
```

A trilha e preenchida por trigger na tabela `associados`. Nao ha endpoint de
escrita direta nessa tabela; ela e somente leitura para o app.

### 4.3 Politica RLS

O claim `associacao_id` deve estar presente no JWT do operador autenticado
(provisionado no momento do login, conforme ADR-002 C2). As policies leem
esse claim diretamente; subquery em `operadores` e proibida para evitar N+1.

```sql
-- habilitar RLS
alter table associados enable row level security;
alter table associados_audit enable row level security;

-- operadores so enxergam registros da propria associacao
create policy associados_isolamento on associados
  using (associacao_id::text = auth.jwt() ->> 'associacao_id');

-- auditoria: leitura restrita a operadores da mesma associacao
create policy associados_audit_leitura on associados_audit
  for select
  using (associacao_id::text = auth.jwt() ->> 'associacao_id');

-- auditoria: sem escrita direta pelo app (apenas via trigger)
create policy associados_audit_sem_insert on associados_audit
  for insert
  with check (false);
```

---

## 5. API

Base de URL: `/api/associados`

Todas as rotas exigem sessao ativa (cookie de sessao Supabase ou Bearer token).
O `associacao_id` e inferido do operador logado; nao e um parametro de URL.

### 5.1 POST /api/associados

Cria um novo associado.

Request body:

```json
{
  "nome": "string, obrigatorio, nao vazio",
  "cpf": "string, obrigatorio, 11 digitos numericos",
  "email": "string, opcional, formato e-mail",
  "telefone": "string, opcional"
}
```

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Criado com sucesso. Body: `{ id, nome, cpf_mascarado, email, telefone, status, criado_em }` |
| 401  | Nao autenticado. |
| 409  | CPF ja cadastrado na associacao. |
| 422  | CPF com formato invalido, CPF que falha no algoritmo, ou nome vazio. |

O campo `cpf_mascarado` expoe apenas os tres primeiros e dois ultimos digitos
(ex.: `123.***.***-09`) para reduzir exposicao de dado pessoal sensivel no
response de listagem e criacao.

### 5.2 GET /api/associados

Lista os associados da associacao do operador logado.

Query params opcionais:

| Param    | Tipo   | Descricao |
|----------|--------|-----------|
| `q`      | string | Busca parcial por nome (case-insensitive). |
| `status` | string | Filtra por `ativo` ou `inativo`. Padrao: `ativo`. |
| `page`   | int    | Pagina (base 1). Padrao: 1. |
| `per_page` | int  | Registros por pagina. Padrao: 50. Maximo: 200. |

Response 200:

```json
{
  "data": [
    { "id", "nome", "cpf_mascarado", "email", "telefone", "status", "criado_em" }
  ],
  "total": 42,
  "page": 1,
  "per_page": 50
}
```

### 5.3 GET /api/associados/:id

Retorna os dados de um associado pelo id.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Dados do associado. Mesmo shape do item em GET /api/associados. |
| 401  | Nao autenticado. |
| 404  | Associado nao encontrado na associacao do operador. |

Nota: a RLS garante que um id pertencente a outra associacao retorna 404, nao
403, para nao vazar a existencia do registro.

### 5.4 PATCH /api/associados/:id

Atualiza campos editaveis do associado. O CPF nao e editavel apos o cadastro
e e ignorado no payload (ver AC-008).

Campos editaveis: `nome`, `email`, `telefone`, `status`.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Atualizado. Body: dados atualizados no mesmo shape. |
| 401  | Nao autenticado. |
| 404  | Nao encontrado na associacao. |
| 422  | Nome vazio ou status invalido. |

### 5.5 Validacao de CPF (logica de servico)

A validacao ocorre no backend, antes de qualquer operacao de banco. O frontend
pode replicar a logica para feedback imediato, mas a verificacao autoritativa e
do servidor.

Algoritmo (padrao Receita Federal):

1. Rejeitar sequencias uniformes: `000...000`, `111...111`, ..., `999...999`.
2. Calcular o primeiro digito verificador: soma ponderada dos 9 primeiros
   digitos, multiplicados por 10, 9, 8, ..., 2. Resto da divisao por 11: se
   menor que 2, digito = 0; caso contrario, digito = 11 menos o resto.
3. Calcular o segundo digito verificador: soma ponderada dos 10 primeiros
   digitos, multiplicados por 11, 10, 9, ..., 2. Mesma regra de resto.
4. Comparar os digitos calculados com os dois ultimos do CPF informado.

A validacao recebe a string com ou sem mascara (pontos e traco sao removidos
antes do calculo).

---

## 6. UI

### 6.1 Tela: lista de associados

Rota sugerida: `/associados`

Elementos:
- Tabela paginada com colunas: Nome, CPF (mascarado), E-mail, Status.
- Campo de busca por nome.
- Filtro de status (ativo / inativo / todos).
- Botao "Novo associado" que abre o formulario de cadastro.
- Linha clicavel que navega para o detalhe do associado.

### 6.2 Tela: formulario de cadastro

Rota sugerida: `/associados/novo`

Campos:
- Nome completo (obrigatorio).
- CPF (obrigatorio): mascara `000.000.000-00` aplicada no campo; validacao do
  algoritmo inline (sem disparar request ao servidor ate o submit).
- E-mail (opcional).
- Telefone (opcional).

Comportamento:
- Submit dispara POST /api/associados.
- Em caso de 409, exibe mensagem: "CPF ja cadastrado nesta associacao."
- Em caso de 422, exibe a mensagem do campo correspondente abaixo do input.
- Em caso de sucesso, redireciona para a tela de detalhe do associado criado
  ou para a lista, conforme decisao de UX.

### 6.3 Tela: detalhe e edicao do associado

Rota sugerida: `/associados/:id`

Exibe os dados do associado. O CPF e exibido mascarado e o campo nao e
editavel. Os demais campos (nome, email, telefone, status) podem ser editados
in-place ou por formulario lateral.

Exibe tambem a lista de veiculos vinculados ao associado (leitura apenas nesta
tela; edicao de veiculo e responsabilidade da SPEC-003).

---

## 7. Observabilidade

- Logar no nivel INFO cada criacao e edicao de associado, com o `associado_id`
  e o `associacao_id`, sem incluir o CPF em claro no log.
- Logar no nivel WARN cada tentativa rejeitada por CPF duplicado (409) ou CPF
  invalido (422), com o `associacao_id` e o tipo de rejeicao, sem CPF em claro.
- A tabela `associados_audit` e a trilha persistente; os logs de aplicacao sao
  complementares e podem ser expurgados conforme politica de retencao.
- Metrica recomendada: contador de cadastros bem-sucedidos por associacao e
  por dia, para acompanhamento do volume de onboarding.

---

## 8. Seguranca e LGPD

- O CPF e dado pessoal sensivel. Ele nao aparece em claro em logs, responses
  de listagem nem em mensagens de erro.
- Nos responses da API, o CPF e sempre retornado mascarado (`cpf_mascarado`).
  O CPF completo so e acessivel internamente na camada de servico, quando
  necessario para validacao ou exportacao.
- A comunicacao e exclusivamente por HTTPS (RNF-04).
- O isolamento por RLS garante que dados de uma associacao nao vazam para
  operadores de outra (RNF-01).
- A trilha de auditoria e imutavel: sem endpoint de DELETE ou UPDATE em
  `associados_audit`; a policy RLS bloqueia insercao direta pelo app (RNF-02).
- O acesso ao CPF completo (sem mascara) para fins de exportacao do arquivo
  BASE deve ser documentado como finalidade legitima no mapeamento de dados
  da LGPD do produto.
- Futuramente, implementar anonimizacao do CPF em registros de associados
  inativos apos prazo legal; fora do escopo do MVP.

---

## 9. Testes

### 9.1 Testes unitarios (validacao de CPF)

- CPF valido: ao menos cinco exemplos com digitos verificadores corretos.
- CPF invalido por sequencia uniforme: todos os onze padroes (000 a 999).
- CPF invalido por primeiro digito errado.
- CPF invalido por segundo digito errado.
- CPF com mascara (pontos e traco): deve ser normalizado e aceito se valido.
- CPF com comprimento diferente de 11 digitos apos normalizacao: rejeitar.

### 9.2 Testes de integracao (API)

- POST com dados validos retorna 201 e payload esperado.
- POST com CPF duplicado na mesma associacao retorna 409.
- POST com CPF duplicado em associacao diferente retorna 201 (isolamento
  de tenant).
- POST com CPF invalido (formato) retorna 422.
- POST com CPF invalido (algoritmo) retorna 422.
- POST com nome vazio retorna 422.
- GET /api/associados retorna somente registros da associacao do operador.
- GET /api/associados/:id de outra associacao retorna 404.
- PATCH com CPF no payload nao altera o CPF persistido.
- PATCH com nome vazio retorna 422.

### 9.3 Ligacao com o oraculo do motor aprovado

O cadastro de associado por si so nao envolve o motor de rateio. A ligacao
ocorre na cadeia completa: associado -> veiculo (SPEC-003) -> vistoria
(SPEC-004) -> situacao de boleto (SPEC-005) -> exportacao BASE (SPEC-000).

O associado cadastrado aqui e prerequisito para que o veiculo apareca no
denominador da BASE. O teste fim a fim (harness de reconciliacao, SPEC-000
secao 6) valida que, dado um associado com veiculo admitido e boleto baixado
na competencia, o arquivo BASE exportado tem `detectar_tipo` correto e a cota
aparece na coluna BAIXADO do segmento correspondente, com invariante de
fechamento igual a zero.

---

## 10. Rollout

1. Aplicar a migration de banco (`associados` + `associados_audit` + constraints
   + RLS + trigger de auditoria) em ambiente de desenvolvimento.
2. Rodar os testes unitarios de CPF e os testes de integracao da API.
3. Revisar a policy RLS com um segundo operador de tenant diferente (teste
   manual de isolamento).
4. Aprovar a spec com o Tech Lead e o Spec Lead antes de prosseguir para
   implementacao do frontend.
5. Apos o frontend concluir a tela de cadastro, realizar o aceite funcional
   manual com base nos criterios da secao 3.
6. A spec de veiculo (SPEC-003) pode ser iniciada em paralelo apos a aprovacao
   desta; ela depende da tabela `associados` estar migrada, nao do frontend
   concluido.

---

## 11. Questoes em aberto

- Dado minimo de contato: e-mail e telefone sao opcionais no MVP, mas ha
  discussao se ao menos um deles deveria ser obrigatorio para fins de
  notificacao do associado. Decisao pendente com o Spec Lead.
- Mascaramento do CPF no detalhe: a tela de detalhe do associado deve exibir
  o CPF completo para o operador (para conferencia) ou sempre mascarado?
  Opcao A (sempre mascarado) reduz exposicao; opcao B (completo para
  operador) facilita conferencia manual. Decidir antes da implementacao do
  frontend.
- Inativacao vs. exclusao: o campo `status` permite inativar um associado,
  mas nao ha endpoint de DELETE no MVP. Confirmar se inativacao e suficiente
  ou se precisara de soft-delete com flag de exclusao e prazo de retencao LGPD.
- Busca por CPF: o endpoint de listagem aceita busca por nome. Falta definir
  se o operador pode buscar pelo CPF completo ou pelo numero parcial; se sim,
  o campo `q` precisara cobrir CPF alem de nome.
