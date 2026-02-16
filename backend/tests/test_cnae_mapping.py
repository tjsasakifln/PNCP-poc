"""Tests for CNAE to sector mapping (GTM-004 AC6)."""

import pytest
from utils.cnae_mapping import map_cnae_to_setor, get_setor_name


class TestMapCnaeToSetor:
    """Test CNAE code to sector mapping."""

    @pytest.mark.parametrize("cnae,expected", [
        # Vestuário
        ("4781", "vestuario"),
        ("1412", "vestuario"),
        # Facilities
        ("8121", "facilities"),
        ("8011", "facilities"),
        # Equipamentos
        ("2710", "equipamentos"),
        ("3250", "equipamentos"),
        # Alimentos
        ("1011", "alimentos"),
        ("1091", "alimentos"),
        # TI
        ("6201", "informatica"),
        ("6202", "informatica"),
    ])
    def test_top_10_cnaes(self, cnae: str, expected: str):
        """AC6: All top 10 CNAEs map to correct sector."""
        assert map_cnae_to_setor(cnae) == expected

    @pytest.mark.parametrize("cnae,expected", [
        ("4781-4/00", "vestuario"),
        ("8121-4/00", "facilities"),
        ("6201-5/01", "informatica"),
    ])
    def test_formatted_cnae(self, cnae: str, expected: str):
        """Handles CNAE in full format (e.g., 4781-4/00)."""
        assert map_cnae_to_setor(cnae) == expected

    @pytest.mark.parametrize("cnae,expected", [
        ("47814", "vestuario"),
        ("81214", "facilities"),
    ])
    def test_five_digit_cnae(self, cnae: str, expected: str):
        """Handles 5-digit CNAE prefix format."""
        assert map_cnae_to_setor(cnae) == expected

    def test_unknown_cnae_falls_back_to_vestuario(self):
        """Unknown CNAE falls back to vestuario."""
        assert map_cnae_to_setor("9999") == "vestuario"
        assert map_cnae_to_setor("0000") == "vestuario"

    def test_empty_input(self):
        """Empty or very short input falls back to vestuario."""
        assert map_cnae_to_setor("") == "vestuario"
        assert map_cnae_to_setor("12") == "vestuario"
        assert map_cnae_to_setor("abc") == "vestuario"

    def test_whitespace_handling(self):
        """Handles leading/trailing whitespace."""
        assert map_cnae_to_setor("  4781  ") == "vestuario"
        assert map_cnae_to_setor(" 8121-4/00 ") == "facilities"

    def test_text_with_cnae(self):
        """Handles CNAE embedded in description text."""
        # The function extracts first 4 digits
        assert map_cnae_to_setor("4781-4/00 — Comércio varejista") == "vestuario"


class TestGetSetorName:
    """Test sector name lookup."""

    def test_known_sectors(self):
        """Returns correct names for known sectors."""
        assert get_setor_name("vestuario") == "Vestuário e Uniformes"
        assert get_setor_name("facilities") == "Facilities e Serviços"
        assert get_setor_name("equipamentos") == "Equipamentos"
        assert get_setor_name("alimentos") == "Alimentos e Merenda"
        assert get_setor_name("informatica") == "Hardware e Equipamentos de TI"

    def test_unknown_sector(self):
        """Falls back to title-cased ID for unknown sectors."""
        assert get_setor_name("unknown_sector") == "Unknown Sector"
