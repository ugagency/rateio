# SPEC-004 -- Admissao Verificada (App Visto)

Status: rascunho. Data: 2026-05-29.
Responsavel: Engenheiro de Vistoria.
Requisitos cobertos: RF-VIST-01, RF-VIST-02, RF-VIST-03, RF-VIST-04,
RF-VIST-05, RF-VIST-06, RNF-02, RNF-03.

---

## 1. Contexto

A vistoria antifraude e o portao de admissao do MVP: o momento em que um
veiculo cadastrado, pertencente a um associado, passa por uma esteira
fotografica verificada e se torna apto a constar no arquivo BASE e a gerar
cotas no denominador do rateio.

A inspiracao vem do App Visto (Hinova). Os mecanismos antifraude essenciais
foram adaptados para o contexto de PWA, conforme a decisao 3 do ADR-001
(captura ao vivo via `getUserMedia`, sem app nativo no MVP). O modelo nativo
oferece protecao adicional contra adulteracao de imagens e de dados de
localizacao, porem a captura ao vivo com carimbo imutavel por foto ja
representa a barreira principal contra os cenarios de fraude mais comuns
(foto de galeria, foto de veiculo de terceiro, foto de momento anterior ao
sinistro).

Posicao na cadeia de admissao:

  associado (SPEC-002)
    -> veiculo e cota (SPEC-003)
      -> vistoria verificada (esta spec)
        -> veiculo admitido, apto a constar na BASE (SPEC-005, SPEC-000)

A vistoria so finaliza completa. Nao existe finalizacao parcial nem
aproveitamento de fotos de vistorias incompletas. Uma vistoria finalizada e
imutavel: nenhum campo, foto ou metadado pode ser alterado apos o status
`finalizada`.

Casos fora do escopo desta spec: vistorias por frota, vistorias para pessoa
juridica sem smartphone e qualquer forma de upload de arquivo de galeria.
Esses casos ficam para fase posterior.

---

## 2. Requisitos

Esta spec cobre os seguintes requisitos do MVP-SCOPE:

- RF-VIST-01: O sistema DEVE permitir definir scripts de vistoria por tipo
  (carro, moto, reboque, revistoria), com quantidade e ordem de fotos.
- RF-VIST-02: O sistema DEVE capturar fotos somente ao vivo, bloqueando upload
  da galeria.
- RF-VIST-03: O sistema DEVE carimbar cada foto com data, hora e
  geolocalização (latitude e longitude).
- RF-VIST-04: O sistema DEVE exigir o fluxo sequencial completo (selfie,
  documento, fotos do veiculo) e so marcar a vistoria como `finalizada`
  quando concluida inteira.
- RF-VIST-05: O sistema DEVE registrar o inicio, cada captura e a finalizacao
  com horario (base da timeline antifraude).
- RF-VIST-06: O sistema DEVE vincular a vistoria finalizada ao veiculo,
  habilitando-o a admissao.

Requisitos nao funcionais aplicaveis:

- RNF-01: Isolamento por associacao (RLS).
- RNF-02: Trilha de auditoria imutavel nas operacoes de admissao.
- RNF-03: Fotos e metadados de vistoria sao imutaveis apos finalizacao.
- RNF-04: Comunicacao por HTTPS; dados pessoais tratados conforme a LGPD.

O que esta spec nao cobre: validacao por IA ou OCR de documentos e fotos
(entrada manual no MVP); integracao com sistemas externos como SGA; gateway
de pagamento; app nativo iOS e Android.

---

## 3. Criterios de Aceite

### CA-004-1: Criacao de script de vistoria

```
Given um operador autenticado,
When envia um payload valido com tipo (carro, moto, reboque ou revistoria),
lista ordenada de etapas e tempo maximo configuravel,
Then o sistema persiste o script com id gerado, versao 1 e status `ativo`,
e retorna HTTP 201.
```

### CA-004-2: Versionamento de script ja utilizado

```
Given um script de vistoria com id X que ja foi referenciado em ao menos
uma vistoria (a realizar ou finalizada),
When um operador tenta excluir o script X,
Then o sistema rejeita a exclusao com HTTP 409 e mantem o script intacto.
O operador pode inativar o script (status `inativo`), mas nao excluir.
```

### CA-004-3: Inicio de vistoria

```
Given um veiculo com status `pendente_vistoria` e um script ativo compativel
com o tipo do veiculo,
When o operador inicia a vistoria pelo painel,
Then o sistema cria o registro de vistoria com status `a_realizar`, registra
o timestamp de inicio e retorna o token de sessao de vistoria com a sequencia
de etapas do script.
```

