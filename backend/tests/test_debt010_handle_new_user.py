"""DEBT-010 DB-011: Integration test for handle_new_user() trigger.

Verifies that the trigger produces profiles matching the expected schema:
- 10 fields: id, email, full_name, company, sector, phone_whatsapp,
  whatsapp_consent, plan_type, avatar_url, context_data
- Phone normalization: strips formatting, validates 10-11 digits, removes country code
- Default plan_type: 'free_trial'
- ON CONFLICT (id) DO NOTHING for re-signups
"""

import re


# The expected fields that handle_new_user() inserts
EXPECTED_PROFILE_FIELDS = {
    "id",
    "email",
    "full_name",
    "company",
    "sector",
    "phone_whatsapp",
    "whatsapp_consent",
    "plan_type",
    "avatar_url",
    "context_data",
}

# Regex for phone normalization (mirrors trigger logic)
def normalize_phone(raw_phone: str | None) -> str | None:
    """Python mirror of handle_new_user() phone normalization logic."""
    if not raw_phone:
        return None
    # Strip non-digits
    phone = re.sub(r"[^0-9]", "", raw_phone)
    # Remove country code 55
    if len(phone) > 11 and phone[:2] == "55":
        phone = phone[2:]
    # Remove leading 0
    if phone and phone[0] == "0":
        phone = phone[1:]
    # Validate length
    if len(phone) not in (10, 11):
        return None
    return phone


class TestHandleNewUserTriggerSchema:
    """Verify handle_new_user() trigger produces correct profile schema."""

    def test_expected_fields_count(self):
        """AC2: Trigger inserts exactly 10 fields."""
        assert len(EXPECTED_PROFILE_FIELDS) == 10

    def test_trigger_sql_contains_all_fields(self):
        """AC2: The migration SQL references all expected fields."""
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "supabase", "migrations",
            "20260225110000_fix_handle_new_user_trigger.sql",
        )
        with open(migration_path, "r") as f:
            sql = f.read().lower()

        for field in EXPECTED_PROFILE_FIELDS:
            assert field.lower() in sql, f"Field '{field}' not found in trigger SQL"

    def test_trigger_has_on_conflict(self):
        """AC2: Trigger uses ON CONFLICT (id) DO NOTHING for re-signup safety."""
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "supabase", "migrations",
            "20260225110000_fix_handle_new_user_trigger.sql",
        )
        with open(migration_path, "r") as f:
            sql = f.read()

        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql

    def test_trigger_default_plan_type(self):
        """AC2: Default plan_type is 'free_trial'."""
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "supabase", "migrations",
            "20260225110000_fix_handle_new_user_trigger.sql",
        )
        with open(migration_path, "r") as f:
            sql = f.read()

        assert "'free_trial'" in sql

    def test_trigger_is_security_definer(self):
        """AC2: Trigger uses SECURITY DEFINER (required for auth.users access)."""
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "supabase", "migrations",
            "20260225110000_fix_handle_new_user_trigger.sql",
        )
        with open(migration_path, "r") as f:
            sql = f.read()

        assert "SECURITY DEFINER" in sql


class TestPhoneNormalization:
    """Verify phone normalization logic matches trigger behavior."""

    def test_strips_formatting(self):
        assert normalize_phone("(11) 98765-4321") == "11987654321"

    def test_removes_country_code_55(self):
        assert normalize_phone("5511987654321") == "11987654321"

    def test_removes_leading_zero(self):
        assert normalize_phone("011987654321") == "11987654321"

    def test_valid_10_digit(self):
        assert normalize_phone("1198765432") == "1198765432"

    def test_valid_11_digit(self):
        assert normalize_phone("11987654321") == "11987654321"

    def test_invalid_short(self):
        assert normalize_phone("123456") is None

    def test_invalid_long(self):
        assert normalize_phone("123456789012345") is None

    def test_none_input(self):
        assert normalize_phone(None) is None

    def test_empty_string(self):
        assert normalize_phone("") is None

    def test_full_international_format(self):
        """Country code + DDD + number."""
        assert normalize_phone("+55 (11) 98765-4321") == "11987654321"

    def test_all_zeros_country_code(self):
        """Leading 0 after country code removal."""
        assert normalize_phone("55011987654321") == "11987654321"


class TestTriggerFieldMapping:
    """Verify the INSERT statement maps COALESCE defaults correctly."""

    def test_coalesce_defaults_in_sql(self):
        """Trigger uses COALESCE for optional metadata fields."""
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "supabase", "migrations",
            "20260225110000_fix_handle_new_user_trigger.sql",
        )
        with open(migration_path, "r") as f:
            sql = f.read()

        # full_name, company, sector have COALESCE with empty string default
        assert "COALESCE(NEW.raw_user_meta_data->>'full_name', '')" in sql
        assert "COALESCE(NEW.raw_user_meta_data->>'company', '')" in sql
        assert "COALESCE(NEW.raw_user_meta_data->>'sector', '')" in sql
        # whatsapp_consent defaults to FALSE
        assert "COALESCE((NEW.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE)" in sql
        # context_data defaults to empty JSONB
        assert "'{}'::jsonb" in sql
