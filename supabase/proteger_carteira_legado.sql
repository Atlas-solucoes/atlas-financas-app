-- Protege documentos novos contra sobrescrita por uma aba antiga do Atlas.
-- Sem alteração de dados financeiros, RLS, usuários ou chaves.
create schema if not exists atlas_private;
revoke all on schema atlas_private from public;
create or replace function atlas_private.proteger_carteira_legado()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  if jsonb_typeof(old.doc -> 'meios') = 'array'
     and jsonb_array_length(old.doc -> 'meios') > 0
     and (new.doc ->> 'pgSchema') is distinct from '1' then
    raise exception using errcode = 'P0001',
      message = 'Atualize o Atlas antes de sincronizar: esta conta já possui carteira de bancos, cartões e benefícios.';
  end if;
  return new;
end;
$$;
revoke all on function atlas_private.proteger_carteira_legado() from public, anon, authenticated;
drop trigger if exists atlas_proteger_carteira_legado on public.app_state;
create trigger atlas_proteger_carteira_legado before update of doc on public.app_state
for each row execute function atlas_private.proteger_carteira_legado();
