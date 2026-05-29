# SPEC-001 -- Autenticacao e Contexto da Associacao

Status: rascunho. Data: 2026-05-29.
Autores: Engenheiro Frontend / Tech Lead.
Requisitos cobertos: RF-AUTH-01, RF-AUTH-02, RNF-01.

---

## 1. Contexto

O MVP de Admissao Verificada opera com operadores humanos que acessam a
plataforma via navegador. Cada operador pertence a exatamente uma associacao
(tenant). Todo registro de dado da aplicacao -- associado, veiculo, vistoria,
boleto, evento -- precisa estar vinculado a essa associacao para que o
isolamento funcione e para que a exportacao de BASE e RATEIO reflita apenas
os dados da associacao correta.

A fundacao tecnica escolhida e Next.js 15 mais Supabase, conforme ADR-001. O
Supabase Auth gerencia sessao e tokens JWT. O isolamento multi-tenant e
implementado por Row Level Security (RLS) no Postgres do Supabase, usando o
identificador da associacao propagado via claims do JWT.

O MVP opera com uma unica associacao cadastrada. O schema, porem, e projetado
desde o inicio para suportar multiplas associacoes sem refatoracao de
isolamento, conforme a decisao 2 do ADR-001: "barato agora, evita retrabalho
de isolamento depois".

Fluxos fora do escopo desta spec: convite e cadastro autonomo de operadores,
recuperacao de senha com fluxo customizado, permissoes granulares por papel,
autenticacao por provedor externo (SSO, OAuth). Esses fluxos entram em fase
posterior.

---

## 2. Requisitos

Esta spec cobre os seguintes requisitos do MVP-SCOPE:

- RF-AUTH-01: O sistema DEVE permitir login por e-mail e senha para operadores.
- RF-AUTH-02: O sistema DEVE vincular todo registro a uma associacao (tenant).
- RNF-01: Toda tabela DEVE ter isolamento por associacao (RLS).

O que esta spec nao cobre: cadastro de novos operadores em producao (sera
feito via Supabase Dashboard no MVP), recuperacao de senha (delegada ao fluxo
padrao do Supabase Auth), permissoes por papel dentro da associacao.

---

## 3. Criterios de Aceite

### CA-001-1: Login valido

```
Given um operador cadastrado com e-mail e senha validos,
When ele submete o formulario de login com as credenciais corretas,
Then a sessao e criada, o JWT contem o claim associacao_id correto
e o operador e redirecionado ao painel da associacao.
```

### CA-001-2: Credenciais incorretas

```
Given um operador existente,
When ele submete senha errada ou e-mail inexistente,
Then a aplicacao exibe mensagem de erro generica (sem distinguir e-mail de
senha) e nenhuma sessao e criada.
```

### CA-001-3: Acesso sem sessao

```
Given um navegador sem sessao ativa,
When qualquer rota protegida e acessada diretamente,
Then o usuario e redirecionado para a tela de login sem expor dados.
```

### CA-001-4: Sessao expirada

```
Given um operador com sessao ativa que expirou,
When ele tenta acessar qualquer rota protegida,
Then o Supabase Auth renova o token via refresh token (silencioso) ou,
se o refresh tambem expirou, redireciona para login.
```

### CA-001-5: Isolamento por RLS -- leitura

```
Given duas associacoes A e B com registros proprios na base,
When um operador da associacao A executa qualquer consulta em tabela com RLS,
Then ele visualiza apenas registros onde associacao_id = A.
```

### CA-001-6: Isolamento por RLS -- escrita

```
Given um operador autenticado da associacao A,
When ele tenta inserir ou atualizar um registro com associacao_id diferente
de A (inclusive via API direta ao Supabase),
Then a operacao e rejeitada pelo RLS com erro de permissao.
```

### CA-001-7: Logout

```
Given um operador com sessao ativa,
When ele aciona o logout,
Then a sessao e invalidada no Supabase Auth, os tokens sao removidos do
cliente e qualquer rota protegida volta a redirecionar para login.
```

---

## 4. Modelo de Dados

### 4.1. Tabela: associacoes

Armazena cada tenant. No MVP ha exatamente um registro; o schema comporta N.

| Coluna        | Tipo                     | Restricoes                        |
|---------------|--------------------------|-----------------------------------|
| id            | uuid                     | PK, default gen_random_uuid()     |
| nome          | text                     | NOT NULL                          |
| slug          | text                     | NOT NULL, UNIQUE                  |
| criado_em     | timestamptz              | NOT NULL, default now()           |

Observacoes:
- `slug` e um identificador legivel por humanos (ex.: "assoc-norte"), util para
  URLs amigaveis em fases futuras; obrigatorio mesmo no MVP para manter o
  schema extensivel.
