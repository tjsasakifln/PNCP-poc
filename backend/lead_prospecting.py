"""
Lead Prospecting - Main orchestrator for *acha-leads workflow.

This module orchestrates the complete lead prospecting workflow:
1. Query PNCP homologated contracts
2. Extract unique CNPJs + aggregate by company
3. Deduplication (filter already-discovered leads)
4. Enrich with Receita Federal
5. Calculate dependency scores
6. Web search for contact data
7. Gather strategic intelligence
8. Generate personalized messages
9. Calculate qualification scores
10. Update history
11. Generate markdown report

STORY-184: Lead Prospecting Workflow
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from pncp_homologados_client import PNCPHomologadosClient
from receita_federal_client import ReceitaFederalClient
from lead_scorer import LeadScorer
from lead_deduplicator import LeadDeduplicator
from contact_searcher import ContactSearcher
from message_generator import MessageGenerator
from report_generator import ReportGenerator
from services.sanctions_service import SanctionsService

from schemas_lead_prospecting import (
    ContractData,
    CompanyData,
    LeadProfile,
)

logger = logging.getLogger(__name__)


def execute_acha_leads(
    sectors: Optional[List[str]] = None,
    months: int = 12,
    min_score: float = 7.0,
    skip_sanctions: bool = False,
) -> str:
    """
    Execute complete *acha-leads workflow.

    Args:
        sectors: List of target sectors (e.g., ['uniformes', 'facilities'])
        months: Time window in months (default 12)
        min_score: Minimum qualification score (default 7.0)
        skip_sanctions: Skip sanctions check (AC10, useful for dev/debug)

    Returns:
        Path to generated markdown report
    """
    start_time = datetime.now()
    logger.info(f"Starting *acha-leads workflow (sectors={sectors}, months={months}, min_score={min_score})")

    # Initialize clients
    pncp_client = PNCPHomologadosClient()
    receita_client = ReceitaFederalClient()
    scorer = LeadScorer()
    deduplicator = LeadDeduplicator()
    contact_searcher = ContactSearcher()
    message_gen = MessageGenerator()
    report_gen = ReportGenerator()

    # Step 1: Query PNCP homologated contracts
    logger.info("Step 1: Querying PNCP for homologated contracts...")
    contracts = pncp_client.buscar_homologadas(
        meses=months,
        setores=sectors,
        max_pages=100,  # Safety limit
    )
    logger.info(f"Found {len(contracts)} contracts from PNCP")

    if not contracts:
        logger.warning("No contracts found - aborting workflow")
        return None

    # Step 2: Group contracts by CNPJ
    logger.info("Step 2: Grouping contracts by CNPJ...")
    contracts_by_cnpj = defaultdict(list)
    for contract in contracts:
        contracts_by_cnpj[contract.cnpj].append(contract)

    all_cnpjs = list(contracts_by_cnpj.keys())
    logger.info(f"Found {len(all_cnpjs)} unique companies")

    # Step 3: Deduplication (AC10)
    logger.info("Step 3: Filtering out already-discovered leads...")
    new_cnpjs = deduplicator.filter_new_cnpjs(all_cnpjs)

    if not new_cnpjs:
        logger.warning("No new leads found - all CNPJs already in history")
        # Still generate report showing this
        report_path = report_gen.generate_empty_report(
            sectors=sectors,
            months=months,
            min_score=min_score,
            total_candidates=len(all_cnpjs),
            in_history=len(all_cnpjs),
        )
        return report_path

    logger.info(f"Processing {len(new_cnpjs)} NEW companies")

    # Step 4: Enrich with Receita Federal
    logger.info("Step 4: Enriching with Receita Federal data...")

    def progress_callback(current, total, cnpj):
        if current % 10 == 0 or current == total:
            logger.info(f"Receita Federal progress: {current}/{total}")

    company_data_map = receita_client.consultar_batch(
        new_cnpjs, progress_callback=progress_callback
    )
    logger.info(f"Enriched {sum(1 for v in company_data_map.values() if v)} companies")

    # Step 5: Check sanctions (STORY-256 AC6)
    sanctions_map: Dict[str, "SanctionsResult"] = {}
    sanctioned_cnpjs: List[str] = []

    if not skip_sanctions:
        logger.info("Step 5: Checking sanctions (CEIS + CNEP)...")
        import asyncio
        from clients.sanctions import SanctionsResult as _SR

        sanctions_service = SanctionsService()
        try:
            loop = asyncio.new_event_loop()
            reports_map = loop.run_until_complete(
                sanctions_service.check_companies(new_cnpjs)
            )
            loop.run_until_complete(sanctions_service.close())
            loop.close()

            for cnpj_key, report in reports_map.items():
                if report.status == "unavailable":
                    logger.warning(f"Sanctions check unavailable for {cnpj_key}")
                    continue
                # Convert CompanySanctionsReport back to SanctionsResult for schema
                from clients.sanctions import SanctionsResult
                sr = SanctionsResult(
                    cnpj=report.cnpj,
                    is_sanctioned=report.is_sanctioned,
                    sanctions=report.ceis_records + report.cnep_records,
                    checked_at=report.checked_at,
                    ceis_count=len(report.ceis_records),
                    cnep_count=len(report.cnep_records),
                    cache_hit=False,
                )
                sanctions_map[cnpj_key] = sr
                if report.is_sanctioned:
                    sanctioned_cnpjs.append(cnpj_key)
                    logger.info(
                        f"SANCTIONED: {cnpj_key} ({report.total_active_sanctions} active sanctions)"
                    )
        except Exception as exc:
            logger.warning(f"Sanctions check failed (graceful degradation): {exc}")

        logger.info(
            f"Sanctions check complete: {len(sanctioned_cnpjs)} sanctioned out of {len(new_cnpjs)}"
        )
    else:
        logger.info("Step 5: Sanctions check SKIPPED (--skip-sanctions)")

    # Step 6-10: Process each company
    logger.info("Step 6-10: Processing companies (scoring, contact search, messages)...")
    qualified_leads = []
    disqualified_sanctions = []

    for cnpj in new_cnpjs:
        company_data = company_data_map.get(cnpj)
        if not company_data:
            logger.warning(f"Skipping CNPJ {cnpj} - no company data")
            continue

        # AC8: Disqualify sanctioned companies (score × 0)
        sanctions_result = sanctions_map.get(cnpj)
        if sanctions_result and sanctions_result.is_sanctioned:
            disqualified_sanctions.append({
                "cnpj": cnpj,
                "company_name": company_data.razao_social,
                "ceis_count": sanctions_result.ceis_count,
                "cnep_count": sanctions_result.cnep_count,
                "reason": "Active sanctions (CEIS/CNEP)",
            })
            logger.info(f"Disqualified {cnpj} ({company_data.razao_social}) - active sanctions")
            continue

        company_contracts = contracts_by_cnpj[cnpj]

        # Step 6: Calculate dependency score
        dependency_score = scorer.calculate_dependency_score(
            contracts=company_contracts,
            company_data=company_data,
            time_window_months=months,
        )

        # Filter by dependency (≥70% for high-value leads)
        if dependency_score.dependency_level != "HIGH":
            continue

        # Step 6: Find contact data
        contact_data = contact_searcher.find_contact_data(
            company_name=company_data.razao_social,
            cnpj=cnpj,
            existing_data={
                "email": company_data.email,
                "telefone": company_data.telefone,
            },
        )

        # Step 7: Gather strategic intelligence
        sector = sectors[0] if sectors else "licitações públicas"
        intelligence = contact_searcher.gather_intelligence(
            company_name=company_data.razao_social,
            cnpj=cnpj,
            sector=sector,
        )

        # Step 8: Generate personalized message
        most_recent_contract = max(company_contracts, key=lambda c: c.contract_date)
        personalized_message = message_gen.generate_message(
            company_name=company_data.razao_social,
            sector=sector,
            recent_contract=most_recent_contract,
            intelligence=intelligence,
            dependency_percentage=dependency_score.dependency_percentage,
        )

        # Step 9: Calculate qualification score
        qualification = scorer.calculate_qualification_score(
            dependency_score=dependency_score,
            contracts=company_contracts,
            sectors=[sector],
            target_sectors=sectors or [],
            contact_data=contact_data,
        )

        # Filter by qualification score
        if qualification.overall_score < min_score:
            continue

        # Create lead profile
        lead = LeadProfile(
            cnpj=cnpj,
            company_name=company_data.razao_social,
            nome_fantasia=company_data.nome_fantasia,
            company_data=company_data,
            sanctions_check=sanctions_map.get(cnpj),
            is_sanctioned=False,  # If we got here, it's not sanctioned
            contracts=company_contracts,
            dependency_score=dependency_score,
            contact_data=contact_data,
            intelligence=intelligence,
            personalized_message=personalized_message,
            qualification=qualification,
            sectors=sectors or [],
        )

        qualified_leads.append(lead)

    logger.info(f"Qualified {len(qualified_leads)} leads (score >= {min_score})")

    # Step 10: Update history (AC10)
    if qualified_leads:
        logger.info("Step 10: Updating lead history...")
        total_in_history = deduplicator.add_leads_to_history(qualified_leads)
        logger.info(f"Total leads in history: {total_in_history}")

    # Step 11: Generate report
    logger.info("Step 11: Generating markdown report...")
    execution_time = datetime.now() - start_time

    report_path = report_gen.generate_report(
        leads=qualified_leads,
        sectors=sectors,
        months=months,
        min_score=min_score,
        execution_time=execution_time.total_seconds(),
        total_candidates=len(all_cnpjs),
        in_history=len(all_cnpjs) - len(new_cnpjs),
        new_processed=len(new_cnpjs),
        disqualified_sanctions=disqualified_sanctions,
    )

    logger.info(f"Workflow complete! Report: {report_path}")
    logger.info(f"Execution time: {execution_time.total_seconds():.1f}s")

    return report_path


if __name__ == "__main__":
    # CLI for testing
    import sys

    sectors_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sectors = sectors_arg.split(",") if sectors_arg else None

    report_path = execute_acha_leads(sectors=sectors)
    print(f"\nReport generated: {report_path}")
