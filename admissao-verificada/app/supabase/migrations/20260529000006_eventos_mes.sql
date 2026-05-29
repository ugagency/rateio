-- Migration 0006 — eventos do mês / numerador do RATEIO (SPEC-006)

create table public.eventos_mes (
  id                uuid primary key default gen_random_uuid(),
  associacao_id     uuid not null references public.associacoes(id) on delete restrict,
  competencia       date not null,           -- primeiro dia do mês (ADR-002 C3)
  marcador_secao    text not null check (marcador_secao in (
                      'LEVES ASSOCIADOS', 'LEVES TERCEIROS',
                      'MOTOS ASSOCIADOS', 'MOTOS TERCEIROS',
                      'PESADOS ASSOCIADOS', 'PESADOS TERCEIROS')),
  tipo              text not null check (tipo in ('INTEGRAL', 'PARCIAL')),
  protocolo         text not null,
  motivo            text,
  placa             text not null,
  data_comunicacao  date not null,
  valor_rateado     numeric(14,2) not null check (valor_rateado > 0),
  status            text not null default 'ativo' check (status in ('ativo', 'cancelado')),
  criado_em         timestamptz not null default now(),
  atualizado_em     timestamptz not null default now(),
  constraint eventos_mes_protocolo_competencia_unique
    unique (associacao_id, competencia, protocolo),
  constraint eventos_mes_competencia_primeiro_dia
    check (extract(day from competencia) = 1)
);

create index eventos_mes_associacao_competencia_idx
  on public.eventos_mes (associacao_id, competencia) where status = 'ativo';
create index eventos_mes_associacao_placa_idx
  on public.eventos_mes (associacao_id, placa);
create index eventos_mes_associacao_protocolo_idx
  on public.eventos_mes (associacao_id, protocolo);

create trigger eventos_mes_set_updated_at
  before update on public.eventos_mes
  for each row execute function public.set_updated_at();

-- Auditoria (RNF-02)
create table public.eventos_mes_audit (
  id              bigint generated always as identity primary key,
  evento_id       uuid not null,
  associacao_id   uuid not null,
  operador_id     uuid,
  operacao        text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes   jsonb,
  payload_depois  jsonb,
  ocorrido_em     timestamptz not null default now()
);

create trigger eventos_mes_audit_trg
  after insert or update or delete on public.eventos_mes
  for each row execute function public.fn_audit('eventos_mes_audit', 'evento_id');

-- RLS (ADR-002 C2)
alter table public.eventos_mes enable row level security;
alter table public.eventos_mes_audit enable row level security;

create policy eventos_mes_isolamento on public.eventos_mes
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid)
  with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy eventos_mes_audit_leitura on public.eventos_mes_audit
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy eventos_mes_audit_sem_insert on public.eventos_mes_audit
  for insert with check (false);
