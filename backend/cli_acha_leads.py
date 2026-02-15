"""
CLI wrapper for *acha-leads workflow integration with AIOS.

This script provides a command-line interface for the lead prospecting workflow,
compatible with AIOS task execution.

Usage:
    python cli_acha_leads.py [--sectors SECTOR1,SECTOR2] [--months N] [--min-score S]

Examples:
    python cli_acha_leads.py --sectors uniformes --months 12 --min-score 7.0
    python cli_acha_leads.py --sectors uniformes,facilities --months 6
    python cli_acha_leads.py
"""

import sys
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from lead_prospecting import execute_acha_leads


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Lead Prospecting Workflow - Find high-dependency companies from PNCP homologated contracts'
    )

    parser.add_argument(
        '--sectors',
        type=str,
        default=None,
        help='Comma-separated list of sectors (e.g., uniformes,facilities). Default: all'
    )

    parser.add_argument(
        '--months',
        type=int,
        default=12,
        help='Time window in months (default: 12)'
    )

    parser.add_argument(
        '--min-score',
        type=float,
        default=7.0,
        help='Minimum qualification score 0-10 (default: 7.0)'
    )

    parser.add_argument(
        '--skip-sanctions',
        action='store_true',
        default=False,
        help='Skip CEIS/CNEP sanctions check (useful for dev/debug)'
    )

    args = parser.parse_args()

    # Parse sectors
    sectors = args.sectors.split(',') if args.sectors else None

    # Print banner
    print("=" * 80)
    print("LEAD PROSPECTING WORKFLOW - *acha-leads")
    print("=" * 80)
    print(f"Sectors: {sectors or 'ALL'}")
    print(f"Time Window: {args.months} months")
    print(f"Min Score: {args.min_score}/10")
    print(f"Sanctions Check: {'SKIPPED' if args.skip_sanctions else 'ENABLED'}")
    print("=" * 80)
    print()

    try:
        # Execute workflow
        report_path = execute_acha_leads(
            sectors=sectors,
            months=args.months,
            min_score=args.min_score,
            skip_sanctions=args.skip_sanctions,
        )

        if report_path:
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print(f"Report generated: {report_path}")
            print()
            print("Next steps:")
            print("1. Review lead profiles in report")
            print("2. Generate Excel with current opportunities (SmartLic)")
            print("3. Send personalized messages + Excel to each lead")
            print("=" * 80)
            return 0
        else:
            print()
            print("=" * 80)
            print("NO NEW LEADS FOUND")
            print("=" * 80)
            print("All candidates are already in history.")
            print("Try different parameters or check lead history.")
            print("=" * 80)
            return 0

    except Exception as e:
        logger.exception("Workflow failed")
        print()
        print("=" * 80)
        print("ERROR!")
        print("=" * 80)
        print(f"Workflow failed: {e}")
        print("Check logs for details.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(main())
