-- Migration 0002 — associados (SPEC-002)

create table public.associados (
  id             uuid primary key default gen_random_uuid(),
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  nome           text not null check (char_length(trim(nome)) > 0),
  cpf            char(11) not null,          -- apenas dígitos, sem máscara
  email          text,
  telefone       text,
  status         text not null default 'ativo'
                   check (status in ('ativo', 'inativo')),
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),
  constraint associados_cpf_associacao_unique unique (associacao_id, cpf)
);

create index associados_associacao_cpf_idx on public.associados (associacao_id, cpf);

create trigger associados_set_updated_at
  before update on public.associados
  for each row execute function public.set_updated_at();

-- Auditoria (RNF-02)
create table public.associados_audit (
  id              bigint generated always as identity primary key,
  associado_id    uuid not null,
  associacao_id   uuid not null,
  operador_id     uuid,
  operacao        text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes   jsonb,
  payload_depois  jsonb,
  ocorrido_em     timestamptz not null default now()
);

create trigger associados_audit_trg
  after insert or update or delete on public.associados
  for each row execute function public.fn_audit('associados_audit', 'associado_id');

-- RLS (ADR-002 C2)
alter table public.associados enable row level security;
alter table public.associados_audit enable row level security;

create policy associados_isolamento on public.associados
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid)
  with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy associados_audit_leitura on public.associados_audit
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy associados_audit_sem_insert on public.associados_audit
  for insert with check (false);
