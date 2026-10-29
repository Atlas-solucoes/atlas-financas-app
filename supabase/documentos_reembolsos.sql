-- Arquivos privados por proprietário; não altera app_state nem registros financeiros existentes.
create table public.atlas_expense_cases (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 parent_type text not null check(parent_type in ('avulso','gasto','conta','fatura','plano')), parent_id text not null check(length(parent_id) between 1 and 160),
 title text not null check(length(title) between 1 and 140), expense_date date, amount_cents bigint not null default 0 check(amount_cents between 0 and 99999999999),
 scope text not null default 'pessoal' check(scope in ('pessoal','corporativo')), company text not null default '' check(length(company)<=120),
 paid_by text not null default 'proprio' check(paid_by in ('proprio','empresa')),
 reimbursement_status text not null default 'nao_solicitar' check(reimbursement_status in ('nao_solicitar','a_solicitar','solicitado','recebido')),
 reimbursement_record_id text check(length(reimbursement_record_id)<=160), notes text not null default '' check(length(notes)<=2000),
 revision bigint not null default 1 check(revision>0), created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 unique(id,user_id), unique(user_id,parent_type,parent_id),
 check(reimbursement_status='nao_solicitar' or (scope='corporativo' and paid_by='proprio' and length(trim(company))>0))
);
create table public.atlas_documents (
 id uuid primary key, user_id uuid not null references auth.users(id) on delete cascade, case_id uuid not null,
 path text not null unique, file_name text not null check(length(file_name) between 1 and 180), mime_type text not null check(mime_type in ('application/pdf','image/jpeg','image/png','image/webp')),
 size_bytes bigint not null check(size_bytes between 1 and 10485760), sha256 text not null check(sha256 ~ '^[a-f0-9]{64}$'),
 doc_kind text not null default 'outro' check(doc_kind in ('nota','comprovante','boleto','fatura','orcamento','outro')),
 created_at timestamptz not null default now(), unique(user_id,case_id,sha256),
 foreign key(case_id,user_id) references public.atlas_expense_cases(id,user_id) on delete restrict,
 check(path=user_id::text||'/'||case_id::text||'/'||id::text||case mime_type when 'application/pdf' then '.pdf' when 'image/png' then '.png' when 'image/webp' then '.webp' else '.jpg' end)
);
create index atlas_cases_filter on public.atlas_expense_cases(user_id,scope,reimbursement_status,expense_date);
create index atlas_documents_owner_case on public.atlas_documents(user_id,case_id);
alter table public.atlas_expense_cases enable row level security;
alter table public.atlas_documents enable row level security;
revoke all on public.atlas_expense_cases,public.atlas_documents from anon;
grant select,insert,update,delete on public.atlas_expense_cases to authenticated;
grant select,insert,delete on public.atlas_documents to authenticated;
create policy atlas_cases_select on public.atlas_expense_cases for select to authenticated using ((select auth.uid())=user_id);
create policy atlas_cases_insert on public.atlas_expense_cases for insert to authenticated with check ((select auth.uid())=user_id);
create policy atlas_cases_update on public.atlas_expense_cases for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create policy atlas_cases_delete on public.atlas_expense_cases for delete to authenticated using ((select auth.uid())=user_id);
create policy atlas_docs_select on public.atlas_documents for select to authenticated using ((select auth.uid())=user_id);
create policy atlas_docs_insert on public.atlas_documents for insert to authenticated with check ((select auth.uid())=user_id);
create policy atlas_docs_delete on public.atlas_documents for delete to authenticated using ((select auth.uid())=user_id);
create or replace function atlas_private.atlas_case_revision() returns trigger language plpgsql security invoker set search_path='' as $$ begin new.revision=old.revision+1;new.updated_at=now();new.created_at=old.created_at;return new;end $$;
revoke all on function atlas_private.atlas_case_revision() from public,anon,authenticated;
create trigger atlas_case_revision before update on public.atlas_expense_cases for each row execute function atlas_private.atlas_case_revision();
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values ('atlas-financas-documentos','atlas-financas-documentos',false,10485760,array['application/pdf','image/jpeg','image/png','image/webp']);
create policy atlas_files_select on storage.objects for select to authenticated using (bucket_id='atlas-financas-documentos' and (storage.foldername(name))[1]=(select auth.uid()::text));
create policy atlas_files_insert on storage.objects for insert to authenticated with check (bucket_id='atlas-financas-documentos' and (storage.foldername(name))[1]=(select auth.uid()::text) and exists(select 1 from public.atlas_expense_cases c where c.id::text=(storage.foldername(name))[2] and c.user_id=(select auth.uid())));
create policy atlas_files_delete on storage.objects for delete to authenticated using (bucket_id='atlas-financas-documentos' and (storage.foldername(name))[1]=(select auth.uid()::text));
