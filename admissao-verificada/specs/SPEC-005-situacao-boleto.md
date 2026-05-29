# SPEC-005 — Situacao de Boleto por Competencia

Status: rascunho. Data: 2026-05-29.
Responsavel: Engenheiro Backend.

---

## 1. Contexto

O denominador do rateio e a soma de cotas dos veiculos com status `ativo` e
situacao de boleto `baixado` na competencia, por segmento. Esse numero alimenta
diretamente a coluna BAIXADO de cada segmento no arquivo BASE, que o motor
aprovado utiliza para calcular o rateio (ver SPEC-000, secoes 2 e 4). Status do
veiculo e situacao de boleto sao eixos distintos: um veiculo ativo com boleto
`aberto` entra em cotas abertas, nao no denominador. A situacao `cancelado` e
apenas informativa e nao entra no denominador nem no invariante (ADR-002 C1 e
C7).

Para que o app possa construir a BASE, ele precisa saber, para cada veiculo
ativo (status `ativo`, vistoria finalizada per SPEC-004), qual foi a situacao
do boleto naquela competencia: baixado (pago), aberto (inadimplente) ou
cancelado. Essa situacao nao e derivada de um gateway de pagamento real; no MVP
ela e registrada manualmente pelo operador ou importada por arquivo simples.

A competencia e representada internamente como uma coluna `date` no primeiro dia
do mes (por exemplo 2026-06-01). A entrada de API aceita o formato `AAAA-MM`; a
exibicao na UI usa `MM/AAAA` (ADR-002 C3). Um veiculo pode ter no maximo uma
situacao de boleto por competencia. A ausencia de registro para uma competencia
significa que o veiculo nao esta na base daquele mes; o app nao deve inclui-lo
no calculo da BASE se nao houver registro de situacao.

A consolidacao por segmento (somar cotas de veiculos baixados, abertos e
cancelados por segmento) e o passo intermediario entre os registros individuais
e o arquivo BASE. Ela deve ser calculada dinamicamente a partir dos registros de
situacao e nunca persistida como um totalizador fixo, evitando inconsistencias.

Esta spec se apoia nas tabelas `veiculos` (SPEC-003) e `associacoes` (SPEC-001).
A exportacao que consome a consolidacao e tratada na SPEC-006 (exportacao
BASE/RATEIO) junto com os eventos.

---

## 2. Requisitos

Esta spec cobre os seguintes requisitos do MVP-SCOPE:

- RF-SIT-01: O sistema DEVE registrar, por veiculo e competencia, a situacao
  do boleto (baixado, aberto, cancelado).
- RF-SIT-02: O sistema DEVE consolidar, por segmento, as cotas baixadas,
  abertas e canceladas da competencia.

Requisitos nao funcionais aplicaveis:

- RNF-01: Isolamento por associacao (RLS).
- RNF-02: Trilha de auditoria imutavel nas operacoes de registro de situacao.
- RNF-04: Comunicacao por HTTPS; dados pessoais tratados conforme a LGPD.

---

## 3. Criterios de Aceite

### AC-001 — Registro de situacao com dados validos

Given um operador autenticado na associacao A e um veiculo com status `ativo`
pertencente a essa associacao,
When o operador envia `veiculo_id`, `competencia` (formato AAAA-MM) e
`situacao` (baixado, aberto ou cancelado) para o endpoint de criacao,
Then o sistema persiste o registro, retorna HTTP 201 e o corpo contem o `id`
gerado, `veiculo_id`, `competencia` (exibida como MM/AAAA), `situacao` e
`registrado_em`.

### AC-002 — Competencia com formato invalido

Given um operador autenticado,
When envia uma string de competencia que nao segue o formato AAAA-MM (por
exemplo "05/2025", "05-2025" ou "texto"),
Then o sistema rejeita com HTTP 422 e mensagem indicando formato invalido de
competencia, sem gravar registro.

### AC-003 — Situacao invalida

Given um operador autenticado,
When envia um valor de situacao diferente de `baixado`, `aberto` ou `cancelado`,
Then o sistema rejeita com HTTP 422 e mensagem indicando situacao invalida,
sem gravar registro.

### AC-004 — Duplicidade de registro para o mesmo veiculo e competencia