### CA-004-4: Bloqueio de galeria

```
Given uma sessao de vistoria ativa no navegador do executante,
When o PWA solicita uma captura e o executante tenta usar qualquer metodo
diferente de camera ao vivo (upload de arquivo, colar imagem, URL de imagem),
Then o sistema rejeita a tentativa no cliente (restricao de atributos HTML e
ausencia de campo de upload), exibe mensagem de erro e permanece aguardando
captura ao vivo pela camera.
```

Limite do MVP (ADR-002 C8): a barreira e implementada no cliente via captura
ao vivo pela camera do PWA, sem campo de upload de arquivo. A verificacao
server-side por metadados (por exemplo, analise EXIF) nao e implementada no
MVP e fica para fase posterior.

### CA-004-5: Carimbo imutavel por foto

```
Given uma foto capturada ao vivo dentro de uma sessao de vistoria,
When a foto e enviada ao servidor,
Then o servidor grava os metadados (timestamp UTC, latitude, longitude, ordem
da etapa) vinculados ao arquivo no Storage, e esses metadados nao podem ser
alterados por nenhuma operacao subsequente.
```

### CA-004-6: QR Code de verificacao na foto

```
Given uma foto com carimbo gravado,
When a foto e exibida no painel ou baixada,
Then ela contem um QR Code embutido com lat, long, data e hora verificaveis,
legivel por qualquer leitora generica de QR Code.
```

### CA-004-7: Fluxo sequencial obrigatorio

```
Given uma sessao de vistoria ativa com etapas [selfie, documento, frente,
traseira, lateral_esquerda, lateral_direita, teto, placa],
When o executante tenta capturar a etapa N+1 sem ter concluido a etapa N,
Then o sistema bloqueia o avanco, exibe a etapa atual pendente e nao avanca
na sequencia.
```

### CA-004-8: Cronometro de tempo maximo

```
Given uma sessao de vistoria ativa com tempo maximo configurado de T minutos,
When o tempo decorrido desde o inicio ultrapassa T minutos,
Then o sistema invalida a sessao, descarta todas as fotos capturadas ate
aquele momento, registra o evento de expiracao na timeline e exige que o
operador inicie uma nova vistoria do zero.
```

### CA-004-9: Intervalo entre fotos registrado

```
Given uma sessao de vistoria com multiplas capturas registradas,
When a vistoria e visualizada no painel pelo operador,
Then a timeline exibe o timestamp de cada captura, permitindo calcular o
intervalo entre fotos consecutivas.
```

### CA-004-10: Finalizacao somente quando completa

```
Given uma sessao de vistoria com todas as etapas do script concluidas,
When o executante aciona "Finalizar",
Then o sistema transiciona o status para `finalizada`, registra o timestamp
de finalizacao, e o veiculo vinculado passa para status `ativo` (conforme
ADR-002 C1; o valor `admitido` nao existe no enum).
Nenhuma alteracao e permitida a partir desse momento.
```

### CA-004-11: Imutabilidade pos finalizacao

```
Given uma vistoria com status `finalizada`,
When qualquer operador tenta alterar dados, substituir fotos ou reabrir
a vistoria via API ou painel,
Then o sistema rejeita a operacao com HTTP 403 e nao modifica nenhum dado
da vistoria.
```

### CA-004-12: Habilitacao do veiculo a admissao

```
Given um veiculo com vistoria `finalizada`,
When o exportador da BASE consulta veiculos ativos na competencia,
Then o veiculo aparece na contagem de cotas do seu segmento (a soma reflete
na coluna BAIXADO ou ABERTO conforme a situacao do boleto na SPEC-005).
```

### CA-004-13: Refazer foto -- janela de um dia

```
Given uma vistoria com status `a_realizar` e etapa N ja concluida,
When o operador solicita refazer a foto da etapa N dentro do mesmo dia
ou em ate um dia apos a captura original,
Then o sistema permite substituir a foto da etapa N uma unica vez, registra
o evento de substituicao na timeline com o timestamp e o id do operador, e
mantem a foto original no Storage para auditoria.
```

### CA-004-14: Refazer foto -- fora da janela

```
Given uma etapa ja concluida cuja captura ocorreu ha mais de um dia,
When o operador solicita refazer a foto dessa etapa,
Then o sistema rejeita a substituicao com HTTP 422 e informa que a janela
de refacao expirou.
```

### CA-004-15: Refazer foto -- tentativa dupla

