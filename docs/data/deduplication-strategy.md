# Deduplication Strategy for Multi-Source Procurement Data

**Version:** 1.0
**Status:** Design Phase
**Last Updated:** 2026-02-03

---

## Quick Reference

### Source Priority (for conflict resolution)

| Priority | Source | Rationale |
|----------|--------|-----------|
| 1 (Highest) | PNCP | Official federal portal, most authoritative |
| 2 | Portal de Compras Publicas | Established marketplace |
| 3 | BLL Compras | Major private portal |
| 4 | BNC | Regional focus |
| 5 (Lowest) | Licitar Digital | Newest entrant |

### Match Confidence Thresholds

| Confidence | Action |
|------------|--------|
| >= 0.90 | Auto-merge records |
| 0.75 - 0.89 | Flag for human review |
| < 0.75 | Treat as distinct records |

---

## 1. Problem Statement

The same procurement opportunity may appear in multiple sources (PNCP, BLL, Portal de Compras, etc.) with:
- Different identifiers
- Slightly different field values
- Different levels of completeness

We need to:
1. Identify duplicate records across sources
2. Merge them into a single canonical record
3. Preserve data quality and audit trail

---

## 2. Primary Key Definition

### 2.1 Natural Key (Preferred)

A procurement is uniquely identified by the composite natural key:

```
{orgao_cnpj}:{modalidade_id}:{numero_compra}:{ano_compra}
```

**Example:**
```
83614912000156:6:000001/2026:2026
```

This key should be consistent across sources because:
- CNPJ is the official agency identifier
- numero_compra and ano_compra are assigned by the agency
- modalidade_id follows standard classification

### 2.2 Fallback Key (When CNPJ unavailable)

If CNPJ is not available, use:

```
{orgao_nome_normalized}:{uf}:{modalidade_id}:{numero_compra}:{ano_compra}
```

Where `orgao_nome_normalized` is:
- Lowercase
- Accents removed
- Only alphanumeric characters

**Example:**
```
prefeitura_municipal_de_joinville:SC:6:000001/2026:2026
```

---

## 3. Matching Algorithm

### 3.1 Stage 1: Exact Match

Check for exact matches on high-confidence identifiers:

```python
def exact_match(record1, record2) -> bool:
    """Check for exact match (confidence = 1.0)."""

    # Match on natural key
    if (record1.orgao_cnpj == record2.orgao_cnpj and
        record1.modalidade_id == record2.modalidade_id and
        record1.numero_compra == record2.numero_compra and
        record1.ano_compra == record2.ano_compra):
        return True

    # Match on normalized link_edital URL
    if (record1.link_edital and record2.link_edital and
        normalize_url(record1.link_edital) == normalize_url(record2.link_edital)):
        return True

    return False
```

### 3.2 Stage 2: Fuzzy Match

When exact match fails, use weighted similarity scoring:

| Factor | Weight | Calculation |
|--------|--------|-------------|
| `objeto` similarity | 0.35 | Jaccard on normalized tokens |
| `orgao_nome` similarity | 0.25 | Levenshtein ratio |
| `valor_estimado` proximity | 0.20 | 1.0 if within 5%, else scaled |
| `data_publicacao` proximity | 0.10 | 1.0 if within 7 days, else scaled |
| `uf` + `municipio` match | 0.10 | 1.0 if both match exactly |

**Total: 1.00**

### 3.3 Similarity Functions