Given a associacao A ja possui um registro de situacao para o veiculo V na
competencia 2025-05,
When um operador da associacao A tenta criar outro registro para o mesmo
veiculo V na mesma competencia 2025-05,
Then o sistema rejeita com HTTP 409 e mensagem indicando que ja existe registro
para esse veiculo nessa competencia.

### AC-005 — Atualizacao da situacao existente

Given existe um registro de situacao para o veiculo V na competencia 2025-05
com situacao `aberto`,
When o operador envia um PATCH alterando a situacao para `baixado`,
Then o sistema atualiza o registro, persiste o novo valor, retorna HTTP 200 com
os dados atualizados, e a auditoria registra o estado anterior e o novo estado.

### AC-006 — Veiculo nao encontrado ou de outra associacao

Given um operador da associacao A,
When envia `veiculo_id` pertencente a associacao B (ou inexistente),
Then o sistema rejeita com HTTP 404 (o veiculo nao e visivel pela RLS), sem
gravar registro.

### AC-007 — Veiculo sem status ativo nao pode receber situacao de boleto

Given um veiculo com status `pendente_vistoria` ou `inativo`,
When o operador tenta registrar situacao de boleto para esse veiculo,
Then o sistema rejeita com HTTP 422 e mensagem indicando que o veiculo precisa
ter status ativo para receber situacao de boleto.

### AC-008 — Consolidacao por segmento na competencia

Given a associacao A possui tres veiculos ativos: V1 (LEVES, cota 200,
situacao baixado), V2 (LEVES, cota 200, situacao aberto) e V3 (PESADOS,
cota 500, situacao baixado) na competencia 2025-05,
When o operador consulta a consolidacao da competencia 2025-05,
Then o response contem: LEVES com baixadas=200, abertas=200, canceladas=0;
PESADOS com baixadas=500, abertas=0, canceladas=0; MOTOS com baixadas=0,
abertas=0, canceladas=0. O denominador da BASE e a soma das cotas baixadas
(200 para LEVES, 500 para PESADOS); as demais situacoes sao informativas.

### AC-009 — Veiculo sem registro na competencia nao entra na consolidacao

Given o veiculo V4 (LEVES, cota 300) esta ativo mas nao tem registro de
situacao na competencia 2025-05,
When o app gera a consolidacao de 2025-05,
Then a cota de V4 nao aparece em nenhuma coluna (baixadas, abertas nem
canceladas) do segmento LEVES.

### AC-010 — Isolamento de tenant na listagem

Given a associacao A possui cinco registros de situacao e a associacao B
possui tres,
When um operador da associacao A lista os registros da competencia,
Then recebe exatamente os cinco registros da associacao A, sem nenhum dado
da associacao B.

### AC-011 — Importacao por arquivo simples

Given um operador autenticado envia um arquivo CSV com colunas `placa`,
`competencia` e `situacao`,
When o arquivo e valido (todas as linhas com placa reconhecida na associacao,
competencia no formato AAAA-MM e situacao valida),
Then o sistema cria ou atualiza os registros de situacao para cada linha e
retorna HTTP 200 com o resumo: total de linhas, criadas, atualizadas e
rejeitadas (com motivo por linha rejeitada).

### AC-012 — Importacao com linhas invalidas nao interrompe as validas

Given um arquivo CSV com dez linhas, sendo duas com situacao invalida e uma
com placa nao encontrada na associacao,
When o operador importa o arquivo,
Then o sistema processa as sete linhas validas normalmente, rejeita as tres
invalidas com motivo descrito no response e retorna HTTP 200 (nao HTTP 422),
sem reverter os registros validos ja gravados.

### AC-013 — Contribuicao para o arquivo BASE

Given os veiculos ativos da associacao A na competencia 2025-05 tem suas
situacoes de boleto registradas,
When o app exporta a BASE de 2025-05,
Then a coluna BAIXADO de cada segmento no arquivo reflete exatamente a soma
das cotas dos veiculos com status `ativo` e situacao `baixado` naquele segmento
(ADR-002 C1); veiculos com situacao `cancelado` nao entram na coluna BAIXADO nem
no invariante (ADR-002 C7); e `detectar_tipo` reconhece o arquivo como BASE.

---

## 4. Modelo de Dados

### 4.1 Tabela `situacoes_boleto`

Registro de situacao do boleto por veiculo e competencia.