```
Given uma etapa que ja sofreu uma substituicao de foto dentro da janela,
When o operador tenta substituir a foto dessa etapa novamente,
Then o sistema rejeita a segunda substituicao com HTTP 422 (refacao permitida
apenas uma vez por etapa).
```

### CA-004-16: Isolamento por associacao

```
Given vistorias de duas associacoes distintas cadastradas no sistema,
When um operador da associacao A lista ou consulta vistorias,
Then ele visualiza somente vistorias onde associacao_id = A, sem acesso a
dados da associacao B.
```

---

## 4. Modelo de Dados

O isolamento por associacao e feito pela coluna `associacao_id` em cada
tabela combinada com RLS via claim do JWT, conforme ADR-002 C2. A forma
canonica esta detalhada na secao 4.6.

### 4.1 Tabela `scripts_vistoria`

Define os roteiros reutilizaveis de captura, versionados por ID. Nunca
excluir se ja referenciado; apenas inativar.

```sql
create table scripts_vistoria (
  id            uuid primary key default gen_random_uuid(),
  associacao_id uuid not null references associacoes(id) on delete restrict,
  tipo          text not null
                  check (tipo in ('carro', 'moto', 'reboque', 'revistoria')),
  descricao     text,
  tempo_max_min integer not null check (tempo_max_min > 0),
                                 -- tempo maximo em minutos antes de expirar
  status        text not null default 'ativo'
                  check (status in ('ativo', 'inativo')),
  criado_em     timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
```

### 4.2 Tabela `etapas_script`

Etapas do script em ordem sequencial. A ordem e definida pela coluna
`sequencia` (inteiro, comeca em 1).

```sql
create table etapas_script (
  id              uuid primary key default gen_random_uuid(),
  script_id       uuid not null references scripts_vistoria(id)
                    on delete restrict,
  sequencia       integer not null check (sequencia >= 1),
  tipo_etapa      text not null
                    check (tipo_etapa in (
                      'selfie', 'documento', 'frente', 'traseira',
                      'lateral_esquerda', 'lateral_direita', 'teto',
                      'placa', 'chassi', 'outro'
                    )),
  camera_preferencial text not null default 'traseira'
                    check (camera_preferencial in ('frontal', 'traseira')),
  obrigatoria     boolean not null default true,
  instrucao_texto text,
  unique (script_id, sequencia)
);
```

### 4.3 Tabela `vistorias`

Instancia de uma vistoria de um veiculo especifico.

```sql
create table vistorias (
  id              uuid primary key default gen_random_uuid(),
  associacao_id   uuid not null references associacoes(id) on delete restrict,
  veiculo_id      uuid not null references veiculos(id) on delete restrict,
  script_id       uuid not null references scripts_vistoria(id)
                    on delete restrict,
  operador_id     uuid not null references operadores(id) on delete restrict,
  status          text not null default 'a_realizar'
                    check (status in ('a_realizar', 'finalizada', 'expirada')),
  iniciado_em     timestamptz not null default now(),
  finalizado_em   timestamptz,
  expirado_em     timestamptz,
  token_sessao    uuid not null default gen_random_uuid(),
  criado_em       timestamptz not null default now()
);
```

Notas:
- `token_sessao` e gerado no inicio e referenciado pelo PWA para autenticar
  as chamadas de upload de foto sem expor o JWT do operador ao dispositivo
  do executante no campo.
- Apenas uma vistoria por veiculo pode ter status `a_realizar`
  simultaneamente. Restricao aplicada por partial unique index:

```sql
create unique index vistorias_veiculo_em_andamento
  on vistorias (veiculo_id)
  where status = 'a_realizar';
```

### 4.4 Tabela `capturas_vistoria`

Registro de cada foto capturada em uma etapa.

```sql
create table capturas_vistoria (
  id              uuid primary key default gen_random_uuid(),
  vistoria_id     uuid not null references vistorias(id) on delete restrict,
  etapa_id        uuid not null references etapas_script(id) on delete restrict,
  associacao_id   uuid not null references associacoes(id) on delete restrict,
  storage_path    text not null,
                  -- caminho no Supabase Storage, imutavel apos criacao
  capturado_em    timestamptz not null,
                  -- timestamp do dispositivo no momento da captura
  recebido_em     timestamptz not null default now(),
                  -- timestamp do servidor no momento do recebimento
  latitude        numeric(10, 7),
  longitude       numeric(10, 7),
  substituida_por uuid references capturas_vistoria(id),
                  -- preenchido quando esta foto e substituida (refacao)
  refacao_de      uuid references capturas_vistoria(id),
                  -- preenchido quando esta foto substitui outra
  unico_uso       boolean not null default false
                  -- true se a etapa ja teve uma substituicao
);
```

