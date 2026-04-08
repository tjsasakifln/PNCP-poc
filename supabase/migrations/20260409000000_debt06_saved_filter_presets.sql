-- DEBT-06 TD-037: Saved filter presets
-- Tabela para armazenar presets de filtros salvos pelos usuários.
-- Limite: 10 presets por usuário (enforced via trigger).

create table if not exists public.saved_filter_presets (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  name          text not null check (char_length(name) >= 1 and char_length(name) <= 60),
  filters_json  jsonb not null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- Index para buscas por usuário ordenadas por criação
create index if not exists saved_filter_presets_user_id_created_at_idx
  on public.saved_filter_presets (user_id, created_at desc);

-- RLS
alter table public.saved_filter_presets enable row level security;

-- Usuário vê apenas seus próprios presets
create policy "Users can read own presets"
  on public.saved_filter_presets
  for select using (auth.uid() = user_id);

-- Usuário cria apenas para si mesmo
create policy "Users can insert own presets"
  on public.saved_filter_presets
  for insert with check (auth.uid() = user_id);

-- Usuário atualiza apenas os seus
create policy "Users can update own presets"
  on public.saved_filter_presets
  for update using (auth.uid() = user_id);

-- Usuário deleta apenas os seus
create policy "Users can delete own presets"
  on public.saved_filter_presets
  for delete using (auth.uid() = user_id);

-- Trigger: manter updated_at atualizado
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger saved_filter_presets_updated_at
  before update on public.saved_filter_presets
  for each row execute function public.set_updated_at();

-- Trigger: limite de 10 presets por usuário
create or replace function public.enforce_preset_limit()
returns trigger language plpgsql as $$
declare
  preset_count int;
begin
  select count(*) into preset_count
  from public.saved_filter_presets
  where user_id = new.user_id;

  if preset_count >= 10 then
    raise exception 'Limite de 10 presets por usuário atingido'
      using errcode = 'P0001', hint = 'Delete um preset existente antes de criar outro.';
  end if;
  return new;
end;
$$;

create trigger enforce_preset_limit_trigger
  before insert on public.saved_filter_presets
  for each row execute function public.enforce_preset_limit();

-- Grant usage
grant select, insert, update, delete on public.saved_filter_presets to authenticated;