```python
from difflib import SequenceMatcher
import unicodedata
import re


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def jaccard_similarity(text1: str, text2: str) -> float:
    """Token-based Jaccard similarity."""
    tokens1 = set(normalize_text(text1).split())
    tokens2 = set(normalize_text(text2).split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union)


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Levenshtein similarity ratio (0-1)."""
    return SequenceMatcher(None, normalize_text(s1), normalize_text(s2)).ratio()


def value_proximity(v1: float, v2: float, threshold: float = 0.05) -> float:
    """Value proximity score (1.0 if within threshold)."""
    if v1 == 0 and v2 == 0:
        return 1.0
    if v1 == 0 or v2 == 0:
        return 0.0

    diff = abs(v1 - v2) / max(v1, v2)
    if diff <= threshold:
        return 1.0
    elif diff >= 0.5:
        return 0.0
    else:
        # Linear scale between threshold and 0.5
        return 1.0 - (diff - threshold) / (0.5 - threshold)


def date_proximity(d1, d2, max_days: int = 7) -> float:
    """Date proximity score."""
    if not d1 or not d2:
        return 0.5  # Neutral when missing

    delta = abs((d1 - d2).days)
    if delta <= max_days:
        return 1.0
    elif delta >= 90:
        return 0.0
    else:
        return 1.0 - (delta - max_days) / (90 - max_days)


def calculate_match_score(record1, record2) -> float:
    """Calculate weighted match score."""
    scores = {
        "objeto": jaccard_similarity(record1.objeto, record2.objeto),
        "orgao_nome": levenshtein_ratio(record1.orgao_nome, record2.orgao_nome),
        "valor": value_proximity(
            float(record1.valor_estimado),
            float(record2.valor_estimado)
        ),
        "data": date_proximity(record1.data_publicacao, record2.data_publicacao),
        "location": 1.0 if (
            record1.uf == record2.uf and
            record1.municipio == record2.municipio
        ) else 0.5 if record1.uf == record2.uf else 0.0,
    }

    weights = {
        "objeto": 0.35,
        "orgao_nome": 0.25,
        "valor": 0.20,
        "data": 0.10,
        "location": 0.10,
    }

    return sum(scores[k] * weights[k] for k in scores)
```

---

## 4. Merge Strategy

### 4.1 Merge Rules

When duplicates are identified:

1. **Select primary record** based on source priority
2. **Fill null fields** from secondary sources
3. **Preserve audit trail** in consolidation metadata

### 4.2 Field Resolution

| Field Type | Resolution Strategy |
|------------|---------------------|
| Identification (source_id) | Keep primary's |
| Core required (objeto, orgao_nome) | Keep primary's |
| Optional fields | Fill from secondary if primary is null |
| Computed fields | Recompute after merge |
| Timestamps | Keep earliest created_at |

### 4.3 Merge Implementation

```python
def merge_records(records: list[UnifiedProcurement]) -> UnifiedProcurement:
    """
    Merge multiple records into one canonical record.

    Args:
        records: List of duplicate records to merge

    Returns:
        Single merged UnifiedProcurement
    """
    if len(records) == 1:
        return records[0]

    # Sort by priority (highest priority = lowest number)
    sorted_records = sorted(records, key=lambda r: r.source_priority)
    primary = sorted_records[0]

    # Start with primary record's data
    merged_data = primary.model_dump()

    # Fields that can be filled from lower-priority sources
    fillable_fields = [
        "orgao_cnpj", "orgao_esfera", "municipio", "municipio_codigo",
        "modalidade_id", "modalidade_nome", "situacao_id", "situacao_nome",
        "data_abertura", "data_encerramento", "valor_homologado",
        "link_edital", "link_portal", "numero_processo", "numero_compra",
        "ano_compra",
    ]

    # Fill nulls from secondary sources
    for field in fillable_fields:
        if merged_data.get(field) is None:
            for record in sorted_records[1:]:
                value = getattr(record, field)
                if value is not None:
                    merged_data[field] = value
                    break

    # Set consolidation metadata
    merged_data["is_consolidated"] = True
    merged_data["consolidated_from"] = [r.unified_id for r in records]
    merged_data["primary_source"] = primary.source_type
    merged_data["consolidation_method"] = "EXACT_MATCH"  # or "FUZZY_MATCH"
    merged_data["consolidation_confidence"] = 1.0  # or calculated score

    # Keep earliest created_at
    merged_data["created_at"] = min(r.created_at for r in records)

    # Generate new unified_id
    import uuid
    merged_data["unified_id"] = str(uuid.uuid4())

    return UnifiedProcurement(**merged_data)
```