- Nao ha RLS nesta tabela no MVP (a tabela e pequena e so operadores
  autenticados a leem). Caso o produto cresça, RLS pode ser adicionado sem
  breaking change.

### 4.2. Tabela: operadores

Complemento ao usuario do Supabase Auth. Vincula o auth.users.id a uma
associacao.

| Coluna           | Tipo        | Restricoes                                  |
|------------------|-------------|---------------------------------------------|
| id               | uuid        | PK, references auth.users(id) ON DELETE CASCADE |
| associacao_id    | uuid        | NOT NULL, references associacoes(id)        |
| nome_exibicao    | text        | NOT NULL                                    |
| ativo            | boolean     | NOT NULL, default true                      |
| criado_em        | timestamptz | NOT NULL, default now()                     |
| atualizado_em    | timestamptz | NOT NULL, default now()                     |

RLS -- politica SELECT:
```sql
CREATE POLICY operadores_select ON operadores
  FOR SELECT
  USING (
    associacao_id = (
      SELECT associacao_id FROM operadores
      WHERE id = auth.uid()
    )
  );
```

RLS -- politica INSERT/UPDATE:
No MVP, insercao e atualizada diretamente pelo administrador via Supabase
Dashboard ou via funcao de servico com service_role key. Operadores comuns nao
tem permissao de INSERT nem UPDATE nesta tabela.

### 4.3. Claim personalizado no JWT: associacao_id

Para que o RLS das demais tabelas nao precise fazer join com `operadores` a
cada linha avaliada, o `associacao_id` e propagado como claim personalizado no
JWT do Supabase Auth via database webhook ou via funcao `auth.hook`.

Mecanismo (Supabase):

```sql
-- Funcao chamada pelo hook de custom_access_token
CREATE OR REPLACE FUNCTION public.custom_jwt_claims(event jsonb)
RETURNS jsonb
LANGUAGE plpgsql STABLE
AS $$
DECLARE
  _assoc_id uuid;
BEGIN
  SELECT associacao_id INTO _assoc_id
    FROM public.operadores
   WHERE id = (event->>'user_id')::uuid;

  RETURN jsonb_build_object(
    'associacao_id', _assoc_id
  );
END;
$$;
```

Referencia ao claim nas policies RLS das demais tabelas:

```sql
(auth.jwt() ->> 'associacao_id')::uuid
```

Essa abordagem e a recomendada pelo Supabase para multi-tenant por RLS, evita
N+1 no lado do banco e mantém a politica legivel.

### 4.4. Padrao RLS para todas as demais tabelas do MVP

Toda tabela que contiver dados de negocio (associados, veiculos, vistorias,
boletos, eventos) DEVE ter a coluna `associacao_id uuid NOT NULL` e as
policies abaixo como minimo:

```sql
-- Habilitar RLS na tabela (exemplo generico)
ALTER TABLE <tabela> ENABLE ROW LEVEL SECURITY;

-- Policy de leitura
CREATE POLICY <tabela>_select ON <tabela>
  FOR SELECT
  USING (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );

-- Policy de escrita (INSERT)
CREATE POLICY <tabela>_insert ON <tabela>
  FOR INSERT
  WITH CHECK (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );

-- Policy de atualizacao
CREATE POLICY <tabela>_update ON <tabela>
  FOR UPDATE
  USING (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  )
  WITH CHECK (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
```

As specs de modulo subsequentes (SPEC-002 a SPEC-006) reproduzem esse padrao
em suas respectivas tabelas sem precisar redefinir a logica aqui.

---

## 5. API

O MVP nao expoe endpoints de autenticacao proprios: toda a autenticacao e
delegada ao Supabase Auth (client-side SDK e API REST do Supabase). A camada
de aplicacao Next.js age como intermediaria apenas para proteger rotas
server-side.

### 5.1. Rotas Next.js protegidas

Toda rota abaixo de `/app/*` e protegida por middleware Next.js que verifica
a sessao do Supabase. Rotas publicas: `/login` e `/` (redirect para login se
sem sessao).

Middleware (pseudocodigo):

```
Para cada requisicao a /app/*:
  1. Obter sessao do Supabase Auth (cookies).
  2. Se sem sessao valida: redirect para /login.
  3. Se sessao valida: injetar associacao_id no contexto da requisicao e
     prosseguir.
```

### 5.2. Endpoints de autenticacao (Supabase Auth, nao customizados)

| Operacao       | Metodo Supabase Auth SDK           | Descricao                          |
|----------------|------------------------------------|------------------------------------|
| Login          | `signInWithPassword({email,password})` | Cria sessao e retorna JWT      |
| Logout         | `signOut()`                        | Invalida sessao local e no servidor|
| Refresh token  | automatico pelo SDK                | Renova JWT antes de expirar        |

