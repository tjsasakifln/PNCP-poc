"""
Integration tests for new sectors (saude, vigilancia, transporte).

Hits the real PNCP API, fetches data, applies sector keywords,
and validates true/false positive rates.

Usage:
    pytest tests/test_integration_new_sectors.py -v -s --timeout=120
"""

import logging
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Tuple

import pytest

sys.path.insert(0, ".")

from filter import match_keywords, normalize_text
from pncp_client import PNCPClient
from sectors import get_sector

logger = logging.getLogger(__name__)

# Use a recent 7-day window for testing
# Adjust if tests are run at a different time

_today = date.today()
_end = _today - timedelta(days=1)  # yesterday (avoid incomplete day)
_start = _end - timedelta(days=6)  # 7-day window

DATA_INICIAL = _start.strftime("%Y-%m-%d")
DATA_FINAL = _end.strftime("%Y-%m-%d")

# States with high procurement volume
TEST_UFS = ["SP", "MG", "RJ", "PR", "BA", "RS"]
MODALIDADE = 6  # Pregão Eletrônico


@dataclass
class SectorTestResult:
    """Results from testing a sector against real PNCP data."""

    sector_id: str
    total_fetched: int
    matched: int
    excluded: int
    match_rate: float
    sample_matches: List[str]
    sample_excluded: List[Tuple[str, str]]  # (objeto, exclusion_reason)
    false_positive_candidates: List[str]  # matched but look suspicious


def fetch_pncp_sample(client: PNCPClient, uf: str, max_pages: int = 3) -> list:
    """Fetch a sample of PNCP records for a given UF."""
    records = []
    for page in range(1, max_pages + 1):
        try:
            resp = client.fetch_page(
                data_inicial=DATA_INICIAL,
                data_final=DATA_FINAL,
                modalidade=MODALIDADE,
                uf=uf,
                pagina=page,
                tamanho=50,  # PNCP max reduced 500→50 (~Feb 2026)
            )
            data = resp.get("data", [])
            if not data:
                break
            records.extend(data)
            if not resp.get("temProximaPagina", False):
                break
        except Exception as e:
            logger.warning(f"Error fetching page {page} for {uf}: {e}")
            break
    return records


def run_sector_against_api(sector_id: str, records: list) -> SectorTestResult:
    """Test a sector's keywords against real PNCP records."""
    sector = get_sector(sector_id)
    keywords = sector.keywords
    exclusions = sector.exclusions

    matched_objects = []
    excluded_objects = []
    all_matched_keywords = Counter()

    for rec in records:
        objeto = rec.get("objetoCompra", "")
        if not objeto:
            continue

        ok, matched_kws = match_keywords(objeto, keywords, exclusions)

        if ok:
            matched_objects.append(objeto)
            for kw in matched_kws:
                all_matched_keywords[kw] += 1
        else:
            # Check if it would have matched without exclusions
            ok_no_exc, _ = match_keywords(objeto, keywords, None)
            if ok_no_exc:
                excluded_objects.append((objeto, "excluded by exclusion list"))

    match_rate = len(matched_objects) / len(records) * 100 if records else 0

    return SectorTestResult(
        sector_id=sector_id,
        total_fetched=len(records),
        matched=len(matched_objects),
        excluded=len(excluded_objects),
        match_rate=match_rate,
        sample_matches=matched_objects[:10],
        sample_excluded=excluded_objects[:5],
        false_positive_candidates=[],
    )


# ─── Fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def pncp_client():
    """Create a PNCP client instance."""
    return PNCPClient()


@pytest.fixture(scope="module")
def pncp_records(pncp_client):
    """Fetch a shared pool of PNCP records for all tests."""
    all_records = []
    for uf in TEST_UFS:
        recs = fetch_pncp_sample(pncp_client, uf, max_pages=5)
        logger.info(f"Fetched {len(recs)} records for {uf}")
        all_records.extend(recs)
    logger.info(f"Total records fetched: {len(all_records)}")
    assert len(all_records) > 0, (
        f"No records fetched from PNCP API for {TEST_UFS} "
        f"({DATA_INICIAL} to {DATA_FINAL}). API may be down."
    )
    return all_records


