"""
Lead Deduplicator - Manage lead history and prevent duplicates (AC10).

This module implements:
1. Load/save lead history (cnpj-history.json)
2. Filter out duplicate CNPJs
3. Update history with new leads
4. Track metadata (first_discovered, last_seen, times_discovered)

STORY-184: Lead Prospecting Workflow - AC10
"""

import logging
import json
from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime

from schemas_lead_prospecting import (
    LeadProfile,
    LeadHistory,
    LeadHistoryFile,
)

logger = logging.getLogger(__name__)


class LeadDeduplicator:
    """Manage lead history and prevent duplicate lead generation."""

    def __init__(self, history_file: str = "docs/leads/history/cnpj-history.json"):
        """
        Initialize lead deduplicator.

        Args:
            history_file: Path to lead history JSON file
        """
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def load_history(self) -> LeadHistoryFile:
        """
        Load lead history from JSON file.

        Returns:
            LeadHistoryFile object

        If file doesn't exist, returns empty history.
        """
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Convert datetime strings back to datetime objects
                data["last_updated"] = datetime.fromisoformat(
                    data["last_updated"].replace("Z", "+00:00")
                )
                for lead in data["leads"]:
                    lead["first_discovered"] = datetime.fromisoformat(
                        lead["first_discovered"].replace("Z", "+00:00")
                    )
                    lead["last_seen"] = datetime.fromisoformat(
                        lead["last_seen"].replace("Z", "+00:00")
                    )

                return LeadHistoryFile(**data)

            except Exception as e:
                logger.error(f"Failed to load history from {self.history_file}: {e}")
                return self._empty_history()
        else:
            return self._empty_history()

    def save_history(self, history: LeadHistoryFile):
        """
        Save lead history to JSON file.

        Args:
            history: LeadHistoryFile object to save
        """
        try:
            # Convert to dict with proper datetime serialization
            data = history.model_dump()

            # Convert datetime objects to ISO strings
            data["last_updated"] = data["last_updated"].isoformat().replace(
                "+00:00", "Z"
            )
            for lead in data["leads"]:
                lead["first_discovered"] = lead["first_discovered"].isoformat().replace(
                    "+00:00", "Z"
                )
                lead["last_seen"] = lead["last_seen"].isoformat().replace(
                    "+00:00", "Z"
                )

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"History saved to {self.history_file}")

        except Exception as e:
            logger.error(f"Failed to save history to {self.history_file}: {e}")

    def get_existing_cnpjs(self) -> Set[str]:
        """
        Get set of CNPJs already in history.

        Returns:
            Set of CNPJs (14 digits, no formatting)
        """
        history = self.load_history()
        return set(lead.cnpj for lead in history.leads)

    def filter_new_cnpjs(self, candidate_cnpjs: List[str]) -> List[str]:
        """
        Filter out CNPJs that already exist in history.

        Args:
            candidate_cnpjs: List of candidate CNPJs

        Returns:
            List of NEW CNPJs (not in history)
        """
        existing = self.get_existing_cnpjs()
        new_cnpjs = [cnpj for cnpj in candidate_cnpjs if cnpj not in existing]

        logger.info(
            f"Deduplication: {len(candidate_cnpjs)} candidates → "
            f"{len(existing)} in history → {len(new_cnpjs)} NEW"
        )

        return new_cnpjs

    def add_leads_to_history(self, new_leads: List[LeadProfile]) -> int:
        """
        Add new leads to history.

        Args:
            new_leads: List of LeadProfile objects to add

        Returns:
            Total number of leads in history after addition
        """
        history = self.load_history()

        now = datetime.utcnow()

        for lead in new_leads:
            # Create history entry
            history_entry = LeadHistory(
                cnpj=lead.cnpj,
                company_name=lead.company_name,
                first_discovered=now,
                last_seen=now,
                times_discovered=1,
                qualification_score=lead.qualification.overall_score,
                contact_made=False,
                converted=False,
                notes="",
            )

            history.leads.append(history_entry)

        # Update metadata
        history.last_updated = now
        history.total_leads = len(history.leads)

        # Save
        self.save_history(history)

        logger.info(
            f"Added {len(new_leads)} new leads to history (total: {history.total_leads})"
        )

        return history.total_leads

    def update_lead_status(
        self,
        cnpj: str,
        contact_made: Optional[bool] = None,
        converted: Optional[bool] = None,
        notes: Optional[str] = None,
    ):
        """
        Update status of existing lead in history.

        Args:
            cnpj: CNPJ to update
            contact_made: Set contact_made status
            converted: Set converted status
            notes: Add/update notes
        """
        history = self.load_history()

        # Find lead
        for lead in history.leads:
            if lead.cnpj == cnpj:
                if contact_made is not None:
                    lead.contact_made = contact_made
                if converted is not None:
                    lead.converted = converted
                if notes is not None:
                    lead.notes = notes

                lead.last_seen = datetime.utcnow()
                break
        else:
            logger.warning(f"CNPJ {cnpj} not found in history")
            return

        # Save
        history.last_updated = datetime.utcnow()
        self.save_history(history)

        logger.info(f"Updated lead status for CNPJ {cnpj}")

    def _empty_history(self) -> LeadHistoryFile:
        """Create empty history object."""
        return LeadHistoryFile(
            version="1.0",
            last_updated=datetime.utcnow(),
            total_leads=0,
            leads=[],
        )
