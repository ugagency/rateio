-- Migration 0008 — hardening de segurança (advisor Supabase)
-- Corrige os avisos do database linter após as migrations 0001-0007:
--   0011 function_search_path_mutable  (set_updated_at, fn_audit, custom_jwt_claims)
--   0028/0029 SECURITY DEFINER chamável via RPC por anon/authenticated
--              (fn_audit, custom_jwt_claims)
-- Convenções: ADR-002 (C2 RLS por claim associacao_id no JWT).

-- ---------- search_path fixo (anti-hijack em SECURITY DEFINER) ----------
-- As três funções só referenciam objetos qualificados (public.*, auth.*) ou
-- do pg_catalog (now(), jsonb_*, casts), então search_path vazio é seguro.

alter function public.set_updated_at() set search_path = '';
alter function public.custom_jwt_claims(jsonb) set search_path = '';

-- fn_audit usa SQL dinâmico com o nome da tabela de auditoria sem schema;
-- com search_path vazio o %I não resolveria, então qualificamos em public.%I.
create or replace function public.fn_audit()
returns trigger language plpgsql security definer set search_path = '' as $$
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
    'insert into public.%I (%I, associacao_id, operador_id, operacao, payload_antes, payload_depois)
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

-- ---------- Remover exposição via PostgREST RPC ----------
-- fn_audit roda apenas como trigger (o gatilho não checa EXECUTE do papel).
-- custom_jwt_claims roda apenas como auth hook (papel supabase_auth_admin).
revoke execute on function public.fn_audit() from anon, authenticated, public;
revoke execute on function public.custom_jwt_claims(jsonb) from anon, authenticated, public;

-- O auth hook precisa ser executável pelo papel do GoTrue.
grant execute on function public.custom_jwt_claims(jsonb) to supabase_auth_admin;