Nenhum endpoint REST proprio e criado nesta spec. O Next.js server action ou
route handler pode encapsular a chamada ao SDK, mas o protocolo subjacente e
do Supabase Auth.

### 5.3. Endpoint de leitura do perfil autenticado

```
GET /api/me
```

Resposta (200):

```json
{
  "id": "<uuid do operador>",
  "associacao_id": "<uuid da associacao>",
  "nome_exibicao": "<string>",
  "ativo": true,
  "associacao": {
    "id": "<uuid>",
    "nome": "<string>",
    "slug": "<string>"
  }
}
```

Resposta de erro (401): `{ "error": "nao autenticado" }`.

Este endpoint e usado pelo frontend para popular o contexto global da
associacao apos o login.

---

## 6. UI

### 6.1. Tela de Login (`/login`)

Elementos obrigatorios:
- Campo e-mail (type="email", required, autocomplete="email").
- Campo senha (type="password", required, autocomplete="current-password").
- Botao "Entrar".
- Mensagem de erro inline (sem distinguir e-mail de senha invalidos).
- Estado de carregamento no botao durante a requisicao.

Elementos fora do escopo desta spec:
- Link "Esqueci minha senha" pode estar presente como placeholder, mas o
  fluxo completo de recuperacao nao e especificado aqui.
- Registro autonomo de operador: nao existe no MVP.

Fluxo apos submit bem-sucedido:
1. SDK do Supabase Auth retorna sessao.
2. Frontend chama `GET /api/me` para obter `associacao_id` e dados do perfil.
3. Contexto global da aplicacao e populado.
4. Redirect para `/app/painel`.

### 6.2. Contexto global da associacao

A aplicacao mantem um contexto React (ou estado global equivalente) com:

```typescript
interface ContextoAssociacao {
  associacaoId: string;
  associacaoNome: string;
  operadorId: string;
  operadorNome: string;
}
```

Esse contexto e inicializado apos login e consumido por todos os componentes
que precisam do `associacaoId` (cabecalho, formularios, chamadas de API).

O `associacaoId` nao e passado manualmente nas chamadas ao Supabase client:
o JWT ja o carrega e o RLS o aplica automaticamente. O contexto existe para
exibicao na UI (nome da associacao no cabecalho, por exemplo) e para
construcao de queries de front que precisem do valor explicitamente.

### 6.3. Cabecalho autenticado

Toda pagina protegida exibe:
- Nome da associacao.
- Nome do operador logado.
- Botao de logout.

### 6.4. Redirecionamentos

| Situacao                               | Destino              |
|----------------------------------------|----------------------|
| Acesso a `/` sem sessao                | `/login`             |
| Acesso a `/app/*` sem sessao           | `/login`             |
| Login bem-sucedido                     | `/app/painel`        |
| Logout                                 | `/login`             |
| Acesso a `/login` com sessao ativa     | `/app/painel`        |

---

## 7. Observabilidade

- Falhas de login (credenciais invalidas) sao registradas pelo Supabase Auth
  com timestamp e IP; nao ha log adicional no MVP.
- Erros de RLS (tentativa de acesso a dados de outra associacao) geram erro
  Postgres que o Supabase expoe no painel de logs; monitorar via Supabase
  Dashboard.
- O endpoint `GET /api/me` deve logar (server-side) o `user_id` e o
  `associacao_id` resolvido a cada chamada bem-sucedida, para auditoria de
  acesso.
- Metrica minima: taxa de falhas de login (volume de erros 401 no Supabase
  Auth). Alerta se superar limiar configuravel (protecao basica contra
  credential stuffing).

---

## 8. Seguranca e LGPD

### 8.1. Seguranca

- Senhas armazenadas pelo Supabase Auth com bcrypt; nenhuma senha transita
  ou e armazenada na camada de aplicacao.
- Toda comunicacao por HTTPS (RNF-04).
- O JWT tem tempo de vida padrao do Supabase (1 hora); o refresh token e
  rotacionado a cada uso.
- A service_role key do Supabase nao e exposta ao cliente; e usada apenas
  server-side para operacoes administrativas.
- Nao ha endpoint publico de registro de operadores: cadastro so por
  administrador autenticado via Supabase Dashboard, eliminando o vetor de
  auto-registro nao autorizado.
- Rate limiting de login: Supabase Auth aplica rate limiting nativo por IP;
  configuracao adicional pode ser feita no painel do projeto.
- O claim `associacao_id` no JWT e gerado server-side pela funcao Postgres
  `custom_jwt_claims`; nao pode ser forjado pelo cliente.

### 8.2. LGPD

- O e-mail do operador e dado pessoal; e armazenado exclusivamente no
  `auth.users` gerenciado pelo Supabase, com criptografia em repouso.
