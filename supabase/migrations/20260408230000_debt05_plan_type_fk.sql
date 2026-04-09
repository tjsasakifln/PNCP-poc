-- ══════════════════════════════════════════════════════════════════════════════
-- DEBT-05: Database Integrity — profiles.plan_type CHECK → FK + is_active audit
--
-- Débitos cobertos:
--   TD-034  pg_dump semanal → S3 (GitHub Actions: .github/workflows/db-backup.yml)
--   TD-021  profiles.plan_type CHECK → FK referencial (integridade garantida)
--   TD-020  Investigar is_active vestigial: DECIDIDO — MANTER (documentado AC4)
--   TD-NEW-002  Confirmar 0 rows is_active=false: CONFIRMADO (purge funciona)
--
-- AC1: Workflow de backup em .github/workflows/db-backup.yml (fora desta migration)
-- AC2: 3-step FK: (1) DROP CHECK → (2) ADD FK NOT VALID → (3) VALIDATE FK
-- AC3: Zero orphan plan_types verificado ANTES de criar FK
-- AC4: Decisão is_active documentada via COMMENT + análise abaixo
-- AC5: VALIDATE usa ShareUpdateExclusiveLock (não bloqueia reads/writes)
--
-- Totalmente idempotente — seguro re-executar.
-- ══════════════════════════════════════════════════════════════════════════════


-- ════════════════════════════════════════════════════════════════════════════
-- PRÉ-CONDIÇÃO: Garantir que free_trial existe em plans
--
-- free_trial é o plan_type padrão de novos usuários (handle_new_user trigger),
-- mas nunca foi inserido formalmente na tabela plans — existia apenas como valor
-- no CHECK constraint. Para a FK referenciar plans(id), o row deve existir.
-- ════════════════════════════════════════════════════════════════════════════
INSERT INTO public.plans (id, name, description, max_searches, price_brl, duration_days, is_active)
VALUES (
    'free_trial',
    'Trial Gratuito',
    'Período de avaliação gratuita de 14 dias com acesso completo ao produto',
    50,     -- 50 buscas durante o trial (ver STORY-264/277/319)
    0.00,   -- gratuito
    14,     -- 14 dias de trial
    true
)
ON CONFLICT (id) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'DEBT-05: free_trial garantido em plans ✓'; END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC3: Verificar zero orphan plan_types
--
-- Todos os valores de profiles.plan_type devem existir em plans.id.
-- Se falhar: investigar quais plan_types estão faltando em plans e inserir
-- antes de re-executar esta migration.
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE
    orphan_count  INTEGER;
    orphan_types  TEXT;
BEGIN
    SELECT
        COUNT(*),
        string_agg(DISTINCT p.plan_type, ', ' ORDER BY p.plan_type)
    INTO orphan_count, orphan_types
    FROM public.profiles p
    WHERE NOT EXISTS (
        SELECT 1 FROM public.plans pl WHERE pl.id = p.plan_type
    );

    IF orphan_count > 0 THEN
        RAISE EXCEPTION
            'DEBT-05/AC3: % perfis com plan_type inválido(s): [%]. Insira os planos faltantes em plans antes de criar a FK.',
            orphan_count, orphan_types;
    END IF;

    RAISE NOTICE 'DEBT-05/AC3: Zero orphan plan_types — todos profiles.plan_type existem em plans.id ✓';
END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC2 — Step 1: DROP CHECK constraint
--
-- O CHECK constraint era a única barreira de integridade. Removemos aqui
-- porque a FK garante integridade de forma mais robusta.
-- AccessShareLock breve; sem impacto em produção.
-- ════════════════════════════════════════════════════════════════════════════
ALTER TABLE public.profiles
    DROP CONSTRAINT IF EXISTS profiles_plan_type_check;

DO $$ BEGIN RAISE NOTICE 'DEBT-05/AC2 Step 1: profiles_plan_type_check CHECK removido ✓'; END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC2 — Step 2: ADD FK NOT VALID  (AC5: lock mínimo)
--
-- NOT VALID: PostgreSQL adiciona o constraint nos metadados sem varrer a tabela.
-- Lock adquirido: RowExclusiveLock (breve, apenas para atualizar pg_constraint).
-- Seguro executar durante horário comercial.
-- Novos INSERTs/UPDATEs passam a ser validados imediatamente.
-- ════════════════════════════════════════════════════════════════════════════
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'profiles_plan_type_fk'
          AND table_name = 'profiles'
          AND constraint_type = 'FOREIGN KEY'
    ) THEN
        ALTER TABLE public.profiles
            ADD CONSTRAINT profiles_plan_type_fk
            FOREIGN KEY (plan_type)
            REFERENCES public.plans(id)
            NOT VALID;
        RAISE NOTICE 'DEBT-05/AC2 Step 2: profiles_plan_type_fk FK adicionado (NOT VALID) ✓';
    ELSE
        RAISE NOTICE 'DEBT-05/AC2 Step 2: profiles_plan_type_fk já existe — pulando ADD ✓';
    END IF;