```sql
create table situacoes_boleto (
  id              uuid primary key default gen_random_uuid(),
  associacao_id   uuid not null references associacoes(id) on delete restrict,
  veiculo_id      uuid not null references veiculos(id) on delete restrict,
  competencia     date not null,
    -- sempre o primeiro dia do mes; ex.: 2025-05-01
    -- a API aceita "AAAA-MM" e converte para date('AAAA-MM-01')
    -- check abaixo garante que nao ha dia diferente de 1
  situacao        text not null
                    check (situacao in ('baixado', 'aberto', 'cancelado')),
  registrado_em   timestamptz not null default now(),
  atualizado_em   timestamptz not null default now(),

  constraint situacoes_boleto_competencia_primeiro_dia
    check (extract(day from competencia) = 1),

  constraint situacoes_boleto_veiculo_competencia_unique
    unique (veiculo_id, competencia)
);
```

Indices:

```sql
-- busca de todos os registros de uma associacao em uma competencia
-- (usada na consolidacao e na geracao da BASE)
create index situacoes_boleto_associacao_competencia_idx
  on situacoes_boleto (associacao_id, competencia);

-- busca por veiculo (usada no detalhe do veiculo, SPEC-003 secao 6.3)
create index situacoes_boleto_veiculo_idx
  on situacoes_boleto (veiculo_id);
```

Notas:
- A constraint `situacoes_boleto_veiculo_competencia_unique` garante no banco
  a unicidade de um registro por veiculo por competencia, reforando o que o
  endpoint tambem verifica (AC-004).
- A coluna `associacao_id` e redundante em relacao ao `veiculo_id` (o veiculo
  ja carrega o tenant), mas e mantida para que a policy de RLS opere
  diretamente sobre a tabela usando o claim do JWT, sem join adicional (ADR-002
  C2).
- Nao ha coluna de valor monetario nesta tabela: a cota do veiculo e lida
  diretamente de `veiculos.cota` no momento da consolidacao. Isso evita
  dessincronia se a cota for atualizada.
- A competencia e armazenada como `date` (primeiro dia do mes). A conversao de
  "AAAA-MM" para date e feita na camada de API antes da persistencia. A exibicao
  na UI usa "MM/AAAA" (ADR-002 C3).

### 4.2 Tabela `situacoes_boleto_audit`

Trilha imutavel de cada operacao sobre `situacoes_boleto`, conforme RNF-02.

```sql
create table situacoes_boleto_audit (
  id              bigint generated always as identity primary key,
  situacao_boleto_id uuid not null,
  associacao_id   uuid not null,
  operador_id     uuid not null,   -- auth.uid() no momento da operacao
  operacao        text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes   jsonb,           -- null em INSERT
  payload_depois  jsonb,           -- null em DELETE
  ocorrido_em     timestamptz not null default now()
);
```

A trilha e preenchida por trigger na tabela `situacoes_boleto`. Nao ha endpoint
de escrita direta nessa tabela.

### 4.3 Politica RLS

```sql
-- habilitar RLS
alter table situacoes_boleto enable row level security;
alter table situacoes_boleto_audit enable row level security;

-- operadores so enxergam registros da propria associacao
-- claim 'associacao_id' presente no JWT (ADR-002 C2)
create policy situacoes_boleto_isolamento on situacoes_boleto
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- auditoria: leitura restrita a operadores da mesma associacao
create policy situacoes_boleto_audit_leitura on situacoes_boleto_audit
  for select
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- auditoria: sem escrita direta pelo app (apenas via trigger)
create policy situacoes_boleto_audit_sem_insert on situacoes_boleto_audit
  for insert
  with check (false);
```

### 4.4 Visao de consolidacao (nao persistida)

A consolidacao por segmento e calculada dinamicamente via query; nao e uma
tabela materializada. A query de referencia e:

```sql
-- :competencia deve ser passado como date (primeiro dia do mes, ex.: '2025-05-01')
select
  v.segmento,
  sb.situacao,
  sum(v.cota) as soma_cotas,
  count(*)    as qtd_veiculos
from situacoes_boleto sb
join veiculos v on v.id = sb.veiculo_id
where
  sb.associacao_id = (auth.jwt() ->> 'associacao_id')::uuid
  and sb.competencia = :competencia
  and v.status = 'ativo'
group by v.segmento, sb.situacao
order by v.segmento, sb.situacao;
```

