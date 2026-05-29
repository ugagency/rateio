-- Migration 0009 — claim associacao_id via app_metadata (revisão do ADR-002 C2)
-- Contexto: o claim de topo associacao_id dependia de um auth hook
-- (custom_access_token) que só é habilitável no painel do Supabase. Para
-- tornar o provisionamento 100% reproduzível por migração/SQL (sem passo
-- manual no dashboard), passamos a derivar a associação do operador a partir
-- do app_metadata do usuário, que o GoTrue já embute no JWT nativamente.
--
-- Compatibilidade: jwt_associacao_id() lê primeiro de app_metadata e cai para
-- o claim de topo (auth.jwt() ->> 'associacao_id'). Assim, se o hook
-- custom_jwt_claims vier a ser habilitado no futuro, tudo continua válido.

-- ---------- Helper: associação corrente a partir do JWT ----------
create or replace function public.jwt_associacao_id()
returns uuid language sql stable
set search_path = ''
as $$
  select coalesce(
    nullif(auth.jwt() -> 'app_metadata' ->> 'associacao_id', ''),
    nullif(auth.jwt() ->> 'associacao_id', '')
  )::uuid;
$$;

-- ---------- Sincroniza associacao_id no app_metadata do operador ----------
-- Assume o papel que o hook tinha: ao provisionar/alterar um operador, grava
-- associacao_id no raw_app_meta_data do usuário. Vale para o próximo token.
create or replace function public.sync_operador_app_metadata()
returns trigger language plpgsql security definer
set search_path = ''
as $$
begin
  update auth.users
     set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb)
         || jsonb_build_object('associacao_id', new.associacao_id::text)
   where id = new.id;
  return new;
end;
$$;

drop trigger if exists operadores_sync_app_metadata on public.operadores;
create trigger operadores_sync_app_metadata
  after insert or update of associacao_id on public.operadores
  for each row execute function public.sync_operador_app_metadata();

-- Hardening (espelha o commit 0008): função definer não deve ser chamável
-- via RPC por anon/authenticated; só roda pela trigger (como dono da tabela).
revoke execute on function public.sync_operador_app_metadata() from public, anon, authenticated;

-- Backfill dos operadores já existentes.
update auth.users u
   set raw_app_meta_data = coalesce(u.raw_app_meta_data, '{}'::jsonb)
       || jsonb_build_object('associacao_id', o.associacao_id::text)
  from public.operadores o
 where o.id = u.id;

-- ---------- Repontar as policies para o helper ----------
-- migration 0001
alter policy associacoes_select on public.associacoes
  using (id = public.jwt_associacao_id());
alter policy operadores_select on public.operadores
  using (associacao_id = public.jwt_associacao_id());

-- migration 0002
alter policy associados_isolamento on public.associados
  using (associacao_id = public.jwt_associacao_id())
  with check (associacao_id = public.jwt_associacao_id());
alter policy associados_audit_leitura on public.associados_audit
  using (associacao_id = public.jwt_associacao_id());

-- migration 0003
alter policy faixas_cota_isolamento on public.faixas_cota
  using (associacao_id = public.jwt_associacao_id());
alter policy veiculos_isolamento on public.veiculos
  using (associacao_id = public.jwt_associacao_id())
  with check (associacao_id = public.jwt_associacao_id());
alter policy veiculos_audit_leitura on public.veiculos_audit
  using (associacao_id = public.jwt_associacao_id());

-- migration 0004
alter policy scripts_vistoria_select on public.scripts_vistoria
  using (associacao_id = public.jwt_associacao_id());
alter policy scripts_vistoria_insert on public.scripts_vistoria
  with check (associacao_id = public.jwt_associacao_id());
alter policy scripts_vistoria_update on public.scripts_vistoria
  using (associacao_id = public.jwt_associacao_id())
  with check (associacao_id = public.jwt_associacao_id());
alter policy etapas_script_select on public.etapas_script
  using (exists (
    select 1 from public.scripts_vistoria s
    where s.id = script_id
      and s.associacao_id = public.jwt_associacao_id()));
alter policy vistorias_select on public.vistorias
  using (associacao_id = public.jwt_associacao_id());
alter policy vistorias_insert on public.vistorias
  with check (associacao_id = public.jwt_associacao_id());
alter policy capturas_vistoria_select on public.capturas_vistoria
  using (associacao_id = public.jwt_associacao_id());
alter policy timeline_vistoria_select on public.timeline_vistoria
  using (associacao_id = public.jwt_associacao_id());

-- migration 0005
alter policy situacoes_boleto_isolamento on public.situacoes_boleto
  using (associacao_id = public.jwt_associacao_id())
  with check (associacao_id = public.jwt_associacao_id());
alter policy situacoes_boleto_audit_leitura on public.situacoes_boleto_audit
  using (associacao_id = public.jwt_associacao_id());

-- migration 0006
alter policy eventos_mes_isolamento on public.eventos_mes
  using (associacao_id = public.jwt_associacao_id())
  with check (associacao_id = public.jwt_associacao_id());
alter policy eventos_mes_audit_leitura on public.eventos_mes_audit
  using (associacao_id = public.jwt_associacao_id());

-- migration 0007
alter policy exportacoes_isolamento on public.exportacoes
  using (associacao_id = public.jwt_associacao_id())
  with check (associacao_id = public.jwt_associacao_id());
