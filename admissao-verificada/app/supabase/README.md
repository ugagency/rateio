# Banco de dados (Supabase) — MVP Admissão Verificada

Migrations do modelo de dados do M2, conforme SPEC-001 a 007 e ADR-002.
Validadas em Postgres 16 (aplicam em ordem; constraints, triggers de auditoria
e consolidação testados).

## Migrations

| Arquivo | Conteúdo |
|---|---|
| 0001 base_e_auth | associacoes, operadores, claim JWT, helpers (updated_at, auditoria) |
| 0002 associados | associados + auditoria |
| 0003 veiculos_cota | faixas_cota, veiculos + auditoria |
| 0004 vistorias | scripts_vistoria, etapas_script, vistorias, capturas, timeline |
| 0005 situacoes_boleto | situação por competência + auditoria (denominador da BASE) |
| 0006 eventos_mes | eventos do mês + auditoria (numerador do RATEIO) |
| 0007 exportacoes | trilha de exportações |

`seed.sql` (dev): uma associação demo, as faixas de cota espelhando o motor
(`rules.py`), e um script de vistoria de exemplo.

## Pré-requisito de produção: hook de claim no JWT

A RLS (ADR-002 C2) depende do claim `associacao_id` no JWT. A função
`public.custom_jwt_claims(event jsonb)` (migration 0001) deve ser registrada
como auth hook do tipo custom access token nas configurações de Auth do
Supabase. Sem o hook, as policies não enxergam o tenant e as consultas do app
retornam vazio.

## Storage

Criar o bucket privado `vistorias` (sem acesso público) nas configurações de
Storage. Path das capturas:
`vistorias/{associacao_id}/{vistoria_id}/{etapa_id}/{captura_id}.jpg`.

## Aplicar

Local (Supabase CLI): `supabase db reset` aplica migrations e `seed.sql`.
Remoto: `supabase db push` (sem o seed). As migrations ainda não foram
aplicadas a nenhum projeto remoto.

## Validação offline

As migrations foram conferidas num Postgres efêmero com stubs de `auth`
(schema `auth`, `auth.users`, `auth.uid()`, `auth.jwt()`): aplicam sem erro,
o seed gera 46 faixas, e a cadeia associado, veículo, situação e evento insere
com os triggers de auditoria disparando.