O denominador da BASE e a soma de `soma_cotas` onde `situacao = 'baixado'` (ADR-002
C1 e C7). As situacoes `aberto` e `cancelado` sao incluidas na consolidacao apenas
como informativo; `cancelado` nao entra no denominador nem no invariante.

O resultado e transformado no backend no shape descrito na secao 5.2 antes de
ser enviado ao cliente ou usado na geracao do arquivo BASE.

---

## 5. API

Base de URL: `/api/situacoes-boleto`

Todas as rotas exigem sessao ativa. O `associacao_id` e lido do claim do JWT
(`auth.jwt() ->> 'associacao_id'`), conforme ADR-002 C2.

### 5.1 POST /api/situacoes-boleto

Cria um novo registro de situacao de boleto.

Request body:

```json
{
  "veiculo_id":  "uuid, obrigatorio",
  "competencia": "AAAA-MM, obrigatorio",
  "situacao":    "baixado | aberto | cancelado, obrigatorio"
}
```

Respostas:

| HTTP | Situacao |
|------|----------|
| 201  | Criado. Body: `{ id, veiculo_id, competencia, situacao, registrado_em }` |
| 401  | Nao autenticado. |
| 404  | `veiculo_id` nao encontrado na associacao do operador. |
| 409  | Ja existe registro para esse veiculo nessa competencia. |
| 422  | Competencia com formato invalido, situacao invalida, `veiculo_id` ausente, ou veiculo sem status `ativo`. |

### 5.2 GET /api/situacoes-boleto/consolidacao

Retorna a consolidacao de cotas por segmento e situacao para uma competencia.
Esse endpoint e o insumo direto da geracao do arquivo BASE.

Query params:

| Param        | Tipo   | Descricao |
|--------------|--------|-----------|
| `competencia`| string | AAAA-MM. Obrigatorio. |

Response 200:

```json
{
  "competencia": "05/2025",
  "segmentos": {
    "LEVES": {
      "baixado": { "soma_cotas": 1200.00, "qtd_veiculos": 6 },
      "aberto":  { "soma_cotas":  400.00, "qtd_veiculos": 2 },
      "cancelado": { "soma_cotas": 0.00, "qtd_veiculos": 0 }
    },
    "MOTOS": {
      "baixado": { "soma_cotas": 300.00, "qtd_veiculos": 3 },
      "aberto":  { "soma_cotas":   0.00, "qtd_veiculos": 0 },
      "cancelado": { "soma_cotas": 0.00, "qtd_veiculos": 0 }
    },
    "PESADOS": {
      "baixado": { "soma_cotas": 2000.00, "qtd_veiculos": 4 },
      "aberto":  { "soma_cotas":  500.00, "qtd_veiculos": 1 },
      "cancelado": { "soma_cotas": 0.00, "qtd_veiculos": 0 }
    }
  }
}
```

Segmentos sem nenhum registro aparecem com soma zero e quantidade zero (nao
sao omitidos), garantindo que o gerador da BASE sempre receba os tres
segmentos.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Consolidacao calculada dinamicamente. |
| 401  | Nao autenticado. |
| 422  | Competencia com formato invalido (nao AAAA-MM) ou ausente. |

### 5.3 GET /api/situacoes-boleto

Lista os registros de situacao da associacao do operador logado.

Query params opcionais:

| Param         | Tipo   | Descricao |
|---------------|--------|-----------|
| `competencia` | string | Filtra por AAAA-MM. |
| `veiculo_id`  | uuid   | Filtra por veiculo. |
| `situacao`    | string | Filtra por baixado, aberto ou cancelado. |
| `page`        | int    | Pagina (base 1). Padrao: 1. |
| `per_page`    | int    | Registros por pagina. Padrao: 50. Maximo: 200. |

Response 200:

```json
{
  "data": [
    {
      "id", "veiculo_id", "competencia", "situacao", "registrado_em", "atualizado_em"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 50
}
```

### 5.4 GET /api/situacoes-boleto/:id

Retorna um registro especifico pelo id.

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Dados do registro. Mesmo shape do item em GET /api/situacoes-boleto. |
| 401  | Nao autenticado. |
| 404  | Nao encontrado na associacao do operador. |

### 5.5 PATCH /api/situacoes-boleto/:id

Atualiza a situacao de um registro existente. Apenas o campo `situacao` e
editavel via PATCH.

