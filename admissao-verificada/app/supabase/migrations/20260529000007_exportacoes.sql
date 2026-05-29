-- Migration 0007 — trilha de exportações (SPEC-007)

create table public.exportacoes (
  id             uuid primary key default gen_random_uuid(),
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  competencia    date not null,            -- primeiro dia do mês (ADR-002 C3)
  tipo           text not null check (tipo in ('BASE', 'RATEIO')),
  arquivo        text not null,            -- caminho/identificador do arquivo gerado
  hash           text,                     -- hash do conteúdo, para conferência
  criado_por     uuid references public.operadores(id),
  criado_em      timestamptz not null default now(),
  constraint exportacoes_competencia_primeiro_dia
    check (extract(day from competencia) = 1)
);

create index exportacoes_associacao_competencia_idx
  on public.exportacoes (associacao_id, competencia, tipo);

alter table public.exportacoes enable row level security;
create policy exportacoes_isolamento on public.exportacoes
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid)
  with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