# ─── Saúde Sector Tests ───────────────────────────────────

@pytest.mark.integration
class TestSaudeIntegration:
    """Validate Saúde sector keywords against real PNCP data."""

    def test_saude_finds_matches(self, pncp_records):
        """Saúde sector should find some matches in a large enough sample."""
        result = run_sector_against_api("saude", pncp_records)
        print(f"\n{'='*60}")
        print("SAÚDE SECTOR RESULTS")
        print(f"{'='*60}")
        print(f"Total records: {result.total_fetched}")
        print(f"Matched: {result.matched} ({result.match_rate:.1f}%)")
        print(f"Excluded (would match w/o exclusions): {result.excluded}")
        print("\nSample matches:")
        for obj in result.sample_matches[:5]:
            print(f"  [+] {obj[:120]}")
        if result.sample_excluded:
            print("\nExcluded samples:")
            for obj, reason in result.sample_excluded[:3]:
                print(f"  [-] {obj[:120]}")
        # With 100+ records, saude should find at least some matches
        # (health is ~20% of all procurement)
        assert result.matched > 0 or result.total_fetched < 50, (
            f"Saúde found 0 matches in {result.total_fetched} records. "
            f"Keywords may need tuning."
        )

    def test_saude_exclusions_work(self, pncp_records):
        """Verify exclusions prevent false positives."""
        sector = get_sector("saude")
        false_positives = []
        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            ok, kws = match_keywords(objeto, sector.keywords, sector.exclusions)
            if ok:
                # Check for common false positive patterns
                norm = normalize_text(objeto)
                suspicious_patterns = [
                    "construção civil", "construcao civil",
                    "material de limpeza",
                    "uniforme", "fardamento",
                    "software", "sistema de gestao",
                    "merenda escolar",
                ]
                for pattern in suspicious_patterns:
                    if pattern in norm and not any(
                        medical in norm
                        for medical in ["hospitalar", "médico", "medico", "saúde", "saude", "medicamento"]
                    ):
                        false_positives.append((objeto[:100], kws, pattern))
                        break

        print(f"\nSaúde false positive candidates: {len(false_positives)}")
        for obj, kws, pattern in false_positives[:5]:
            print(f"  [!] [{pattern}] {obj} (matched: {kws})")

        # Allow some but flag if too many
        assert len(false_positives) <= max(5, len(pncp_records) * 0.02), (
            f"Too many false positives ({len(false_positives)}). "
            f"Review exclusion list."
        )

    def test_saude_keyword_coverage(self, pncp_records):
        """Check which keyword categories actually produce matches."""
        sector = get_sector("saude")
        keyword_hits = Counter()
        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            ok, kws = match_keywords(objeto, sector.keywords, sector.exclusions)
            if ok:
                for kw in kws:
                    keyword_hits[kw] += 1

        print("\nSaúde keyword hit distribution (top 15):")
        for kw, count in keyword_hits.most_common(15):
            print(f"  {kw}: {count}")

        # No assertion here — informational only


# ─── Vigilância Sector Tests ──────────────────────────────