Request body:

```json
{
  "situacao": "baixado | aberto | cancelado, obrigatorio"
}
```

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Atualizado. Body: dados atualizados no mesmo shape. |
| 401  | Nao autenticado. |
| 404  | Nao encontrado na associacao do operador. |
| 422  | Situacao invalida. |

### 5.6 POST /api/situacoes-boleto/importar

Importa registros de situacao a partir de um arquivo CSV.

Request: `multipart/form-data` com campo `arquivo` (arquivo CSV).

Formato do CSV:

```
placa,competencia,situacao
ABC1234,2025-05,baixado
XYZ9999,2025-05,aberto
```

Comportamento:
- Para cada linha valida, o sistema verifica se ja existe registro para o par
  (veiculo da placa, competencia): se nao existir, cria; se existir, atualiza.
- Linhas invalidas (placa nao encontrada, formato de competencia invalido,
  situacao invalida) sao rejeitadas individualmente; as demais sao processadas.
- O processamento nao e transacional por linha: linhas validas sao gravadas
  mesmo que outras sejam rejeitadas (ver AC-012).

Response 200:

```json
{
  "total": 10,
  "criadas": 7,
  "atualizadas": 1,
  "rejeitadas": 2,
  "erros": [
    { "linha": 4, "motivo": "placa nao encontrada na associacao: ZZZ0000" },
    { "linha": 8, "motivo": "situacao invalida: pago" }
  ]
}
```

Respostas:

| HTTP | Situacao |
|------|----------|
| 200  | Processamento concluido (parcial ou total). Body com resumo acima. |
| 400  | Arquivo ausente ou nao e CSV. |
| 401  | Nao autenticado. |
| 422  | CSV sem as colunas obrigatorias (`placa`, `competencia`, `situacao`). |

---

## 6. UI

### 6.1 Tela: lancamento em lote por competencia

Rota sugerida: `/competencias/:aaaa-mm/boletos`

Elementos:
- Cabecalho com o mes e ano da competencia em destaque.
- Tabela de veiculos ativos da associacao com colunas: Placa, Segmento, Cota,
  Situacao Atual (dropdown inline: baixado, aberto, cancelado, ou em branco se
  nao registrado ainda).
- Barra de resumo no topo ou rodape mostrando a consolidacao em tempo real
  (conforme o operador preenche as situacoes): cotas baixadas, abertas e
  canceladas por segmento.
- Botao "Salvar alteracoes" que envia as mudancas pendentes para o backend
  (POST ou PATCH conforme o caso).
- Botao "Importar CSV" que abre o dialogo de importacao (ver 6.2).

Comportamento:
- A tabela pre-carrega os registros existentes de situacao para a competencia
  selecionada. Veiculos sem registro aparecem com situacao em branco.
- Ao alterar um dropdown, o item e marcado como pendente (sem salvar
  imediatamente). O operador revisa e confirma com "Salvar alteracoes".
- A consolidacao exibida na barra de resumo e calculada localmente a partir
  dos valores visiveis na tabela (preview), sendo atualizada no servidor
  somente apos o salvar.
- Apos salvar, o app consulta GET /api/situacoes-boleto/consolidacao e
  atualiza a barra de resumo com os dados confirmados.

### 6.2 Dialogo: importacao de CSV

Aberto a partir do botao "Importar CSV" da tela 6.1.

Elementos:
- Campo de upload de arquivo (aceita apenas .csv).
- Botao "Enviar".
- Apos o processamento, exibe o resumo retornado pelo endpoint (total,
  criadas, atualizadas, rejeitadas).
- Erros de linha sao listados em uma tabela expandivel dentro do dialogo.
- Botao "Fechar" que recarrega a tabela principal com os dados atualizados.

### 6.3 Tela: detalhe do veiculo (leitura historica)

O historico de situacoes de boleto por competencia e exibido na tela de
detalhe do veiculo (SPEC-003, secao 6.3) como uma secao de leitura. Cada
linha mostra: competencia, situacao e data de registro. A edicao e feita
pela tela 6.1 ou pelo PATCH direto; a tela do veiculo e somente leitura
para esse historico.

---

## 7. Observabilidade

- Logar no nivel INFO cada criacao e atualizacao de situacao de boleto, com
  `situacao_boleto_id`, `associacao_id`, `veiculo_id` (sem placa em claro),
  `competencia` e `situacao`.
