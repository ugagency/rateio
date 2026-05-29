-- Migration 0004 — admissão verificada / vistoria (SPEC-004)

-- ---------- scripts_vistoria (roteiros versionados) ----------
create table public.scripts_vistoria (
  id             uuid primary key default gen_random_uuid(),
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  tipo           text not null check (tipo in ('carro', 'moto', 'reboque', 'revistoria')),
  descricao      text,
  tempo_max_min  integer not null check (tempo_max_min > 0),
  status         text not null default 'ativo' check (status in ('ativo', 'inativo')),
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now()
);

create trigger scripts_vistoria_set_updated_at
  before update on public.scripts_vistoria
  for each row execute function public.set_updated_at();

-- ---------- etapas_script ----------
create table public.etapas_script (
  id                   uuid primary key default gen_random_uuid(),
  script_id            uuid not null references public.scripts_vistoria(id) on delete restrict,
  sequencia            integer not null check (sequencia >= 1),
  tipo_etapa           text not null check (tipo_etapa in (
                         'selfie', 'documento', 'frente', 'traseira',
                         'lateral_esquerda', 'lateral_direita', 'teto',
                         'placa', 'chassi', 'outro')),
  camera_preferencial  text not null default 'traseira'
                         check (camera_preferencial in ('frontal', 'traseira')),
  obrigatoria          boolean not null default true,
  instrucao_texto      text,
  unique (script_id, sequencia)
);

-- ---------- vistorias ----------
create table public.vistorias (
  id             uuid primary key default gen_random_uuid(),
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  veiculo_id     uuid not null references public.veiculos(id) on delete restrict,
  script_id      uuid not null references public.scripts_vistoria(id) on delete restrict,
  operador_id    uuid not null references public.operadores(id) on delete restrict,
  status         text not null default 'a_realizar'
                   check (status in ('a_realizar', 'finalizada', 'expirada')),
  iniciado_em    timestamptz not null default now(),
  finalizado_em  timestamptz,
  expirado_em    timestamptz,
  token_sessao   uuid not null default gen_random_uuid(),
  criado_em      timestamptz not null default now()
);

-- no máximo uma vistoria em andamento por veículo
create unique index vistorias_veiculo_em_andamento
  on public.vistorias (veiculo_id) where status = 'a_realizar';

-- ---------- capturas_vistoria (imutável após criação) ----------
create table public.capturas_vistoria (
  id              uuid primary key default gen_random_uuid(),
  vistoria_id     uuid not null references public.vistorias(id) on delete restrict,
  etapa_id        uuid not null references public.etapas_script(id) on delete restrict,
  associacao_id   uuid not null references public.associacoes(id) on delete restrict,
  storage_path    text not null,
  capturado_em    timestamptz not null,   -- timestamp do dispositivo
  recebido_em     timestamptz not null default now(),
  latitude        numeric(10,7),
  longitude       numeric(10,7),
  substituida_por uuid references public.capturas_vistoria(id),
  refacao_de      uuid references public.capturas_vistoria(id),
  unico_uso       boolean not null default false
);

-- ---------- timeline_vistoria (trilha antifraude) ----------
create table public.timeline_vistoria (
  id             bigint generated always as identity primary key,
  vistoria_id    uuid not null references public.vistorias(id) on delete restrict,
  associacao_id  uuid not null references public.associacoes(id) on delete restrict,
  evento         text not null check (evento in (
                   'inicio', 'captura', 'refacao', 'expiracao',
                   'finalizacao', 'tentativa_galeria')),
  etapa_id       uuid references public.etapas_script(id),
  captura_id     uuid references public.capturas_vistoria(id),
  ocorrido_em    timestamptz not null default now(),
  metadados      jsonb
);

-- ---------- RLS (ADR-002 C2) ----------
alter table public.scripts_vistoria enable row level security;
create policy scripts_vistoria_select on public.scripts_vistoria
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
create policy scripts_vistoria_insert on public.scripts_vistoria
  for insert with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
create policy scripts_vistoria_update on public.scripts_vistoria
  for update using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid)
  with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);

alter table public.etapas_script enable row level security;
create policy etapas_script_select on public.etapas_script
  for select using (exists (
    select 1 from public.scripts_vistoria s
    where s.id = script_id
      and s.associacao_id = (auth.jwt() ->> 'associacao_id')::uuid));

alter table public.vistorias enable row level security;
create policy vistorias_select on public.vistorias
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
create policy vistorias_insert on public.vistorias
  for insert with check (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
-- UPDATE (finalização, expiração) somente por service_role.

alter table public.capturas_vistoria enable row level security;
create policy capturas_vistoria_select on public.capturas_vistoria
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
-- INSERT/UPDATE/DELETE somente por service_role (upload e refação).

alter table public.timeline_vistoria enable row level security;
create policy timeline_vistoria_select on public.timeline_vistoria
  for select using (associacao_id = (auth.jwt() ->> 'associacao_id')::uuid);
-- escrita somente por service_role.

-- Bucket de Storage 'vistorias' (privado) é criado fora desta migration,
-- na configuração de Storage do Supabase. Path:
-- vistorias/{associacao_id}/{vistoria_id}/{etapa_id}/{captura_id}.jpg
