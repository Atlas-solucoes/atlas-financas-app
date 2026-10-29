-- Cadastro privado e vínculo opcional: preserva os nomes e registros anteriores.
create table public.atlas_companies (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 legal_name text not null check(length(trim(legal_name)) between 1 and 120),
 cnpj text not null check(cnpj ~ '^[A-Z0-9]{12}[0-9]{2}$'),
 state_registration text not null default '' check(length(state_registration)<=30),
 archived boolean not null default false,
 revision bigint not null default 1 check(revision>0),
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 unique(id,user_id), unique(user_id,cnpj)
);
alter table public.atlas_companies enable row level security;
revoke all on public.atlas_companies from public,anon;
grant select,insert,update on public.atlas_companies to authenticated;
create policy atlas_companies_select on public.atlas_companies for select to authenticated using ((select auth.uid())=user_id);
create policy atlas_companies_insert on public.atlas_companies for insert to authenticated with check ((select auth.uid())=user_id);
create policy atlas_companies_update on public.atlas_companies for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create trigger atlas_companies_revision before update on public.atlas_companies for each row execute function atlas_private.atlas_case_revision();
alter table public.atlas_expense_cases add column company_id uuid;
alter table public.atlas_expense_cases add constraint atlas_cases_company_owner foreign key(company_id,user_id) references public.atlas_companies(id,user_id) on delete restrict;
create index atlas_cases_company on public.atlas_expense_cases(company_id,user_id);