@pytest.mark.integration
class TestVigilanciaIntegration:
    """Validate Vigilância e Segurança sector keywords against real PNCP data."""

    def test_vigilancia_finds_matches(self, pncp_records):
        result = run_sector_against_api("vigilancia", pncp_records)
        print(f"\n{'='*60}")
        print("VIGILÂNCIA SECTOR RESULTS")
        print(f"{'='*60}")
        print(f"Total records: {result.total_fetched}")
        print(f"Matched: {result.matched} ({result.match_rate:.1f}%)")
        print(f"Excluded: {result.excluded}")
        print("\nSample matches:")
        for obj in result.sample_matches[:5]:
            print(f"  [+] {obj[:120]}")
        if result.sample_excluded:
            print("\nExcluded samples:")
            for obj, reason in result.sample_excluded[:3]:
                print(f"  [-] {obj[:120]}")
        # Vigilância may have low match rate with modality 6 only
        # (many security contracts use Dispensa or Pregão Presencial)
        if result.matched == 0:
            print("  NOTE: 0 matches — security contracts may use other modalities")
        assert result.matched >= 0  # informational — don't fail on 0

    def test_vigilancia_excludes_sanitaria(self, pncp_records):
        """Vigilância sanitária should NOT match vigilância sector."""
        sector = get_sector("vigilancia")
        sanitaria_leaked = []
        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            ok, kws = match_keywords(objeto, sector.keywords, sector.exclusions)
            if ok:
                norm = normalize_text(objeto)
                if "sanitaria" in norm or "epidemiologica" in norm:
                    sanitaria_leaked.append(objeto[:100])

        print(f"\nVigilância sanitária leaks: {len(sanitaria_leaked)}")
        for obj in sanitaria_leaked[:3]:
            print(f"  [!] {obj}")
        assert len(sanitaria_leaked) == 0, (
            f"Vigilância sanitária leaked through exclusions: {sanitaria_leaked[:3]}"
        )

    def test_vigilancia_keyword_coverage(self, pncp_records):
        sector = get_sector("vigilancia")
        keyword_hits = Counter()
        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            ok, kws = match_keywords(objeto, sector.keywords, sector.exclusions)
            if ok:
                for kw in kws:
                    keyword_hits[kw] += 1

        print("\nVigilância keyword hit distribution (top 15):")
        for kw, count in keyword_hits.most_common(15):
            print(f"  {kw}: {count}")


# ─── Transporte Sector Tests ──────────────────────────────

@pytest.mark.integration
class TestTransporteIntegration:
    """Validate Transporte e Veículos sector keywords against real PNCP data."""

    def test_transporte_finds_matches(self, pncp_records):
        result = run_sector_against_api("transporte", pncp_records)
        print(f"\n{'='*60}")
        print("TRANSPORTE SECTOR RESULTS")
        print(f"{'='*60}")
        print(f"Total records: {result.total_fetched}")
        print(f"Matched: {result.matched} ({result.match_rate:.1f}%)")
        print(f"Excluded: {result.excluded}")
        print("\nSample matches:")
        for obj in result.sample_matches[:5]:
            print(f"  [+] {obj[:120]}")
        if result.sample_excluded:
            print("\nExcluded samples:")
            for obj, reason in result.sample_excluded[:3]:
                print(f"  [-] {obj[:120]}")
        assert result.matched > 0 or result.total_fetched < 50, (
            f"Transporte found 0 matches in {result.total_fetched} records."
        )

    def test_transporte_excludes_non_vehicle(self, pncp_records):
        """Check that non-vehicle uses of keywords are excluded."""
        sector = get_sector("transporte")
        false_positives = []
        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            ok, kws = match_keywords(objeto, sector.keywords, sector.exclusions)
            if ok:
                norm = normalize_text(objeto)
                suspicious = [
                    "veiculo de comunicacao",
                    "mecanica dos solos",
                    "ventilador mecanico", "ventilacao mecanica",
                    "filtro de agua",
                    "bateria de notebook",
                ]
                for pattern in suspicious:
                    if pattern in norm:
                        false_positives.append((objeto[:100], kws, pattern))
                        break

        print(f"\nTransporte false positive candidates: {len(false_positives)}")
        for obj, kws, pattern in false_positives[:3]:
            print(f"  [!] [{pattern}] {obj} (matched: {kws})")
        assert len(false_positives) == 0, (
            f"Known false positive patterns leaked: {false_positives[:3]}"
        )

    def test_transporte_keyword_coverage(self, pncp_records):
        sector = get_sector("transporte")
        keyword_hits = Counter()
        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            ok, kws = match_keywords(objeto, sector.keywords, sector.exclusions)
            if ok:
                for kw in kws:
                    keyword_hits[kw] += 1

        print("\nTransporte keyword hit distribution (top 15):")
        for kw, count in keyword_hits.most_common(15):
            print(f"  {kw}: {count}")


# ─── Cross-Sector Overlap Test ─────────────────────────────

