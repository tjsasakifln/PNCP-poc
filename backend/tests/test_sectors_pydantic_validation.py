"""TD-SYS-020: Tests for Pydantic validation of sectors_data.yaml at startup."""
import pytest
from pydantic import ValidationError

from sectors import SectorsYamlSchema, SectorYaml, SECTORS


class TestSectorsYamlSchema:
    def test_real_yaml_passes_validation(self):
        """The actual sectors_data.yaml must pass validation."""
        import yaml, os
        yaml_path = os.path.join(os.path.dirname(__file__), "..", "sectors_data.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        schema = SectorsYamlSchema.model_validate(data)
        assert len(schema.sectors) > 0

    def test_missing_required_name_fails(self):
        data = {"sectors": {"test": {"description": "D", "keywords": ["kw"]}}}
        with pytest.raises(ValidationError, match="name"):
            SectorsYamlSchema.model_validate(data)

    def test_missing_required_keywords_fails(self):
        data = {"sectors": {"test": {"name": "N", "description": "D"}}}
        with pytest.raises(ValidationError, match="keywords"):
            SectorsYamlSchema.model_validate(data)

    def test_keywords_must_be_list_of_strings(self):
        data = {"sectors": {"test": {"name": "N", "description": "D", "keywords": [123, 456]}}}
        with pytest.raises(ValidationError):
            SectorsYamlSchema.model_validate(data)

    def test_viability_range_must_have_two_elements(self):
        data = {"sectors": {"test": {"name": "N", "description": "D", "keywords": ["kw"],
                                      "viability_value_range": [1000]}}}
        with pytest.raises(ValidationError, match="2 elements"):
            SectorsYamlSchema.model_validate(data)

    def test_valid_sector_with_all_fields(self):
        data = {"sectors": {"vestuario": {
            "name": "Vestuário",
            "description": "Setor de vestuário",
            "keywords": ["uniforme", "roupa"],
            "exclusions": ["móveis"],
            "viability_value_range": [1000.0, 500000.0],
            "co_occurrence_rules": [{"trigger": "uniforme", "negative_contexts": ["hospital"]}],
        }}}
        schema = SectorsYamlSchema.model_validate(data)
        assert schema.sectors["vestuario"].name == "Vestuário"

    def test_sectors_global_loads_without_error(self):
        """SECTORS module-level variable must be non-empty (validation passed)."""
        assert len(SECTORS) > 0
        first = next(iter(SECTORS.values()))
        assert first.name
        assert len(first.keywords) > 0
