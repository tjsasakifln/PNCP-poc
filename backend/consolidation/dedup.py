"""Deduplication engine for multi-source procurement records.

TD-008: Extracted from consolidation.py as part of DEBT-07 module split.
Contains DeduplicationEngine with all dedup layers (exact, fuzzy, process,
title-prefix) and merge-enrichment logic.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional

from clients.base import UnifiedProcurement
from config import DEDUP_FUZZY_ENABLED, DEDUP_FUZZY_THRESHOLD
from metrics import DEDUP_FIELDS_MERGED, DEDUP_FUZZY_HITS

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """
    Runs all deduplication layers against a list of UnifiedProcurement records.

    Features:
    - source_id dedup (same PNCP ID from datalake + live API)
    - dedup_key exact dedup (highest-priority source wins, merge-enrichment)
    - Fuzzy Jaccard dedup (same procurement, different edital numbers)
    - Process-number dedup (adjacent sequential editals from same org)
    - Title-prefix dedup (cross-org duplicates)
    """

    # HARDEN-006: Fields eligible for merge-enrichment from lower-priority duplicate
    _MERGE_FIELDS = ("valor_estimado", "modalidade", "orgao", "objeto")

    # Portuguese stopwords irrelevant for tender object comparison
    _FUZZY_STOPWORDS = frozenset({
        "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
        "para", "por", "com", "e", "a", "o", "um", "uma", "ao", "pelo",
        "pela", "que", "se", "ou", "os", "as", "este", "esta", "essa",
    })

    _LOT_PATTERN = re.compile(
        r'\b(?:lote|item|grupo|lotes?)\s*(?:n[.ºo°]?\s*)?(\d+)\b',
        re.IGNORECASE,
    )

    # Process-number pattern — PNCP source_id format:
    # "{cnpj}-{seq}-{edital_number}/{year}" e.g. "12345678000195-2026-000065/2026"
    _PROCESS_NUMBER_PATTERN = re.compile(r"-(\d{4,6})/(\d{4})$")

    def __init__(
        self,
        adapters: Dict,
        fuzzy_enabled: Optional[bool] = None,
        fuzzy_threshold: Optional[float] = None,
    ):
        """
        Args:
            adapters: Dict mapping source code to SourceAdapter instance.
                      Used to determine source priority for winner selection.
            fuzzy_enabled: Override for DEDUP_FUZZY_ENABLED (default from config env).
                           When False the three fuzzy layers are skipped; only
                           source_id + dedup_key exact passes run.
            fuzzy_threshold: Override for DEDUP_FUZZY_THRESHOLD (default from config env).
                             Jaccard similarity floor applied in the fuzzy + title-prefix
                             layers. Lower = more aggressive; higher = safer.
        """
        self._adapters = adapters
        self._fuzzy_enabled = (
            DEDUP_FUZZY_ENABLED if fuzzy_enabled is None else fuzzy_enabled
        )
        self._fuzzy_threshold = (
            DEDUP_FUZZY_THRESHOLD if fuzzy_threshold is None else fuzzy_threshold
        )

    def run(self, records: List[UnifiedProcurement]) -> List[UnifiedProcurement]:
        """Run all dedup layers in sequence and return deduplicated records."""
        deduped = self._deduplicate_by_source_id(records)
        deduped = self._deduplicate(deduped)
        if self._fuzzy_enabled:
            deduped = self._deduplicate_fuzzy(deduped)
            deduped = self._deduplicate_by_process_number(deduped)
            deduped = self._deduplicate_by_title_prefix(deduped)
        return deduped

    def _get_source_priority(self) -> Dict[str, int]:
        """Build source priority lookup from adapters (lower = higher priority)."""
        source_priority = {}
        for code, adapter in self._adapters.items():
            adapter_code = getattr(adapter, "code", code)
            adapter_meta = getattr(adapter, "metadata", None)
            if adapter_meta is not None:
                source_priority[adapter_code] = adapter_meta.priority
        return source_priority

    def _deduplicate_by_source_id(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """ISSUE-027: Deduplicate by source_id when same ID appears from multiple paths.

        When datalake and live API return the same bid, they share the same
        source_id (e.g., PNCP contract ID). This layer catches those before
        the more expensive dedup_key-based dedup runs.
        """
        if not records:
            return []

        seen: Dict[str, UnifiedProcurement] = {}
        no_id: list[UnifiedProcurement] = []

        for record in records:
            sid = record.source_id
            if not sid:
                no_id.append(record)
                continue

            existing = seen.get(sid)
            if existing is None:
                seen[sid] = record
            else:
                existing_priority = getattr(
                    getattr(self._adapters.get(existing.source_name), "metadata", None),
                    "priority", 999,
                )
                new_priority = getattr(
                    getattr(self._adapters.get(record.source_name), "metadata", None),
                    "priority", 999,
                )
                if new_priority < existing_priority:
                    seen[sid] = record

        result = list(seen.values()) + no_id
        removed = len(records) - len(result)
        if removed > 0:
            logger.info(f"[DEDUP] source_id dedup removed {removed} duplicates")
        return result

    def _deduplicate(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """
        Deduplicate records by dedup_key with merge-enrichment.

        Priority is determined by SourceMetadata.priority (lower = higher priority).
        The winner record is enriched with non-empty fields from the loser when
        the winner's field is empty/zero (HARDEN-006).
        """
        if not records:
            return []

        source_priority = self._get_source_priority()

        seen: Dict[str, UnifiedProcurement] = {}
        for record in records:
            key = record.dedup_key
            if not key:
                seen[f"_nokey_{id(record)}"] = record
                continue

            existing = seen.get(key)
            if existing is None:
                seen[key] = record
            else:
                # AC17: Log warning if same procurement has >5% value discrepancy
                if (
                    existing.source_name != record.source_name
                    and existing.valor_estimado > 0
                    and record.valor_estimado > 0
                ):
                    diff_pct = abs(existing.valor_estimado - record.valor_estimado) / max(
                        existing.valor_estimado, record.valor_estimado
                    )
                    if diff_pct > 0.05:
                        logger.warning(
                            f"[CONSOLIDATION] Value discrepancy >5% for dedup_key={key}: "
                            f"{existing.source_name}=R${existing.valor_estimado:,.2f} vs "
                            f"{record.source_name}=R${record.valor_estimado:,.2f} "
                            f"(diff={diff_pct:.1%})"
                        )

                existing_priority = source_priority.get(existing.source_name, 999)
                new_priority = source_priority.get(record.source_name, 999)
                if new_priority < existing_priority:
                    winner, loser = record, existing
                    seen[key] = record
                else:
                    winner, loser = existing, record

                self._merge_enrich(winner, loser, key)

        return list(seen.values())

    def _merge_enrich(
        self,
        winner: UnifiedProcurement,
        loser: UnifiedProcurement,
        dedup_key: str,
    ) -> None:
        """Enrich winner with non-empty fields from loser (HARDEN-006 AC1/AC2/AC3)."""
        for field_name in self._MERGE_FIELDS:
            winner_val = getattr(winner, field_name, None)
            loser_val = getattr(loser, field_name, None)

            winner_empty = (
                winner_val is None
                or winner_val == ""
                or (isinstance(winner_val, (int, float)) and winner_val == 0)
            )
            loser_has = (
                loser_val is not None
                and loser_val != ""
                and not (isinstance(loser_val, (int, float)) and loser_val == 0)
            )

            if winner_empty and loser_has:
                setattr(winner, field_name, loser_val)
                winner.merged_from[field_name] = loser.source_name
                # Lazy import via facade so patch("consolidation.DEDUP_FIELDS_MERGED") works (AC2)
                import consolidation as _consolidation
                _consolidation.DEDUP_FIELDS_MERGED.labels(field=field_name).inc()
                logger.debug(
                    f"[DEDUP-MERGE] key={dedup_key} field={field_name} "
                    f"filled from {loser.source_name} (winner={winner.source_name})"
                )

    @staticmethod
    def _tokenize_objeto(texto: str) -> frozenset:
        """Tokenize and normalize procurement object for Jaccard similarity.

        ISSUE-027 fix: Strip accents (NFD + remove combining marks) before
        tokenizing so that "contratação" and "contratacao" produce the same token.
        """
        import unicodedata

        texto = texto.lower()
        texto = "".join(
            c
            for c in unicodedata.normalize("NFD", texto)
            if unicodedata.category(c) != "Mn"
        )
        texto = re.sub(r"[^\w\s]", " ", texto)
        return frozenset(
            t for t in texto.split()
            if len(t) > 2 and t not in DeduplicationEngine._FUZZY_STOPWORDS
        )

    @staticmethod
    def _jaccard(a: frozenset, b: frozenset) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    @staticmethod
    def _extract_edital_number(source_id: str) -> int | None:
        """Extract numeric edital number from source_id for proximity comparison."""
        match = re.search(r"/(\d{4,6})/", source_id or "")
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def _extract_lot_number(obj_text: str) -> str | None:
        """Extract lot/item/group number from objetoCompra text.

        ISSUE-027: Bids with the same object but different lot numbers are
        legitimate separate procurements and must NOT be deduplicated.
        """
        m = DeduplicationEngine._LOT_PATTERN.search(obj_text or "")
        return m.group(1) if m else None

    def _deduplicate_fuzzy(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """Second dedup layer: same procurement with different edital numbers.

        Blocking: group by cnpj_orgao (avoids O(n²) global comparisons).
        Match: Jaccard >= 0.85 on objeto tokens AND valor within 5%.
        Winner: higher-priority source, or first encountered if same priority.
        """
        if len(records) < 2:
            return records

        blocks: Dict[str, List[int]] = defaultdict(list)
        for idx, rec in enumerate(records):
            cnpj = re.sub(r"[^\d]", "", rec.cnpj_orgao or "")
            if cnpj and len(cnpj) < 14:
                cnpj = cnpj.zfill(14)
            if cnpj:
                blocks[cnpj].append(idx)

        to_remove: set = set()
        removed_count = 0
        tokens_cache: Dict[int, frozenset] = {}

        for cnpj, indices in blocks.items():
            if len(indices) < 2:
                continue

            for i_pos in range(len(indices)):
                idx_a = indices[i_pos]
                if idx_a in to_remove:
                    continue

                if idx_a not in tokens_cache:
                    tokens_cache[idx_a] = self._tokenize_objeto(records[idx_a].objeto)

                for j_pos in range(i_pos + 1, len(indices)):
                    idx_b = indices[j_pos]
                    if idx_b in to_remove:
                        continue

                    if idx_b not in tokens_cache:
                        tokens_cache[idx_b] = self._tokenize_objeto(records[idx_b].objeto)

                    sim = self._jaccard(tokens_cache[idx_a], tokens_cache[idx_b])
                    if sim < 0.70:
                        continue

                    lot_a_diag = self._extract_lot_number(records[idx_a].objeto)
                    lot_b_diag = self._extract_lot_number(records[idx_b].objeto)
                    logger.debug(
                        f"[FUZZY-DEDUP-DIAG] sim={sim:.3f} lot_a={lot_a_diag} lot_b={lot_b_diag} "
                        f"val_a={records[idx_a].valor_estimado} val_b={records[idx_b].valor_estimado} "
                        f"src_a={records[idx_a].source_id[:40]} src_b={records[idx_b].source_id[:40]}"
                    )

                    lot_a = lot_a_diag
                    lot_b = lot_b_diag
                    if sim >= self._fuzzy_threshold and lot_a is not None and lot_b is not None and lot_a != lot_b:
                        continue

                    if lot_a is not None:
                        records[idx_a]._lot_number = lot_a  # type: ignore[attr-defined]
                    if lot_b is not None:
                        records[idx_b]._lot_number = lot_b  # type: ignore[attr-defined]

                    if lot_a is None and lot_b is None:
                        num_a = self._extract_edital_number(records[idx_a].source_id)
                        num_b = self._extract_edital_number(records[idx_b].source_id)
                        if (
                            num_a is not None
                            and num_b is not None
                            and abs(num_a - num_b) <= 3
                            and sim >= 0.60
                        ):
                            to_remove.add(idx_b)
                            DEDUP_FUZZY_HITS.labels(layer="fuzzy").inc()
                            removed_count += 1
                            logger.info(
                                f"[FUZZY-DEDUP] Collapsed sequential lot (Jaccard={sim:.2f}): "
                                f"cnpj={cnpj}, kept={records[idx_a].source_id}, "
                                f"removed={records[idx_b].source_id} "
                                f"(edital_nums={num_a}/{num_b}, gap={abs(num_a - num_b)})"
                            )
                            continue

                    val_a = records[idx_a].valor_estimado or 0
                    val_b = records[idx_b].valor_estimado or 0
                    if val_a > 0 and val_b > 0:
                        diff = abs(val_a - val_b) / max(val_a, val_b)
                        value_threshold = 0.20 if sim >= self._fuzzy_threshold else 0.05
                        if diff > value_threshold:
                            continue

                    if sim < self._fuzzy_threshold:
                        num_a = self._extract_edital_number(records[idx_a].source_id)
                        num_b = self._extract_edital_number(records[idx_b].source_id)
                        if num_a is not None and num_b is not None:
                            if abs(num_a - num_b) > 5:
                                continue
                        else:
                            continue

                    to_remove.add(idx_b)
                    DEDUP_FUZZY_HITS.labels(layer="fuzzy").inc()
                    removed_count += 1
                    logger.info(
                        f"[FUZZY-DEDUP] Merged duplicate (Jaccard={sim:.2f}): "
                        f"cnpj={cnpj}, kept={records[idx_a].source_id}, "
                        f"removed={records[idx_b].source_id}"
                    )

        if removed_count > 0:
            logger.info(
                f"[FUZZY-DEDUP] Removed {removed_count} fuzzy duplicates "
                f"from {len(records)} records"
            )

        return [rec for idx, rec in enumerate(records) if idx not in to_remove]

    @staticmethod
    def _extract_process_base(source_id: str, cnpj: str) -> str | None:
        """Return a (cnpj, year) key if this source_id looks like a PNCP edital."""
        if not source_id or not cnpj:
            return None
        m = DeduplicationEngine._PROCESS_NUMBER_PATTERN.search(source_id)
        if m:
            year = m.group(2)
            return f"{cnpj}|{year}"
        return None

    def _deduplicate_by_process_number(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """Third dedup layer: same org + same year with very similar objects.

        ISSUE-027: Addresses cases like "Amparo ETA V" appearing twice because
        PNCP returned adjacent edital numbers (/000065 and /000066) for the same
        procurement.
        """
        if len(records) < 2:
            return records

        groups: Dict[str, List[int]] = defaultdict(list)
        for idx, rec in enumerate(records):
            cnpj = re.sub(r"[^\d]", "", rec.cnpj_orgao or "")
            if cnpj and len(cnpj) < 14:
                cnpj = cnpj.zfill(14)
            base = self._extract_process_base(rec.source_id or "", cnpj)
            if base:
                groups[base].append(idx)

        source_priority = self._get_source_priority()
        to_remove: set = set()
        removed_count = 0
        tokens_cache: Dict[int, frozenset] = {}

        for base, indices in groups.items():
            if len(indices) < 2:
                continue

            for i_pos in range(len(indices)):
                idx_a = indices[i_pos]
                if idx_a in to_remove:
                    continue

                if idx_a not in tokens_cache:
                    tokens_cache[idx_a] = self._tokenize_objeto(records[idx_a].objeto)

                for j_pos in range(i_pos + 1, len(indices)):
                    idx_b = indices[j_pos]
                    if idx_b in to_remove:
                        continue

                    if idx_b not in tokens_cache:
                        tokens_cache[idx_b] = self._tokenize_objeto(records[idx_b].objeto)

                    sim = self._jaccard(tokens_cache[idx_a], tokens_cache[idx_b])
                    if sim < 0.80:
                        continue

                    lot_a = self._extract_lot_number(records[idx_a].objeto)
                    lot_b = self._extract_lot_number(records[idx_b].objeto)
                    if lot_a is not None and lot_b is not None and lot_a != lot_b:
                        continue

                    val_a = records[idx_a].valor_estimado or 0
                    val_b = records[idx_b].valor_estimado or 0
                    if val_a > 0 and val_b > 0:
                        diff = abs(val_a - val_b) / max(val_a, val_b)
                        if diff > 0.20:
                            continue

                    pri_a = source_priority.get(records[idx_a].source_name, 999)
                    pri_b = source_priority.get(records[idx_b].source_name, 999)
                    if pri_b < pri_a:
                        to_remove.add(idx_a)
                        DEDUP_FUZZY_HITS.labels(layer="process_number").inc()
                        removed_count += 1
                        logger.info(
                            f"[PROCESS-DEDUP] Merged duplicate (Jaccard={sim:.2f}): "
                            f"base={base}, kept={records[idx_b].source_id}, "
                            f"removed={records[idx_a].source_id}"
                        )
                        break
                    else:
                        to_remove.add(idx_b)
                        DEDUP_FUZZY_HITS.labels(layer="process_number").inc()
                        removed_count += 1
                        logger.info(
                            f"[PROCESS-DEDUP] Merged duplicate (Jaccard={sim:.2f}): "
                            f"base={base}, kept={records[idx_a].source_id}, "
                            f"removed={records[idx_b].source_id}"
                        )

        if removed_count > 0:
            logger.info(
                f"[PROCESS-DEDUP] Removed {removed_count} process-number duplicates "
                f"from {len(records)} records"
            )

        return [rec for idx, rec in enumerate(records) if idx not in to_remove]

    def _deduplicate_by_title_prefix(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """Fourth dedup layer: same title prefix across different orgs.

        ISSUE-027: Catches cross-org duplicates where the same procurement
        appears from PNCP and PCP with different CNPJs (e.g., consortia,
        republications). Blocks by first 60 chars of normalized objeto
        (avoids O(n²)). Within each block, dedup if Jaccard >= 0.85
        and valor within 20%.
        """
        if len(records) < 2:
            return records

        blocks: Dict[str, List[int]] = defaultdict(list)
        for idx, rec in enumerate(records):
            texto = re.sub(r"[^\w\s]", " ", (rec.objeto or "").lower())
            texto = " ".join(texto.split())
            prefix = texto[:60].strip()
            if prefix and len(prefix) > 15:
                blocks[prefix].append(idx)

        to_remove: set = set()
        tokens_cache: Dict[int, frozenset] = {}
        source_priority = self._get_source_priority()

        for prefix, indices in blocks.items():
            if len(indices) < 2:
                continue
            for i_pos in range(len(indices)):
                idx_a = indices[i_pos]
                if idx_a in to_remove:
                    continue
                if idx_a not in tokens_cache:
                    tokens_cache[idx_a] = self._tokenize_objeto(records[idx_a].objeto)

                for j_pos in range(i_pos + 1, len(indices)):
                    idx_b = indices[j_pos]
                    if idx_b in to_remove:
                        continue
                    if idx_b not in tokens_cache:
                        tokens_cache[idx_b] = self._tokenize_objeto(records[idx_b].objeto)

                    sim = self._jaccard(tokens_cache[idx_a], tokens_cache[idx_b])
                    if sim < self._fuzzy_threshold:
                        continue

                    lot_a = self._extract_lot_number(records[idx_a].objeto)
                    lot_b = self._extract_lot_number(records[idx_b].objeto)
                    if lot_a is not None and lot_b is not None and lot_a != lot_b:
                        continue

                    va = records[idx_a].valor_estimado or 0
                    vb = records[idx_b].valor_estimado or 0
                    if va > 0 and vb > 0:
                        diff = abs(va - vb) / max(va, vb)
                        if diff > 0.20:
                            continue

                    pa = source_priority.get(records[idx_a].source_name, 999)
                    pb = source_priority.get(records[idx_b].source_name, 999)
                    loser = idx_b if pa <= pb else idx_a
                    to_remove.add(loser)
                    DEDUP_FUZZY_HITS.labels(layer="title_prefix").inc()

        if to_remove:
            logger.info(
                f"[TITLE-PREFIX-DEDUP] Removed {len(to_remove)} cross-org duplicates"
            )
        return [r for i, r in enumerate(records) if i not in to_remove]