---

## 5. Consolidation Pipeline

### 5.1 Pipeline Steps

```
1. INGEST
   - Fetch data from all sources
   - Transform to UnifiedProcurement via adapters
   - Validate required fields

2. INDEX
   - Build index on natural keys
   - Build index on link_edital URLs

3. EXACT MATCH
   - Group records with same natural key
   - Group records with same link_edital

4. FUZZY MATCH
   - For remaining records, compute similarity scores
   - Group records above threshold

5. MERGE
   - For each group, merge records
   - Track consolidation metadata

6. OUTPUT
   - Return consolidated records
   - Return statistics (dedup rate, errors)
```

### 5.2 Pipeline Implementation

```python
from dataclasses import dataclass, field
from collections import defaultdict
import time


@dataclass
class ConsolidationPipeline:
    """Pipeline for consolidating records from multiple sources."""

    confidence_threshold: float = 0.90
    auto_merge_threshold: float = 0.90
    review_threshold: float = 0.75

    # Statistics
    stats: dict = field(default_factory=dict)

    def consolidate(
        self,
        records: list[UnifiedProcurement]
    ) -> ConsolidationResult:
        """Run full consolidation pipeline."""
        start_time = time.time()

        # Track input stats
        input_by_source = defaultdict(int)
        for r in records:
            input_by_source[r.source_type] += 1

        # Stage 1: Group by natural key (exact match)
        key_groups = defaultdict(list)
        for record in records:
            key = record.compute_natural_key()
            key_groups[key].append(record)

        # Stage 2: Group by link_edital (exact match)
        url_groups = defaultdict(list)
        for record in records:
            if record.link_edital:
                url = self._normalize_url(record.link_edital)
                url_groups[url].append(record)

        # Combine groups
        all_groups = self._combine_groups(key_groups, url_groups)

        # Stage 3: Fuzzy match on remaining singletons
        singletons = [g[0] for g in all_groups if len(g) == 1]
        multi_groups = [g for g in all_groups if len(g) > 1]

        fuzzy_groups = self._fuzzy_match_groups(singletons)

        # Combine all groups
        final_groups = multi_groups + fuzzy_groups

        # Stage 4: Merge each group
        merged_records = []
        duplicates_merged = 0

        for group in final_groups:
            if len(group) == 1:
                merged_records.append(group[0])
            else:
                merged = merge_records(group)
                merged_records.append(merged)
                duplicates_merged += 1

        # Compute stats
        output_by_source = defaultdict(int)
        for r in merged_records:
            src = r.primary_source or r.source_type
            output_by_source[src] += 1

        processing_time = (time.time() - start_time) * 1000

        return ConsolidationResult(
            unified_records=merged_records,
            total_input_records=len(records),
            total_output_records=len(merged_records),
            duplicates_merged=duplicates_merged,
            records_by_source=dict(input_by_source),
            output_by_primary_source=dict(output_by_source),
            processing_time_ms=processing_time,
        )

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        url = url.lower().strip()
        url = url.rstrip("/")
        # Remove common tracking params
        url = re.sub(r"\?.*$", "", url)
        return url

    def _combine_groups(
        self,
        key_groups: dict,
        url_groups: dict
    ) -> list[list[UnifiedProcurement]]:
        """Combine groups from different matching methods."""
        # Implementation: union-find on record IDs
        # Simplified: just return key_groups for now
        return list(key_groups.values())

    def _fuzzy_match_groups(
        self,
        records: list[UnifiedProcurement]
    ) -> list[list[UnifiedProcurement]]:
        """Find fuzzy matches among singleton records."""
        if len(records) < 2:
            return [[r] for r in records]

        # Simple O(n^2) approach - optimize for large datasets
        matched = set()
        groups = []

        for i, r1 in enumerate(records):
            if i in matched:
                continue

            group = [r1]
            for j, r2 in enumerate(records[i+1:], start=i+1):
                if j in matched:
                    continue

                score = calculate_match_score(r1, r2)
                if score >= self.confidence_threshold:
                    group.append(r2)
                    matched.add(j)

            groups.append(group)
            matched.add(i)

        return groups
```

