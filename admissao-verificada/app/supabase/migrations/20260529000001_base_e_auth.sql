-- Migration 0001 — base, autenticação e funções compartilhadas
-- SPEC-001 (associacoes, operadores, claim JWT) + helpers de updated_at e auditoria.
-- Convenções: ADR-002 (C2 RLS por claim associacao_id no JWT).

-- gen_random_uuid() é nativo no Postgres 13+ (pgcrypto não é necessário).

-- ---------- Funções compartilhadas ----------

-- Mantém atualizado_em em UPDATE.
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.atualizado_em := now();
  return new;
end;
$$;

-- Trilha de auditoria genérica (RNF-02). Parâmetros via TG_ARGV:
--   TG_ARGV[0] = nome da tabela de auditoria
--   TG_ARGV[1] = nome da coluna de id da entidade na tabela de auditoria
-- security definer: insere na tabela de auditoria contornando a RLS
-- (que bloqueia INSERT direto pelo app); operador_id vem de auth.uid().
create or replace function public.fn_audit()
returns trigger language plpgsql security definer as $$
declare
  v_assoc uuid;
  v_id uuid;
begin
  if (tg_op = 'DELETE') then
    v_assoc := old.associacao_id; v_id := old.id;
  else
    v_assoc := new.associacao_id; v_id := new.id;
  end if;
  execute format(
    'insert into %I (%I, associacao_id, operador_id, operacao, payload_antes, payload_depois)
       values ($1, $2, $3, $4, $5, $6)',
    tg_argv[0], tg_argv[1]
  )
  using
    v_id,
    v_assoc,
    auth.uid(),
    tg_op,
    case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) else null end,
    case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) else null end;
  if (tg_op = 'DELETE') then return old; else return new; end if;
end;
$$;

-- ---------- associacoes (tenant) ----------

create table public.associacoes (
  id         uuid primary key default gen_random_uuid(),
  nome       text not null,
  slug       text not null unique,
  criado_em  timestamptz not null default now()
);

-- SPEC-001 dispensa RLS aqui; habilitamos com leitura restrita ao próprio
-- tenant para não expor nomes de associações entre tenants pela API.
alter table public.associacoes enable row level security;
create policy associacoes_select on public.associacoes
  for select using (id = (auth.jwt() ->> 'associacao_id')::uuid);

-- ---------- operadores ----------

create table public.operadores (
  id             uuid primary key references auth.users(id) on delete cascade,
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  nome_exibicao  text not null,
  ativo          boolean not null default true,
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now()
);

create index operadores_associacao_idx on public.operadores (associacao_id);

create trigger operadores_set_updated_at
  before update on public.operadores
  for each row execute function public.set_updated_at();

alter table public.operadores enable row level security;

-- Operador enxerga os operadores da própria associação (claim do JWT).
create policy operadores_select on public.operadores
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
-- INSERT/UPDATE somente por service_role (provisionamento administrativo);
-- sem policy para authenticated.

-- ---------- Claim personalizado associacao_id no JWT (ADR-002 C2) ----------
-- Hook de custom access token. Deve ser habilitado nas configurações de Auth
-- do Supabase (auth hook do tipo custom_access_token apontando para esta
-- função). Roda como definer ao gerar o token, então lê operadores sem RLS.
create or replace function public.custom_jwt_claims(event jsonb)
returns jsonb language plpgsql stable security definer as $$
declare
  _assoc uuid;
  _claims jsonb;
begin
  select associacao_id into _assoc
    from public.operadores
   where id = (event->>'user_id')::uuid;

  _claims := coalesce(event->'claims', '{}'::jsonb);
  if _assoc is not null then
    _claims := jsonb_set(_claims, '{associacao_id}', to_jsonb(_assoc::text));
  end if;
  return jsonb_set(event, '{claims}', _claims);
end;
$$;