- A tabela `operadores` armazena apenas `nome_exibicao`; nenhum dado sensivel
  adicional nesta spec.
- O log de acesso (item 7) deve ser tratado como dado de monitoramento e
  retido pelo periodo minimo necessario, definido pela politica de retencao da
  associacao.
- Direito de exclusao: remover o operador de `auth.users` propaga para
  `operadores` via ON DELETE CASCADE; os registros de negocio vinculados ao
  operador sao tratados nas specs de modulo correspondentes.

---

## 9. Testes

### 9.1. Testes unitarios

- Funcao `custom_jwt_claims`: dado um `user_id` valido, retorna o
  `associacao_id` correto; dado um `user_id` inexistente, retorna null sem
  lancar excecao.
- Middleware de rotas: mock de sessao ausente deve resultar em redirect para
  `/login`; mock de sessao valida deve prosseguir e injetar contexto.

### 9.2. Testes de integracao (Supabase local via `supabase start`)

- Login com credenciais validas: sessao criada, JWT contem `associacao_id`.
- Login com senha errada: erro sem sessao.
- SELECT em tabela com RLS com JWT de associacao A nao retorna linhas de
  associacao B.
- INSERT com `associacao_id` diferente do JWT e rejeitado pelo RLS.
- Logout invalida o token; requisicao subsequente com o mesmo token e
  rejeitada.

### 9.3. Relacao com o oraculo do motor aprovado

Esta spec nao aciona diretamente o motor de rateio (`detectar_tipo`,
`reconciliar.py`). No entanto, o isolamento por RLS garantido aqui e
precondition para que os arquivos BASE e RATEIO exportados reflitam
exclusivamente os dados de uma associacao. Sem RLS funcionando, a exportacao
pode contaminar dados entre associacoes, quebrando o invariante de fechamento
do motor. Portanto:

- O harness de reconciliacao da SPEC-000 deve ser rodado sobre dados de uma
  associacao isolada, confirmando que o motor processa sem erro e o invariante
  e zero.
- Se o invariante nao for zero e o motor nao apresentar erro proprio, investigar
  primeiro se o RLS esta filtrando corretamente os registros exportados.

### 9.4. Criterio de aceite para implantacao

Os CAs 001-1 a 001-7 (secao 3) devem passar em ambiente de staging antes do
deploy em producao.

---

## 10. Rollout

1. Aplicar migracao SQL que cria as tabelas `associacoes` e `operadores` e
   registra a funcao `custom_jwt_claims` no hook de JWT personalizado do
   Supabase Auth.
2. Inserir manualmente o registro da associacao via Supabase Dashboard (um
   registro no MVP).
3. Cadastrar o primeiro operador via Supabase Authentication > Users no
   painel; inserir manualmente a linha correspondente em `operadores` com o
   `associacao_id` correto.
4. Verificar que o JWT emitido no login contem o claim `associacao_id`
   inspecionando o token em jwt.io ou via log server-side.
5. Executar o conjunto de testes de integracao (secao 9.2) antes de liberar
   acesso ao painel.
6. Sem feature flag necessaria: auth e pre-requisito de tudo; entra ativo
   desde o primeiro deploy.

Rollback: se a funcao `custom_jwt_claims` falhar, o claim `associacao_id`
sera null no JWT e o RLS bloqueara todas as queries. Correcao: rever a funcao
e retrigerar o hook; nao ha perda de dados.

---

## 11. Questoes em aberto

1. Confirmacao do mecanismo exato de custom JWT claims no Supabase: a
   documentacao menciona `auth.hook` (Supabase > 2.x) e o mecanismo legado
   por trigger. Definir qual versao do Supabase esta provisionada no projeto
   e ajustar a implementacao.

2. Recuperacao de senha: o Supabase Auth oferece fluxo nativo (email de
   reset). Decidir se o MVP usa o link padrao do Supabase ou se precisa de
   pagina customizada dentro do Next.js.

3. Multiplas associacoes: o schema suporta N, mas o fluxo de selecao de
   associacao apos login nao esta especificado. Quando o produto crescer para
   mais de uma associacao, uma tela de selecao ou um subdominio por tenant
   precisara ser definido.

4. Perfis de acesso (roles): no MVP todos os operadores tem acesso identico.
   Quando papeis distintos (administrador, operador de campo, auditor) forem
   necessarios, o modelo de `operadores` precisara de uma coluna `papel` e as
   policies RLS serao refinadas.

5. Inativacao de operador: a coluna `ativo` existe na tabela, mas nao ha
   policy que bloqueie o login de um operador inativo. O bloqueio efetivo
   exige desabilitar o usuario no Supabase Auth Dashboard; essa sincronizacao
   nao esta automatizada no MVP.