---

## 6. Edge Cases

### 6.1 Same Procurement, Different Modalities

A procurement may appear as multiple modalities (e.g., original + amendment).
- **Resolution:** Treat as separate records, link via `numero_processo`

### 6.2 Value Updates

Same procurement with updated value (budget revision).
- **Resolution:** Keep latest based on `source_fetched_at`

### 6.3 Status Transitions

Record in different statuses across sources.
- **Resolution:** Use highest-priority source's status

### 6.4 Conflicting Data

Significantly different values for same field.
- **Resolution:** Flag for review if difference > threshold

---

## 7. Monitoring & Alerts

### 7.1 Metrics to Track

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `dedup_rate` | % records deduplicated | > 50% (suspicious) |
| `error_rate` | % records failing validation | > 5% |
| `fuzzy_match_rate` | % matches via fuzzy (vs exact) | > 30% (review algorithm) |
| `processing_time` | Time per 1000 records | > 30s |
| `source_coverage` | Records per source | < 10% of expected |

### 7.2 Quality Checks

- Cross-validate merged records against source
- Sample review of fuzzy matches
- Track false positive rate over time

---

## 8. Future Enhancements

### 8.1 Machine Learning Matching

- Train model on confirmed duplicates
- Use embeddings for semantic similarity
- Active learning from human reviews

### 8.2 Real-time Deduplication

- Stream processing for new records
- Incremental index updates
- Sub-second matching

### 8.3 Cross-Reference Database

- Maintain mapping of source IDs to unified IDs
- Enable lookup by any source identifier
- Support source-specific updates

---

## Appendix: Test Cases

### A.1 Exact Match Test Cases

```python
def test_exact_match_by_natural_key():
    """Records with same CNPJ+modalidade+numero+ano should match."""
    r1 = create_record(
        orgao_cnpj="12.345.678/0001-90",
        modalidade_id=6,
        numero_compra="001/2026",
        ano_compra=2026,
        source_type=SourceType.PNCP,
    )
    r2 = create_record(
        orgao_cnpj="12.345.678/0001-90",
        modalidade_id=6,
        numero_compra="001/2026",
        ano_compra=2026,
        source_type=SourceType.BLL,
    )
    assert exact_match(r1, r2) is True


def test_exact_match_by_url():
    """Records with same link_edital should match."""
    r1 = create_record(
        link_edital="https://compras.gov.br/edital/123",
        source_type=SourceType.PNCP,
    )
    r2 = create_record(
        link_edital="https://compras.gov.br/edital/123/",
        source_type=SourceType.BLL,
    )
    assert exact_match(r1, r2) is True
```

### A.2 Fuzzy Match Test Cases

```python
def test_fuzzy_match_similar_objeto():
    """Records with similar objeto should match."""
    r1 = create_record(
        objeto="Aquisicao de uniformes escolares para rede municipal",
        orgao_nome="Prefeitura de Joinville",
        valor_estimado=100000,
    )
    r2 = create_record(
        objeto="Aquisicao de uniformes escolares - rede municipal",
        orgao_nome="Prefeitura Municipal de Joinville",
        valor_estimado=100000,
    )
    score = calculate_match_score(r1, r2)
    assert score >= 0.90


def test_fuzzy_match_different_value():
    """Records with significantly different values should not match."""
    r1 = create_record(
        objeto="Uniformes escolares",
        valor_estimado=100000,
    )
    r2 = create_record(
        objeto="Uniformes escolares",
        valor_estimado=500000,  # 5x different
    )
    score = calculate_match_score(r1, r2)
    assert score < 0.75
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | @data-engineer | Initial strategy design |