Notas:
- `storage_path` e imutavel apos o INSERT. A politica RLS bloqueia UPDATE
  nesta tabela para todos os operadores. A substituicao de foto (refacao)
  cria um novo registro, nao modifica o existente.
- A relacao `substituida_por` / `refacao_de` forma um par: quando uma
  refacao ocorre, a captura original recebe `substituida_por = nova_id` e
  a nova captura recebe `refacao_de = original_id`.
- A foto vigente de uma etapa e a que nao tem `substituida_por` preenchido.

### 4.5 Tabela `timeline_vistoria`

Registro cronologico de todos os eventos da vistoria para a trilha
antifraude.

```sql
create table timeline_vistoria (
  id              bigint generated always as identity primary key,
  vistoria_id     uuid not null references vistorias(id) on delete restrict,
  associacao_id   uuid not null references associacoes(id) on delete restrict,
  evento          text not null
                    check (evento in (
                      'inicio', 'captura', 'refacao', 'expiracao',
                      'finalizacao', 'tentativa_galeria'
                    )),
  etapa_id        uuid references etapas_script(id),
  captura_id      uuid references capturas_vistoria(id),
  ocorrido_em     timestamptz not null default now(),
  metadados       jsonb
                  -- informacoes adicionais: ip, user_agent, lat, long, etc.
);
```

Politica de escrita: somente via funcoes de servico (sem permissao de INSERT
direto pelo cliente). Sem UPDATE e sem DELETE por nenhuma role.

### 4.6 Politica RLS

O isolamento e feito pelo claim customizado `associacao_id` presente no JWT,
acessado via `auth.jwt() ->> 'associacao_id'` em todas as policies (ADR-002
C2). Nenhuma policy usa subquery na tabela de operadores para resolver o
tenant; isso evita leituras N+1 e e a forma unica adotada no projeto.

```sql
-- scripts_vistoria
alter table scripts_vistoria enable row level security;
create policy scripts_vistoria_select on scripts_vistoria
  for select using (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
create policy scripts_vistoria_insert on scripts_vistoria
  for insert with check (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
create policy scripts_vistoria_update on scripts_vistoria
  for update using (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  ) with check (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
-- sem DELETE por operador; exclusao bloqueada pela restricao referencial e
-- pela ausencia de policy de DELETE.

-- etapas_script: sem associacao_id direta; acesso via script_id
alter table etapas_script enable row level security;
create policy etapas_script_select on etapas_script
  for select using (
    exists (
      select 1 from scripts_vistoria s
      where s.id = script_id
        and s.associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
    )
  );

-- vistorias
alter table vistorias enable row level security;
create policy vistorias_select on vistorias
  for select using (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
create policy vistorias_insert on vistorias
  for insert with check (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
-- UPDATE somente por funcao de servico (sem policy de UPDATE para role anon
-- ou authenticated diretamente, exceto via service_role).

-- capturas_vistoria: imutavel para o cliente
alter table capturas_vistoria enable row level security;
create policy capturas_vistoria_select on capturas_vistoria
  for select using (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
-- sem INSERT, UPDATE nem DELETE diretamente pelo cliente; apenas via
-- service_role nas funcoes de upload e refacao.

-- timeline_vistoria: somente leitura para o operador
alter table timeline_vistoria enable row level security;
create policy timeline_vistoria_select on timeline_vistoria
  for select using (
    associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  );
```

### 4.7 Supabase Storage

Bucket: `vistorias` (privado, sem acesso publico).

Estrutura de path:
```
vistorias/{associacao_id}/{vistoria_id}/{etapa_id}/{captura_id}.jpg
```

Politica de Storage: leitura permitida apenas para operadores da mesma
associacao; escrita permitida somente via service_role durante o fluxo de
upload autenticado pelo `token_sessao`.

---

## 5. API

Base de URL: `/api/vistorias` e `/api/scripts-vistoria`.

Todas as rotas exigem sessao ativa. As rotas de upload de foto durante a
sessao de campo aceitam autenticacao alternativa por `token_sessao`.

### 5.1 POST /api/scripts-vistoria

Cria um novo script de vistoria.

Request body:

