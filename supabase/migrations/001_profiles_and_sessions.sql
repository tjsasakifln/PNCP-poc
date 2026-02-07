-- ============================================================
-- SmartLic Multi-Tenancy: Phase 1 - Profiles & Session History
-- ============================================================

-- 1. Profiles (extends auth.users)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  company text,
  plan_type text not null default 'free'
    check (plan_type in ('free','avulso','pack','monthly','annual','master')),
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name, avatar_url)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 2. Plans catalog
create table if not exists public.plans (
  id text primary key,
  name text not null,
  description text,
  max_searches int,              -- null = unlimited
  price_brl numeric(10,2) not null default 0,
  duration_days int,             -- null = perpetual (master)
  stripe_price_id text,          -- Stripe Price ID for checkout
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

-- Seed default plans
insert into public.plans (id, name, description, max_searches, price_brl, duration_days) values
  ('free',    'Gratuito',           'Acesso limitado para avaliacao',  3,    0,       null),
  ('pack_5',  'Pacote 5 Buscas',   '5 buscas avulsas',               5,    29.90,   null),
  ('pack_10', 'Pacote 10 Buscas',  '10 buscas avulsas',              10,   49.90,   null),
  ('pack_20', 'Pacote 20 Buscas',  '20 buscas avulsas',              20,   89.90,   null),
  ('monthly', 'Mensal Ilimitado',  'Buscas ilimitadas por 30 dias',  null, 149.90,  30),
  ('annual',  'Anual Ilimitado',   'Buscas ilimitadas por 365 dias', null, 1199.90, 365),
  ('master',  'Master',            'Acesso ilimitado perpetuo',       null, 0,       null)
on conflict (id) do nothing;

-- 3. User subscriptions / purchased packs
create table if not exists public.user_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  plan_id text not null references public.plans(id),
  credits_remaining int,           -- null = unlimited (monthly/annual/master)
  starts_at timestamptz not null default now(),
  expires_at timestamptz,          -- null = never expires (packs + master)
  stripe_subscription_id text,     -- Stripe Subscription ID (for recurring)
  stripe_customer_id text,         -- Stripe Customer ID
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create index idx_user_subscriptions_user on public.user_subscriptions(user_id);
create index idx_user_subscriptions_active on public.user_subscriptions(user_id, is_active) where is_active = true;

-- 4. Search sessions (history per user)
create table if not exists public.search_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  sectors text[] not null,
  ufs text[] not null,
  data_inicial date not null,
  data_final date not null,
  custom_keywords text[],
  total_raw int not null default 0,
  total_filtered int not null default 0,
  valor_total numeric(14,2) default 0,
  resumo_executivo text,
  destaques text[],
  excel_storage_path text,         -- Supabase Storage path (future)
  created_at timestamptz not null default now()
);

create index idx_search_sessions_user on public.search_sessions(user_id);
create index idx_search_sessions_created on public.search_sessions(user_id, created_at desc);

-- ============================================================
-- Row Level Security
-- ============================================================

alter table public.profiles enable row level security;
alter table public.plans enable row level security;
alter table public.user_subscriptions enable row level security;
alter table public.search_sessions enable row level security;

-- Profiles: users see/update only their own
create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = id);
create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

-- Plans: everyone can read (public catalog)
create policy "plans_select_all" on public.plans
  for select using (true);

-- Subscriptions: users see only their own
create policy "subscriptions_select_own" on public.user_subscriptions
  for select using (auth.uid() = user_id);

-- Sessions: users see/insert only their own
create policy "sessions_select_own" on public.search_sessions
  for select using (auth.uid() = user_id);
create policy "sessions_insert_own" on public.search_sessions
  for insert with check (auth.uid() = user_id);

-- ============================================================
-- Updated_at trigger
-- ============================================================
create or replace function public.update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger profiles_updated_at
  before update on public.profiles
  for each row execute function public.update_updated_at();
