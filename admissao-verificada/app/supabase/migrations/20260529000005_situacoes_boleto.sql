-- Migration 0005 — situação de boleto por competência (SPEC-005)
-- Denominador da BASE: status do veículo = ativo E situação = baixado (ADR-002 C1/C7).

create table public.situacoes_boleto (
  id             uuid primary key default gen_random_uuid(),
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  veiculo_id     uuid not null references public.veiculos(id) on delete restrict,
  competencia    date not null,            -- sempre o primeiro dia do mês (ADR-002 C3)
  situacao       text not null check (situacao in ('baixado', 'aberto', 'cancelado')),
  registrado_em  timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),
  constraint situacoes_boleto_competencia_primeiro_dia
    check (extract(day from competencia) = 1),
  constraint situacoes_boleto_veiculo_competencia_unique
    unique (veiculo_id, competencia)
);

create index situacoes_boleto_associacao_competencia_idx
  on public.situacoes_boleto (associacao_id, competencia);
create index situacoes_boleto_veiculo_idx
  on public.situacoes_boleto (veiculo_id);

create trigger situacoes_boleto_set_updated_at
  before update on public.situacoes_boleto
  for each row execute function public.set_updated_at();

-- Auditoria (RNF-02)
create table public.situacoes_boleto_audit (
  id                  bigint generated always as identity primary key,
  situacao_boleto_id  uuid not null,
  associacao_id       uuid not null,
  operador_id         uuid,
  operacao            text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes       jsonb,
  payload_depois      jsonb,
  ocorrido_em         timestamptz not null default now()
);

create trigger situacoes_boleto_audit_trg
  after insert or update or delete on public.situacoes_boleto
  for each row execute function public.fn_audit('situacoes_boleto_audit', 'situacao_boleto_id');

-- RLS (ADR-002 C2)
alter table public.situacoes_boleto enable row level security;
alter table public.situacoes_boleto_audit enable row level security;

create policy situacoes_boleto_isolamento on public.situacoes_boleto
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid)
  with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy situacoes_boleto_audit_leitura on public.situacoes_boleto_audit
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy situacoes_boleto_audit_sem_insert on public.situacoes_boleto_audit
  for insert with check (false);