```json
{
  "tipo": "carro | moto | reboque | revistoria",
  "descricao": "string, opcional",
  "tempo_max_min": 30,
  "etapas": [
    {
      "sequencia": 1,
      "tipo_etapa": "selfie",
      "camera_preferencial": "frontal",
      "obrigatoria": true,
      "instrucao_texto": "Posicione o rosto diante da camera com a placa ao fundo."
    }
  ]
}
```

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Script criado. Body: `{ id, tipo, descricao, tempo_max_min, status, etapas: [...] }` |
| 401  | Nao autenticado. |
| 422  | Tipo invalido, tempo_max_min menor ou igual a zero, etapas vazias ou com
        sequencia duplicada. |

### 5.2 PATCH /api/scripts-vistoria/:id

Atualiza descricao, tempo_max_min ou status (ativo/inativo). Campos de etapas
nao sao editaveis diretamente; alteracoes estruturais exigem criar novo script.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Atualizado. |
| 403  | Tentativa de excluir ou alterar tipo de script ja utilizado. |
| 404  | Nao encontrado na associacao. |
| 422  | Payload invalido. |

### 5.3 GET /api/scripts-vistoria

Lista scripts da associacao. Params opcionais: `tipo`, `status`.

### 5.4 POST /api/vistorias

Inicia uma vistoria para um veiculo.

Request body:

```json
{
  "veiculo_id": "<uuid>",
  "script_id": "<uuid>"
}
```

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Vistoria criada. Body: `{ id, veiculo_id, script_id, status, iniciado_em, token_sessao, etapas: [...] }` |
| 409  | Ja existe uma vistoria `a_realizar` para este veiculo. |
| 422  | Veiculo nao encontrado, script inativo ou tipo do script incompativel com
        o segmento do veiculo. |

### 5.5 POST /api/vistorias/:id/capturas

Recebe uma foto de uma etapa. Autenticacao por `token_sessao` (header
`X-Vistoria-Token`) aceita como alternativa ao JWT de operador.

Request: `multipart/form-data` com os campos:

| Campo          | Tipo    | Descricao |
|----------------|---------|-----------|
| `etapa_id`     | string  | UUID da etapa do script. |
| `arquivo`      | file    | Imagem JPEG capturada ao vivo. |
| `capturado_em` | string  | Timestamp ISO 8601 do dispositivo. |
| `latitude`     | number  | Latitude no momento da captura. |
| `longitude`    | number  | Longitude no momento da captura. |

Validacoes:
- A vistoria deve estar com status `a_realizar` e dentro do tempo maximo.
- A etapa deve pertencer ao script da vistoria e ser a proxima da sequencia
  (ou a propria etapa atual, caso seja uma refacao dentro da janela).
- O arquivo deve ser JPEG com tamanho maximo de 10 MB.
- O campo `input` do elemento de upload no PWA DEVE ter `capture="environment"`
  (ou `capture="user"` para selfie) e ausencia de `accept` amplo que permita
  selecao de galeria.

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Captura registrada. Body: `{ captura_id, etapa_id, capturado_em, recebido_em, qrcode_url }` |
| 400  | Tentativa de upload via galeria detectada (Content-Type inesperado ou
        ausencia de metadados de camera). |
| 403  | Vistoria finalizada ou expirada; captura nao permitida. |
| 408  | Vistoria expirou durante o upload. |
| 422  | Etapa fora da sequencia, arquivo invalido ou metadados ausentes. |

### 5.6 POST /api/vistorias/:id/capturas/:captura_id/refazer

Substitui uma foto dentro da janela permitida (mesmo dia ou dia seguinte,
uma unica vez por etapa).

Mesmo schema de request que 5.5 (multipart/form-data).

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Refacao registrada. Body com os dados da nova captura. |
| 403  | Vistoria finalizada ou expirada. |
| 409  | Etapa ja sofreu uma refacao (segunda tentativa bloqueada). |
| 422  | Janela de refacao expirada (mais de um dia apos a captura original). |

### 5.7 POST /api/vistorias/:id/finalizar

Finaliza a vistoria quando todas as etapas obrigatorias estao concluidas.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Vistoria finalizada. Body: `{ id, status: "finalizada", finalizado_em }` |
| 403  | Vistoria ja finalizada. |
| 422  | Etapas obrigatorias pendentes (lista das etapas faltantes no body). |

Pos-finalizacao: o endpoint atualiza `veiculos.status` para `ativo` (ADR-002
C1) numa transacao atomica com a atualizacao de `vistorias.status`.

### 5.8 GET /api/vistorias/:id