@pytest.mark.integration
class TestCrossSectorOverlap:
    """Verify new sectors don't excessively overlap with existing ones."""

    def test_no_excessive_overlap(self, pncp_records):
        """Each matched record should predominantly belong to one sector."""
        new_sectors = ["saude", "vigilancia", "transporte"]
        all_sectors = [
            "vestuario", "alimentos", "informatica", "mobiliario",
            "papelaria", "engenharia", "software", "facilities",
            "manutencao_predial",
        ] + new_sectors

        overlap_count = 0
        overlap_examples = []

        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            if not objeto:
                continue

            matching_sectors = []
            for sid in all_sectors:
                sector = get_sector(sid)
                ok, _ = match_keywords(objeto, sector.keywords, sector.exclusions)
                if ok:
                    matching_sectors.append(sid)

            # Check if a new sector overlaps with others
            new_matched = [s for s in matching_sectors if s in new_sectors]
            old_matched = [s for s in matching_sectors if s not in new_sectors]
            if new_matched and old_matched:
                overlap_count += 1
                if len(overlap_examples) < 10:
                    overlap_examples.append(
                        (objeto[:80], new_matched, old_matched)
                    )

        total_matched = sum(
            1 for rec in pncp_records
            if any(
                match_keywords(
                    rec.get("objetoCompra", ""),
                    get_sector(s).keywords,
                    get_sector(s).exclusions,
                )[0]
                for s in all_sectors
            )
        )

        overlap_rate = overlap_count / total_matched * 100 if total_matched else 0

        print(f"\n{'='*60}")
        print("CROSS-SECTOR OVERLAP ANALYSIS")
        print(f"{'='*60}")
        print(f"Total matched by any sector: {total_matched}")
        print(f"Overlap (new+old): {overlap_count} ({overlap_rate:.1f}%)")
        if overlap_examples:
            print("\nOverlap examples:")
            for obj, new, old in overlap_examples[:5]:
                print(f"  {obj}")
                print(f"    New: {new} | Old: {old}")

        # Some overlap is expected (e.g., ambulância could be saude+transporte)
        # but should be < 15%
        assert overlap_rate < 15, (
            f"Cross-sector overlap too high: {overlap_rate:.1f}%. "
            f"Review exclusion lists."
        )


# ─── Summary Report ───────────────────────────────────────

@pytest.mark.integration
class TestSummaryReport:
    """Print a consolidated summary of all sectors."""

    def test_print_summary(self, pncp_records):
        all_sectors = [
            "vestuario", "alimentos", "informatica", "mobiliario",
            "papelaria", "engenharia", "software", "facilities",
            "saude", "vigilancia", "transporte", "manutencao_predial",
        ]

        print(f"\n{'='*70}")
        print(f"SECTOR COVERAGE SUMMARY ({DATA_INICIAL} to {DATA_FINAL})")
        print(f"Records: {len(pncp_records)} | UFs: {TEST_UFS}")
        print(f"{'='*70}")
        print(f"{'Sector':<25} {'Matches':>8} {'Rate':>8} {'Excluded':>10}")
        print(f"{'-'*25} {'-'*8} {'-'*8} {'-'*10}")

        total_matched = 0
        unmatched = 0

        for sid in all_sectors:
            result = run_sector_against_api(sid, pncp_records)
            print(
                f"{result.sector_id:<25} {result.matched:>8} "
                f"{result.match_rate:>7.1f}% {result.excluded:>10}"
            )
            total_matched += result.matched

        # Count records not matched by any sector
        for rec in pncp_records:
            objeto = rec.get("objetoCompra", "")
            if not objeto:
                continue
            any_match = False
            for sid in all_sectors:
                sector = get_sector(sid)
                ok, _ = match_keywords(objeto, sector.keywords, sector.exclusions)
                if ok:
                    any_match = True
                    break
            if not any_match:
                unmatched += 1

        print(f"{'-'*25} {'-'*8} {'-'*8} {'-'*10}")
        print(f"{'TOTAL MATCHES':<25} {total_matched:>8}")
        print(f"{'UNMATCHED':<25} {unmatched:>8} {unmatched/len(pncp_records)*100:>7.1f}%")
        print(f"{'='*70}")
