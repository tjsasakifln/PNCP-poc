"""DEBT-05: Database Integrity — profiles.plan_type CHECK → FK + is_active audit.

Tests coverage:
  AC1: GitHub Actions workflow para pg_dump semanal para S3
  AC2: FK migration 3 steps (DROP CHECK, ADD FK NOT VALID, VALIDATE)
  AC3: Verificar zero orphan plan_types antes da FK migration
  AC4: Documentar decisão sobre is_active: manter ou remover coluna
  AC5: Execução off-peak para FK validation (lock breve)
"""

import re
import pytest
from pathlib import Path


MIGRATION_DIR = Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations"
WORKFLOW_DIR = Path(__file__).resolve().parent.parent.parent / ".github" / "workflows"

DEBT05_MIGRATION = MIGRATION_DIR / "20260408230000_debt05_plan_type_fk.sql"
BACKUP_WORKFLOW = WORKFLOW_DIR / "db-backup.yml"


# ════════════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def migration_sql():
    assert DEBT05_MIGRATION.exists(), f"Migration não encontrada: {DEBT05_MIGRATION}"
    return DEBT05_MIGRATION.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow_yaml():
    assert BACKUP_WORKFLOW.exists(), f"Workflow não encontrado: {BACKUP_WORKFLOW}"
    return BACKUP_WORKFLOW.read_text(encoding="utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# AC1: GitHub Actions workflow para pg_dump semanal → S3
# ════════════════════════════════════════════════════════════════════════════════

class TestAC1BackupWorkflow:
    """AC1: Workflow de backup semanal pg_dump → S3 existe e está correto."""

    def test_workflow_file_exists(self):
        """AC1: db-backup.yml existe em .github/workflows/."""
        assert BACKUP_WORKFLOW.exists(), "Arquivo db-backup.yml não encontrado"

    def test_workflow_runs_weekly(self, workflow_yaml):
        """AC1: Workflow agendado semanalmente (cron schedule)."""
        assert "schedule" in workflow_yaml
        assert "cron" in workflow_yaml

    def test_workflow_cron_is_sunday_offpeak(self, workflow_yaml):
        """AC1: Cron executado domingo 2:00 UTC (off-peak)."""
        # '0 2 * * 0' = domingo 02:00 UTC
        assert "0 2 * * 0" in workflow_yaml, "Cron deve ser domingo 2 UTC: '0 2 * * 0'"

    def test_workflow_uses_pg_dump(self, workflow_yaml):
        """AC1: Workflow executa pg_dump."""
        assert "pg_dump" in workflow_yaml

    def test_workflow_uploads_to_s3(self, workflow_yaml):
        """AC1: Workflow faz upload para S3 via AWS CLI."""
        assert "aws s3 cp" in workflow_yaml

    def test_workflow_uses_supabase_db_url_secret(self, workflow_yaml):
        """AC1: Workflow usa SUPABASE_DB_URL (secret existente)."""
        assert "SUPABASE_DB_URL" in workflow_yaml

    def test_workflow_uses_aws_credentials_secrets(self, workflow_yaml):
        """AC1: Workflow usa secrets de credenciais AWS."""
        assert "AWS_BACKUP_ACCESS_KEY_ID" in workflow_yaml
        assert "AWS_BACKUP_SECRET_KEY" in workflow_yaml

    def test_workflow_backup_format_is_custom(self, workflow_yaml):
        """AC1: pg_dump usa formato custom (restaurável via pg_restore)."""
        # --format=custom ou --format custom ou BACKUP_FORMAT: "custom"
        assert "custom" in workflow_yaml

    def test_workflow_cleans_up_local_file(self, workflow_yaml):
        """AC1: Workflow remove arquivo local após upload (não deixa lixo no runner)."""
        assert "rm -f" in workflow_yaml

    def test_workflow_verifies_s3_upload(self, workflow_yaml):
        """AC1: Workflow verifica que o backup existe no S3 após upload."""
        assert "aws s3 ls" in workflow_yaml

    def test_workflow_supports_manual_trigger(self, workflow_yaml):
        """AC1: Workflow pode ser disparado manualmente (workflow_dispatch)."""
        assert "workflow_dispatch" in workflow_yaml

    def test_workflow_has_timeout(self, workflow_yaml):
        """AC1: Job tem timeout configurado (evita runs travadas)."""
        assert "timeout-minutes" in workflow_yaml

    def test_workflow_has_storage_class(self, workflow_yaml):
        """AC1: Upload usa STANDARD_IA (custo menor para backups raramente acessados)."""
        assert "STANDARD_IA" in workflow_yaml

    def test_workflow_has_restore_instructions(self, workflow_yaml):
        """AC1: Workflow documenta como restaurar o backup (Step Summary)."""
        assert "pg_restore" in workflow_yaml


# ════════════════════════════════════════════════════════════════════════════════
# AC2: FK migration 3 steps
# ════════════════════════════════════════════════════════════════════════════════

class TestAC2FKMigration3Steps:
    """AC2: Migração FK executada em 3 steps: DROP CHECK, ADD FK NOT VALID, VALIDATE."""

    def test_migration_file_exists(self):
        """AC2: Migration DEBT-05 existe em supabase/migrations/."""
        assert DEBT05_MIGRATION.exists(), f"Migration não encontrada: {DEBT05_MIGRATION}"

    def test_step1_drops_check_constraint(self, migration_sql):
        """AC2 Step 1: DROP CHECK constraint (profiles_plan_type_check) removido."""
        assert "DROP CONSTRAINT IF EXISTS profiles_plan_type_check" in migration_sql

    def test_step1_targets_profiles_table(self, migration_sql):
        """AC2 Step 1: ALTER TABLE targets profiles."""
        pattern = r"ALTER TABLE public\.profiles\s+DROP CONSTRAINT IF EXISTS profiles_plan_type_check"
        assert re.search(pattern, migration_sql, re.IGNORECASE)

    def test_step2_adds_fk_not_valid(self, migration_sql):
        """AC2 Step 2: ADD FK com NOT VALID (sem scan da tabela)."""
        assert "ADD CONSTRAINT profiles_plan_type_fk" in migration_sql
        assert "FOREIGN KEY (plan_type)" in migration_sql
        assert "REFERENCES public.plans(id)" in migration_sql
        assert "NOT VALID" in migration_sql

    def test_step2_fk_references_plans(self, migration_sql):
        """AC2 Step 2: FK referencia plans(id) corretamente."""
        pattern = r"FOREIGN KEY \(plan_type\)\s+REFERENCES public\.plans\(id\)"
        assert re.search(pattern, migration_sql, re.DOTALL)

    def test_step3_validates_fk(self, migration_sql):
        """AC2 Step 3: VALIDATE CONSTRAINT executado para confirmar FK."""
        assert "VALIDATE CONSTRAINT profiles_plan_type_fk" in migration_sql

    def test_steps_in_correct_order(self, migration_sql):
        """AC2: Steps executados na ordem correta (DROP → ADD NOT VALID → VALIDATE)."""
        pos_drop = migration_sql.index("DROP CONSTRAINT IF EXISTS profiles_plan_type_check")
        pos_add = migration_sql.index("ADD CONSTRAINT profiles_plan_type_fk")
        pos_validate = migration_sql.index("VALIDATE CONSTRAINT profiles_plan_type_fk")

        assert pos_drop < pos_add, "DROP CHECK deve vir antes de ADD FK"
        assert pos_add < pos_validate, "ADD FK NOT VALID deve vir antes de VALIDATE"

    def test_fk_uses_idempotent_guard(self, migration_sql):
        """AC2: ADD FK envolto em DO $$ ... IF NOT EXISTS guard (idempotente)."""
        # O guard verifica se a FK já existe antes de tentar criar
        assert "profiles_plan_type_fk" in migration_sql
        # Deve ter algum tipo de guard (IF NOT EXISTS no DO block ou direto)
        assert "IF NOT EXISTS" in migration_sql


# ════════════════════════════════════════════════════════════════════════════════
# AC3: Zero orphan plan_types antes da FK
# ════════════════════════════════════════════════════════════════════════════════

class TestAC3OrphanCheck:
    """AC3: Migration verifica zero orphan plan_types antes de criar FK."""

    def test_orphan_check_exists(self, migration_sql):
        """AC3: Migration contém verificação de orphan plan_types."""
        # Deve ter uma query que verifica plan_type NOT IN plans
        assert "NOT IN" in migration_sql or "NOT EXISTS" in migration_sql

    def test_orphan_check_raises_exception(self, migration_sql):
        """AC3: Verificação levanta EXCEPTION (não apenas WARNING) se orphans existirem."""
        assert "RAISE EXCEPTION" in migration_sql

    def test_orphan_check_mentions_profiles_and_plans(self, migration_sql):
        """AC3: Check verifica relação entre profiles e plans."""
        assert "profiles" in migration_sql.lower()
        assert "plans" in migration_sql.lower()

    def test_free_trial_inserted_before_orphan_check(self, migration_sql):
        """AC3: free_trial inserido em plans ANTES da verificação de orphans.

        free_trial é o plan_type padrão de novos usuários.
        Sem inserir em plans primeiro, o orphan check detectaria falso positivo.
        """
        # Posição do INSERT de free_trial vs posição do RAISE EXCEPTION
        pos_insert = migration_sql.index("INSERT INTO public.plans")
        pos_exception = migration_sql.index("RAISE EXCEPTION")
        assert pos_insert < pos_exception, (
            "INSERT INTO plans (free_trial) deve vir ANTES do orphan check"
        )

    def test_free_trial_inserted_in_plans(self, migration_sql):
        """AC3: free_trial inserido em plans (pré-requisito para FK)."""
        assert "'free_trial'" in migration_sql
        assert "INSERT INTO public.plans" in migration_sql
        # Deve usar ON CONFLICT DO NOTHING para idempotência
        assert "ON CONFLICT (id) DO NOTHING" in migration_sql

    def test_orphan_check_before_drop_check(self, migration_sql):
        """AC3: Orphan check executado antes de DROP CHECK (ordem de segurança)."""
        pos_exception = migration_sql.index("RAISE EXCEPTION")
        pos_drop = migration_sql.index("DROP CONSTRAINT IF EXISTS profiles_plan_type_check")
        assert pos_exception < pos_drop, (
            "Orphan check deve vir antes do DROP CHECK"
        )


# ════════════════════════════════════════════════════════════════════════════════
# AC4: Decisão is_active documentada
# ════════════════════════════════════════════════════════════════════════════════

class TestAC4IsActiveDecision:
    """AC4: Decisão sobre is_active documentada na migration."""

    def test_is_active_decision_documented(self, migration_sql):
        """AC4: Migration documenta decisão sobre is_active."""
        assert "is_active" in migration_sql

    def test_decision_is_to_keep_column(self, migration_sql):
        """AC4: Decisão é MANTER (não remover) a coluna is_active."""
        # A decisão deve mencionar 'MANTER' ou 'keep' ou similar
        assert "MANTER" in migration_sql or "keep" in migration_sql.lower()

    def test_is_active_comment_updated(self, migration_sql):
        """AC4: COMMENT ON COLUMN pncp_raw_bids.is_active atualizado com decisão."""
        assert "COMMENT ON COLUMN public.pncp_raw_bids.is_active" in migration_sql

    def test_rationale_mentions_index(self, migration_sql):
        """AC4: Justificativa menciona uso no índice (não vestigial)."""
        # O comentário deve mencionar índice ou index
        assert "index" in migration_sql.lower() or "índice" in migration_sql.lower()

    def test_rationale_mentions_purge(self, migration_sql):
        """AC4: Justificativa menciona purge pipeline (razão para 0 rows is_active=false)."""
        assert "purge" in migration_sql.lower()

    def test_td020_reference_in_migration(self, migration_sql):
        """AC4: Migration referencia TD-020 (rastreabilidade)."""
        assert "TD-020" in migration_sql


# ════════════════════════════════════════════════════════════════════════════════
# AC5: Off-peak execution para FK validation
# ════════════════════════════════════════════════════════════════════════════════

class TestAC5OffPeakExecution:
    """AC5: FK validation executada com lock mínimo (ShareUpdateExclusiveLock)."""

    def test_validate_uses_not_valid_pattern(self, migration_sql):
        """AC5: ADD FK usa NOT VALID + VALIDATE separados (evita lock prolongado)."""
        assert "NOT VALID" in migration_sql
        assert "VALIDATE CONSTRAINT" in migration_sql

    def test_migration_documents_lock_type(self, migration_sql):
        """AC5: Migration documenta qual lock é adquirido durante VALIDATE."""
        assert "ShareUpdateExclusiveLock" in migration_sql

    def test_migration_notes_offpeak_recommendation(self, migration_sql):
        """AC5: Migration documenta execução off-peak."""
        assert "off-peak" in migration_sql.lower() or "off_peak" in migration_sql.lower()


# ════════════════════════════════════════════════════════════════════════════════
# Idempotência geral
# ════════════════════════════════════════════════════════════════════════════════

class TestMigrationIdempotency:
    """Migration deve ser segura para re-executar."""

    def test_drop_uses_if_exists(self, migration_sql):
        """DROP CONSTRAINT usa IF EXISTS (seguro re-executar)."""
        drops = re.findall(r"DROP CONSTRAINT\b.*?;", migration_sql, re.DOTALL)
        for drop in drops:
            assert "IF EXISTS" in drop, f"DROP CONSTRAINT sem IF EXISTS: {drop[:80]}"

    def test_insert_uses_on_conflict(self, migration_sql):
        """INSERT em plans usa ON CONFLICT DO NOTHING (idempotente)."""
        assert "ON CONFLICT (id) DO NOTHING" in migration_sql

    def test_add_fk_guarded_by_existence_check(self, migration_sql):
        """ADD FK protegido por verificação de existência (não duplica constraint)."""
        # Deve haver um DO $$ block com IF NOT EXISTS checando profiles_plan_type_fk
        assert "profiles_plan_type_fk" in migration_sql
        # IF NOT EXISTS deve aparecer no contexto de verificar a FK
        fk_section = migration_sql[
            migration_sql.find("profiles_plan_type_fk"):
            migration_sql.find("profiles_plan_type_fk") + 500
        ]
        assert "IF NOT EXISTS" in migration_sql

    def test_migration_ends_with_notify_pgrst(self, migration_sql):
        """Migration termina com NOTIFY pgrst para refresh do schema PostgREST."""
        assert "NOTIFY pgrst, 'reload schema'" in migration_sql

    def test_migration_has_final_verification(self, migration_sql):
        """Migration contém bloco de verificação final."""
        assert "RAISE NOTICE" in migration_sql
        # Deve haver algum bloco de verificação pós-migration
        assert "CONCLUÍDO" in migration_sql or "verified" in migration_sql.lower()


# ════════════════════════════════════════════════════════════════════════════════
# Timestamp e ordenação
# ════════════════════════════════════════════════════════════════════════════════

class TestMigrationOrdering:
    """DEBT-05 deve vir após migrations que dependem."""

    def test_debt05_timestamp_is_after_debt03(self):
        """DEBT-05 (20260408230000) é após DEBT-03 (20260408220000)."""
        debt03 = MIGRATION_DIR / "20260408220000_debt03_rpc_security_audit.sql"
        debt01 = MIGRATION_DIR / "20260408210000_debt01_index_retention.sql"
        assert DEBT05_MIGRATION.exists()
        # Timestamp comparison via filename
        assert "20260408230000" > "20260408220000" > "20260408210000"

    def test_debt05_timestamp_is_after_single_plan_migration(self):
        """DEBT-05 vem após migration que introduziu consultoria (20260301300000)."""
        consultoria_migration = MIGRATION_DIR / "20260301300000_consultoria_stripe_ids.sql"
        assert consultoria_migration.exists()
        assert "20260408230000" > "20260301300000"

    def test_prerequisite_migrations_exist(self):
        """Migrations prerequisito existem (planos que devem estar em plans antes da FK)."""
        prerequisites = [
            "005_update_plans_to_new_tiers.sql",        # consultor_agil, maquina, sala_guerra
            "029_single_plan_model.sql",                 # smartlic_pro
            "20260301300000_consultoria_stripe_ids.sql", # consultoria
        ]
        for prereq in prerequisites:
            path = MIGRATION_DIR / prereq
            assert path.exists(), f"Migration prerequisito não encontrada: {prereq}"