Retorna os dados da vistoria com timeline completa e lista de capturas
(sem binarios; apenas metadados e URLs assinadas de leitura com validade de
1 hora).

### 5.9 GET /api/vistorias

Lista vistorias da associacao. Params opcionais: `veiculo_id`, `status`,
`data_inicio`, `data_fim`, paginacao padrao (`page`, `per_page`).

---

## 6. UI

### 6.1 Tela: gerenciamento de scripts de vistoria

Rota sugerida: `/scripts-vistoria`

Elementos:
- Listagem de scripts com colunas: tipo, descricao, numero de etapas, tempo
  maximo, status (ativo/inativo).
- Botao "Novo script" que abre o formulario de criacao.
- Acao de inativar script (nao excluir).
- Visualizacao das etapas do script em ordem sequencial.

### 6.2 Tela: painel de vistorias

Rota sugerida: `/vistorias`

Elementos:
- Lista de vistorias com colunas: veiculo (placa), associado, script, status,
  data de inicio, data de finalizacao.
- Filtros por status e por periodo.
- Botao "Iniciar vistoria" que abre o modal de selecao de veiculo e script.
- Link para a tela de detalhes da vistoria.

### 6.3 Modal: iniciar vistoria

Campos:
- Selecao de veiculo (busca por placa, filtra veiculos com status
  `pendente_vistoria`).
- Selecao de script (exibe apenas scripts ativos e compativeis com o segmento
  do veiculo).
- Botao "Iniciar": aciona POST /api/vistorias e redireciona para a tela de
  execucao de vistoria (ou gera link para o executante no campo).

### 6.4 Tela de execucao de vistoria (PWA, campo)

Rota sugerida: `/vistoria/sessao/:token_sessao`

Esta e a tela usada no dispositivo do executante durante a captura. Ela e
acessivel via link gerado pelo operador do painel (o link carrega o
`token_sessao`). Nao exige login de operador completo.

Comportamento:
- Exibe a etapa atual com instrucao em texto e indicador de progresso
  (etapa N de M).
- Exibe o cronometro regressivo ate o tempo maximo da sessao.
- O botao de captura aciona `getUserMedia` com:
  - `video: false`
  - `audio: false`
  - Para selfie: `facingMode: "user"`.
  - Para demais etapas: `facingMode: "environment"`.
- O elemento `<input type="file">` de fallback, se presente, DEVE ter o
  atributo `capture` definido e NENHUM `accept` que permita galeria; a
  intencao e nunca abrir o seletor de arquivos.
- Apos captura: exibe previa da foto com botao de confirmacao e botao de
  repetir (antes de enviar). O envio dispara POST /api/vistorias/:id/capturas.
- Avanca automaticamente para a proxima etapa apos confirmacao.
- Ao concluir todas as etapas, exibe botao "Finalizar vistoria" que aciona
  POST /api/vistorias/:id/finalizar.
- Em caso de expiracao do cronometro, exibe tela de aviso e bloqueia novas
  capturas.

### 6.5 Tela: detalhe e timeline da vistoria

Rota sugerida: `/vistorias/:id`

Elementos:
- Cabecalho: veiculo (placa, segmento), associado, script utilizado, status,
  timestamps de inicio e finalizacao.
- Timeline cronologica: evento, timestamp, etapa envolvida, intervalo desde
  a captura anterior.
- Grade de fotos: uma miniatura por etapa em ordem sequencial; clique abre a
  foto em tamanho original com o QR Code visivel.
- Indicacao visual de etapas refazidas (foto original e substituta).
- Mapa de geolocalizacao: pontos das capturas sobrepostos; dispersao
  geografica excessiva e destacada visualmente.

---

## 7. Observabilidade

- Logar no nivel INFO cada evento de inicio, captura e finalizacao de
  vistoria, com `vistoria_id`, `veiculo_id` e `associacao_id`, sem incluir
  binarios ou dados pessoais nos logs.
- Logar no nivel WARN cada tentativa de upload bloqueada como galeria
  (`tentativa_galeria`) e cada expiracao de sessao, com `vistoria_id` e
  timestamp.
- Logar no nivel ERROR falhas de gravacao no Storage (arquivo nao persistido
  apesar de resposta 201) para deteccao de inconsistencia entre banco e
  storage.
- A tabela `timeline_vistoria` e a trilha persistente primaria.
- Metricas recomendadas:
  - Numero de vistorias iniciadas, finalizadas e expiradas por dia e por
    associacao.
  - Tempo medio de duracao de vistoria (iniciado_em ate finalizado_em).
  - Taxa de tentativas bloqueadas de galeria por vistoria.
  - Distribuicao de intervalos entre capturas consecutivas (sinal antifraude).

