-- Migration 0003 — faixas de cota, veículos e auditoria (SPEC-003)

-- ---------- faixas_cota (parâmetro de cálculo da cota por FIPE) ----------
-- Seed de referência (ADR-002 C5) reproduz cotas_por_fipe de rules.py.
-- Preenchida por seed/serviço; sem escrita pelo operador no MVP.
create table public.faixas_cota (
  id             uuid primary key default gen_random_uuid(),
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  fipe_ate       numeric(12,2),            -- null = intervalo aberto superior (cota especial)
  cota_valor     numeric(10,2) not null check (cota_valor > 0),
  vigente_desde  date not null,
  criado_em      timestamptz not null default now()
);

create index faixas_cota_associacao_idx
  on public.faixas_cota (associacao_id, vigente_desde, fipe_ate);

alter table public.faixas_cota enable row level security;
create policy faixas_cota_isolamento on public.faixas_cota
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

-- ---------- veiculos ----------
create table public.veiculos (
  id                   uuid primary key default gen_random_uuid(),
  associacao_id        uuid not null references public.associacoes(id) on delete restrict,
  associado_id         uuid not null references public.associados(id) on delete restrict,
  placa                text not null,       -- normalizada: sem hífen, maiúsculas
  segmento             text not null check (segmento in ('LEVES', 'MOTOS', 'PESADOS')),
  fipe_valor           numeric(12,2) not null check (fipe_valor > 0),
  cobertura_terceiros  text not null default 'nenhuma'
                         check (cobertura_terceiros in ('nenhuma', '50k', '100k')),
  cota                 numeric(10,2) not null check (cota > 0),
  status               text not null default 'pendente_vistoria'
                         check (status in ('pendente_vistoria', 'ativo', 'inativo')),
  criado_em            timestamptz not null default now(),
  atualizado_em        timestamptz not null default now(),
  constraint veiculos_placa_associacao_unique unique (associacao_id, placa)
);

create index veiculos_associacao_placa_idx on public.veiculos (associacao_id, placa);
create index veiculos_associado_idx on public.veiculos (associado_id);
-- usado na geração da BASE (denominador = ativos)
create index veiculos_associacao_segmento_idx
  on public.veiculos (associacao_id, segmento) where status = 'ativo';

create trigger veiculos_set_updated_at
  before update on public.veiculos
  for each row execute function public.set_updated_at();

-- Auditoria (RNF-02)
create table public.veiculos_audit (
  id              bigint generated always as identity primary key,
  veiculo_id      uuid not null,
  associacao_id   uuid not null,
  operador_id     uuid,
  operacao        text not null check (operacao in ('INSERT', 'UPDATE', 'DELETE')),
  payload_antes   jsonb,
  payload_depois  jsonb,
  ocorrido_em     timestamptz not null default now()
);

create trigger veiculos_audit_trg
  after insert or update or delete on public.veiculos
  for each row execute function public.fn_audit('veiculos_audit', 'veiculo_id');

-- RLS (ADR-002 C2)
alter table public.veiculos enable row level security;
alter table public.veiculos_audit enable row level security;

create policy veiculos_isolamento on public.veiculos
  using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid)
  with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy veiculos_audit_leitura on public.veiculos_audit
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

create policy veiculos_audit_sem_insert on public.veiculos_audit
  for insert with check (false);