- Logar no nivel INFO cada importacao CSV concluida, com `associacao_id`,
  `competencia`, totais de criadas, atualizadas e rejeitadas.
- Logar no nivel WARN cada tentativa rejeitada por duplicidade (409) ou
  veiculo inativo (422), com `associacao_id` e o motivo.
- Logar no nivel WARN cada linha rejeitada durante a importacao CSV, com o
  numero da linha e o motivo.
- Metrica recomendada: percentual de veiculos ativos sem situacao registrada
  para a competencia corrente, por associacao. Esse indicador alerta o
  operador sobre lacunas antes da exportacao da BASE.

---

## 8. Seguranca e LGPD

- A tabela `situacoes_boleto` nao contem dados pessoais em si, mas permite
  inferir comportamento de pagamento do associado. Deve ser tratada como dado
  sensivel nos logs e na exportacao.
- A placa aparece no CSV de importacao e no arquivo BASE exportado; seu uso
  nessas operacoes deve ser documentado como finalidade legitima no mapeamento
  de dados da LGPD do produto.
- O isolamento por RLS garante que dados de uma associacao nao vazam para
  operadores de outra (RNF-01).
- A trilha de auditoria e imutavel: sem endpoint de DELETE ou UPDATE em
  `situacoes_boleto_audit`; a policy RLS bloqueia insercao direta pelo app
  (RNF-02).
- A comunicacao e exclusivamente por HTTPS (RNF-04).
- O endpoint de importacao CSV deve validar o tamanho maximo do arquivo (limite
  sugerido: 1 MB no MVP) para prevenir abuso de recursos.

---

## 9. Testes

### 9.1 Testes unitarios (validacao e consolidacao)

Validacao de competencia:
- Formato AAAA-MM valido: ao menos tres exemplos (2025-01, 2030-12, 2026-05).
- Formato invalido: "05/2025", "5/2025", "2025-13", "2025-00", "texto", string
  vazia. Todos devem ser rejeitados.

Validacao de situacao:
- Valores validos: `baixado`, `aberto`, `cancelado` (exatos, minusculas).
- Valores invalidos: `Baixado`, `pago`, `pendente`, string vazia.

Calculo de consolidacao (funcao pura, sem banco):
- Tres veiculos LEVES (dois baixados, um aberto): resultado confere com a soma
  das cotas individuais nas colunas corretas; denominador e a soma das cotas
  baixadas apenas.
- Veiculo PESADOS cancelado: aparece apenas na coluna cancelado de PESADOS; nao
  altera o denominador da BASE nem entra no invariante (ADR-002 C7).
- Nenhum veiculo MOTOS: MOTOS aparece com zeros em todos os campos.
- Veiculo ativo sem registro na competencia: nao entra em nenhuma coluna.

### 9.2 Testes de integracao (API)

- POST com dados validos (competencia no formato AAAA-MM) retorna 201 e payload
  com os campos obrigatorios; competencia no response exibida como MM/AAAA.
- POST com competencia no formato MM/AAAA (formato invalido para API) retorna 422.
- POST com situacao invalida retorna 422.
- POST com `veiculo_id` de outra associacao retorna 404.
- POST com `veiculo_id` de veiculo `pendente_vistoria` retorna 422.
- POST duplicado (mesmo veiculo e competencia) retorna 409.
- PATCH com nova situacao valida retorna 200 e persiste o novo valor.
- PATCH com situacao invalida retorna 422.
- GET /api/situacoes-boleto retorna somente registros da associacao do operador
  (RLS via claim JWT).
- GET /api/situacoes-boleto/:id de outra associacao retorna 404.
- GET /api/situacoes-boleto/consolidacao retorna os tres segmentos (com zeros
  nos segmentos sem registro); a soma das cotas canceladas nao integra o
  denominador da BASE.
- POST /api/situacoes-boleto/importar com CSV valido (competencia AAAA-MM)
  cria os registros e retorna resumo correto.
- POST /api/situacoes-boleto/importar com linhas parcialmente invalidas
  processa as validas e lista os erros das invalidas no resumo.
- POST /api/situacoes-boleto/importar com arquivo nao CSV retorna 400.

### 9.3 Ligacao com o oraculo do motor aprovado