---

## 8. Seguranca e LGPD

### 8.1 Seguranca

- Toda comunicacao por HTTPS (RNF-04); sem endpoint HTTP.
- O bucket `vistorias` no Storage e privado. URLs de acesso sao assinadas com
  validade maxima de 1 hora, geradas sob demanda.
- O `token_sessao` tem validade igual ao tempo maximo do script mais uma
  margem de 5 minutos. Apos a expiracao ou a finalizacao da vistoria, o token
  e invalidado e nao aceita novos uploads.
- A imutabilidade pos-finalizacao (RNF-03) e garantida em tres camadas:
  1. Policy RLS: sem UPDATE nem DELETE em `capturas_vistoria` para qualquer
     role de cliente.
  2. Logica de servico: o endpoint de finalizacao verifica `status` antes de
     qualquer operacao e rejeita se ja `finalizada`.
  3. Storage: o path de uma captura finalizada nao e reescritivel pela policy
     do bucket.
- A dispersao geografica excessiva entre capturas nao bloqueia
  automaticamente a vistoria no MVP (sinalizacao manual pelo operador no
  painel); essa regra automatica entra em fase posterior.
- Limite do MVP para bloqueio de galeria (ADR-002 C8): a barreira contra foto
  de galeria e a captura ao vivo pela camera do PWA. Nao ha campo de upload
  de arquivo na interface. A verificacao server-side por metadados EXIF ou
  outro mecanismo de deteccao de origem da imagem nao e implementada no MVP;
  esse controle fica para fase posterior.

### 8.2 LGPD

- A selfie e a foto do documento sao dados biometricos e dados pessoais
  sensiveis. Devem ser armazenados com finalidade declarada (admissao
  verificada) e retidos somente pelo periodo necessario definido pela politica
  da associacao.
- Nada do dispositivo do executante e monitorado alem dos metadados de
  captura (lat, long, timestamp). Sem acesso a contatos, historico de
  navegacao ou outros sensores (conformidade com a nota do App Visto sobre
  LGPD).
- O controle antifraude e exercido pela timeline pos-fato, nao por
  monitoramento em tempo real do dispositivo.
- O mapa de geolocalizacao exibido no painel e restrito a operadores da
  mesma associacao (RLS).
- Direito de exclusao: a foto original de uma refacao e mantida para
  auditoria; sua exclusao so pode ocorrer por determinacao legal documentada,
  por operacao administrativa com service_role, fora do fluxo normal do MVP.

---

## 9. Testes

### 9.1 Testes unitarios

- Validacao de sequencia de etapas: dado um script com N etapas, verificar
  que avanco sem etapa anterior concluida e bloqueado.
- Logica de janela de refacao: captura com timestamp ha 0 horas: permitida;
  ha 23 horas: permitida; ha 25 horas: bloqueada; ja refazida uma vez:
  bloqueada.
- Expiracao de sessao: dado um `iniciado_em` e um `tempo_max_min`, verificar
  que a funcao de verificacao retorna expirado apos o prazo.
- Geracao de QR Code: dado um conjunto de metadados (lat, long, data, hora),
  verificar que o QR Code codificado pode ser decodificado de volta para os
  mesmos valores.

### 9.2 Testes de integracao (API)

- POST /api/vistorias com veiculo ja em vistoria `a_realizar`: retorna 409.
- POST /api/vistorias/capturas com arquivo que nao e JPEG ao vivo: retorna 400.
- POST /api/vistorias/capturas com etapa fora de sequencia: retorna 422.
- POST /api/vistorias/capturas com sessao expirada: retorna 408.
- POST /api/vistorias/:id/finalizar com etapas obrigatorias pendentes: retorna 422.
- POST /api/vistorias/:id/finalizar com todas as etapas concluidas: retorna 200
  e `veiculos.status` = `ativo` (ADR-002 C1).
- PATCH ou PUT em `capturas_vistoria` com JWT de operador: rejeitado pelo RLS.
- GET /api/vistorias com JWT de associacao B nao retorna vistorias da
  associacao A.

### 9.3 Relacao com o oraculo do motor aprovado

A vistoria finalizada e a precondition para que o veiculo apareca no arquivo
BASE exportado pelo MVP. A ligacao com o motor e:

  vistoria `finalizada`
    -> `veiculos.status = ativo` (ADR-002 C1)
      -> veiculo entra na contagem de cotas da BASE (SPEC-005, SPEC-000)
        -> `detectar_tipo` reconhece o arquivo BASE
          -> motor roda com invariante igual a zero