END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC2 — Step 3: VALIDATE FK  (AC5: ShareUpdateExclusiveLock — off-peak safe)
--
-- VALIDATE varre a tabela profiles verificando cada row.
-- Lock: ShareUpdateExclusiveLock — NÃO bloqueia leituras nem escritas concorrentes.
-- Duração: proporcional ao tamanho da tabela profiles (esperado < 5s em produção).
-- Executado aqui (dentro da migration) às 2 UTC domingo via db-backup.yml schedule,
-- que naturalmente é off-peak. Pode também ser executado manualmente com:
--   ALTER TABLE public.profiles VALIDATE CONSTRAINT profiles_plan_type_fk;
-- ════════════════════════════════════════════════════════════════════════════
ALTER TABLE public.profiles
    VALIDATE CONSTRAINT profiles_plan_type_fk;

DO $$ BEGIN RAISE NOTICE 'DEBT-05/AC2 Step 3: profiles_plan_type_fk VALIDATED ✓'; END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC4: Decisão sobre is_active em pncp_raw_bids
--
-- Investigação (TD-020 + TD-NEW-002):
--   Medição 2026-04-08: 0 rows com is_active = false
--   Hipótese inicial: coluna vestigial (soft-delete nunca usado)
--
-- Análise:
--   1. Coluna USADA no índice parcial:
--      idx_pncp_raw_bids_dashboard_query WHERE is_active = true  (DEBT-01)
--      Removê-la quebraria o índice e a RPC search_datalake.
--
--   2. Coluna USADA na RPC search_datalake:
--      WHERE is_active = true é filtro crítico de performance.
--
--   3. Coluna USADA pelo purge pipeline:
--      loader.py:purge_old_bids() marca is_active=false → hard DELETE.
--      0 rows com is_active=false = purge funciona corretamente, NÃO vestigial.
--
--   4. COMMENT já corrigido em DEBT-01 (migration 20260330120000):
--      "Hard DELETE runs at 4 UTC daily" — semântica documentada.
--
-- DECISÃO: MANTER a coluna is_active.
-- Ação: apenas atualizar COMMENT com resultado desta investigação.
-- ════════════════════════════════════════════════════════════════════════════
COMMENT ON COLUMN public.pncp_raw_bids.is_active IS
    'DEBT-05/AC4: MANTER — Flag de staging para purge pipeline. '
    'FALSE = marcado para deleção por purge_old_bids(). '
    'Hard DELETE executa diariamente às 4 UTC. '
    '0 rows com is_active=false = estado saudável (purge operacional, não coluna vestigial). '
    'Usado em: idx_pncp_raw_bids_dashboard_query (WHERE is_active=true), search_datalake RPC. '
    'TD-020/TD-NEW-002 investigados e encerrados em 2026-04-08.';

DO $$ BEGIN RAISE NOTICE 'DEBT-05/AC4: is_active decision documentada — MANTER ✓'; END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- Verificação final
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE
    fk_exists      BOOLEAN;
    fk_valid       BOOLEAN;
    check_gone     BOOLEAN;
    free_trial_ok  BOOLEAN;
BEGIN
    -- FK exists and validated
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'profiles_plan_type_fk'
          AND conrelid = 'public.profiles'::regclass
          AND contype = 'f'
    ) INTO fk_exists;

    SELECT NOT convalidated IS DISTINCT FROM false INTO fk_valid
    FROM pg_constraint
    WHERE conname = 'profiles_plan_type_fk'
      AND conrelid = 'public.profiles'::regclass
    LIMIT 1;

    -- CHECK constraint removed
    SELECT NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'profiles_plan_type_check'
          AND conrelid = 'public.profiles'::regclass
    ) INTO check_gone;

    -- free_trial in plans
    SELECT EXISTS (
        SELECT 1 FROM public.plans WHERE id = 'free_trial'
    ) INTO free_trial_ok;

    IF fk_exists AND check_gone AND free_trial_ok THEN
        RAISE NOTICE 'DEBT-05 CONCLUÍDO: FK=%, CHECK_removido=%, free_trial_em_plans=%',
            fk_exists, check_gone, free_trial_ok;
    ELSE
        RAISE EXCEPTION
            'DEBT-05 FALHOU: fk_exists=%, check_gone=%, free_trial_ok=%',
            fk_exists, check_gone, free_trial_ok;
    END IF;
END $$;


-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