A situacao de boleto registrada nesta spec e o insumo direto do denominador
da BASE. O link com o oraculo segue a cadeia abaixo, que e o teste de aceite
de ponta a ponta (harness de reconciliacao descrito na SPEC-000, secao 6):

1. Configurar associacao de teste com veiculos ativos de segmentos e cotas
   conhecidos (fixture derivada da SPEC-003).
2. Registrar situacoes de boleto para cada veiculo na competencia de teste
   (no formato AAAA-MM), incluindo ao menos um baixado, um aberto e um
   cancelado por segmento.
3. Chamar GET /api/situacoes-boleto/consolidacao e verificar que as somas de
   cotas baixadas por segmento conferem com os valores esperados da fixture.
4. Exportar a BASE da competencia de teste e verificar:
   a. `detectar_tipo` retorna `BASE` para o arquivo.
   b. A coluna BAIXADO de cada segmento no arquivo confere com
      `consolidacao.segmentos[X].baixado.soma_cotas` (somente veiculos com
      status `ativo` e situacao `baixado`, conforme ADR-002 C1).
   c. As colunas ABERTO e CANCELADO tambem conferem com a consolidacao;
      CANCELADO e informativo e nao entra no denominador (ADR-002 C7).
5. Exportar o RATEIO (SPEC-006) e rodar o motor aprovado sobre BASE e RATEIO
   com `tools/reconciliar.py`; confirmar invariante de fechamento igual a zero.

O passo 4b e o teste central desta spec: se a coluna BAIXADO do arquivo BASE
nao refletir exatamente a soma das cotas baixadas, o aceite falha,
independente de os demais passos passarem.

---

## 10. Rollout

1. Aplicar a migration de banco (`situacoes_boleto`, `situacoes_boleto_audit`,
   constraints, indices, RLS, trigger de auditoria) em ambiente de
   desenvolvimento. A migration depende de `veiculos` (SPEC-003) estar
   aplicada.
2. Inserir fixtures de teste: associacao com veiculos ativos de segmentos
   distintos e situacoes de boleto conhecidas para pelo menos uma competencia.
3. Rodar os testes unitarios de validacao de competencia, situacao e
   consolidacao.
4. Rodar os testes de integracao da API.
5. Revisar a policy RLS com um segundo operador de tenant diferente (teste
   manual de isolamento).
6. Validar o endpoint de consolidacao contra a fixture: conferir que as somas
   batem com os valores esperados.
7. Integrar com o gerador de BASE (SPEC-006) e rodar o harness de
   reconciliacao descrito na secao 9.3.
8. Aprovar a spec com o Tech Lead e o Spec Lead antes de prosseguir para
   implementacao do frontend.
9. Apos o frontend concluir a tela de lancamento em lote e o dialogo de
   importacao, realizar o aceite funcional manual com base nos criterios da
   secao 3.

---

## 11. Questoes em aberto

- Competencia retroativa: definir se o operador pode registrar ou alterar
  situacoes de boleto em competencias passadas apos a exportacao da BASE daquele
  mes ja ter ocorrido. Se sim, o arquivo BASE exportado pode ficar desatualizado
  em relacao ao banco. Uma opcao e bloquear alteracoes em competencias ja
  exportadas; outra e registrar o evento de exportacao e exibir um aviso de
  dessincronismo.
- Delecao de registro: no MVP, o endpoint DELETE nao e previsto. Se um registro
  de situacao for criado por engano, o operador deve usar o PATCH para corrigir
  a situacao. Avaliar se a delecao e necessaria antes da implementacao.
- Granularidade do CSV de importacao: o formato atual aceita uma linha por
  veiculo por competencia. Se o operador precisar importar multiplas competencias
  em um unico arquivo, o formato e a logica de processamento precisam ser
  revistos.
- Situacao de boleto para veiculos inativados apos o registro: se um veiculo
  passa para `inativo` apos ter um registro de situacao em uma competencia em
  aberto, definir se o registro existente permanece valido para efeito da BASE
  daquela competencia ou e ignorado retroativamente.
- Numero de boleto ou referencia de pagamento: o MVP nao armazena identificador
  do boleto emitido (numero, linha digitavel), apenas a situacao. Avaliar se
  algum requisito regulatorio (LC 213 ou SUSEP) exige o registro do identificador
  para fins de auditoria.