Portanto, no harness de reconciliacao (SPEC-000, secao 6):

- Fixture de teste deve incluir ao menos um veiculo por segmento (LEVES,
  MOTOS, PESADOS) com vistoria finalizada e boleto baixado na competencia.
- O harness verifica que a coluna BAIXADO do arquivo BASE exportado reflete
  exatamente a contagem de cotas desses veiculos.
- Se o invariante nao for zero e o motor nao apresentar erro proprio,
  investigar se ha veiculos sem vistoria finalizada sendo incluidos na
  contagem (seria bug no filtro da SPEC-005).

---

## 10. Rollout

1. Aplicar migrations de banco nesta ordem:
   a. `scripts_vistoria` e `etapas_script` com constraints e RLS.
   b. `vistorias` com partial unique index e RLS.
   c. `capturas_vistoria` com RLS (sem UPDATE/DELETE para cliente).
   d. `timeline_vistoria` com RLS (somente leitura para cliente).
   e. Criar bucket privado `vistorias` no Supabase Storage com as policies
      de leitura e escrita descritas na secao 4.7.
2. Cadastrar ao menos um script de vistoria ativo por tipo de veiculo previsto
   (carro, moto) antes de liberar o fluxo de admissao.
3. Habilitar a rota PWA `/vistoria/sessao/:token_sessao` apenas para HTTPS;
   bloquear acesso HTTP no middleware Next.js.
4. Rodar os testes de integracao (secao 9.2) em ambiente de staging com um
   veiculo real de teste, verificando timeline, QR Code e imutabilidade.
5. Validar o aceite funcional manual com base nos criterios de aceite da
   secao 3, cobrindo ao menos CA-004-1 a CA-004-16.
6. Incluir ao menos um veiculo admitido por vistoria no fixture de teste do
   harness de reconciliacao (SPEC-000) e confirmar invariante zero antes do
   deploy em producao.
7. Feature flag recomendada: habilitar o modulo de vistoria somente apos as
   migrations de SPEC-002 (associados) e SPEC-003 (veiculos) estarem aplicadas
   e testadas.

Rollback: as migrations de vistoria nao alteram tabelas de SPEC-002 e SPEC-003.
Em caso de falha, reverter as migrations de vistoria sem impacto no cadastro
de associados e veiculos.

---

## 11. Questoes em aberto

1. Deteccao de galeria via PWA: RESOLVIDO (ADR-002 C8). No MVP, a barreira e
   a captura ao vivo pela camera do PWA, sem campo de upload de arquivo. A
   verificacao server-side por metadados EXIF ou similar nao e implementada
   no MVP; fica para fase posterior. Decisao registrada como limite conhecido
   do MVP.

2. Geolocalizacao como campo obrigatorio: em ambientes sem sinal GPS (interior
   de edificios, areas rurais sem cobertura), a coleta de lat/long pode falhar
   ou retornar valores imprecisos. Decidir se a captura sem coordenadas de GPS
   e permitida (com aviso ao operador) ou bloqueada.

3. QR Code embutido na imagem: a especificacao determina QR Code na foto, mas
   nao define se ele e gravado no binario da imagem (watermark) ou gerado
   dinamicamente na exibicao. A opcao de watermark e mais robusta para
   impressao e compartilhamento offline; a opcao dinamica e mais simples de
   implementar. Decidir antes da implementacao.

4. Mapa de geolocalizacao no painel: a spec descreve exibicao de pontos no
   mapa. Definir qual provedor de tiles/mapas sera usado (por exemplo, Leaflet
   com OpenStreetMap) e se ha custo ou limite de uso a considerar no MVP.

5. Link inteligente para o executante: a spec atual gera um link com
   `token_sessao` para o campo. Definir se esse link e enviado manualmente
   pelo operador (copiar e colar) ou se o sistema deve enviar por e-mail ou
   SMS. Envio automatico envolve integracao com servico externo e esta fora
   do escopo do MVP neste momento.

6. Compatibilidade de tipo de script com segmento de veiculo: a validacao
   de compatibilidade (por exemplo, script tipo `moto` so para veiculos do
   segmento MOTOS) esta descrita como requisito, mas a tabela de mapeamento
   entre tipo de script e segmento nao esta formalizada. Definir se a relacao
   e fixa (enum hardcoded) ou parametrizavel por associacao.
