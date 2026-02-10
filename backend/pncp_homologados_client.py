"""
PNCP Homologados Client - Query homologated (finalized) contracts.

This client queries the PNCP /contratos endpoint to find contracts that have
been signed/executed (homologated), as opposed to open bids.

STORY-184: Lead Prospecting Workflow
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from decimal import Decimal

from config import RetryConfig
from exceptions import PNCPAPIError
from schemas_lead_prospecting import ContractData

logger = logging.getLogger(__name__)


class PNCPHomologadosClient:
    """Client for querying PNCP homologated contracts."""

    BASE_URL = "https://pncp.gov.br/api/consulta/v1"

    def __init__(self, config: RetryConfig | None = None):
        """
        Initialize PNCP Homologados client.

        Args:
            config: Retry configuration (uses defaults if not provided)
        """
        self.config = config or RetryConfig()
        self.session = requests.Session()

    def buscar_homologadas(
        self,
        meses: int = 12,
        setores: Optional[List[str]] = None,
        pagina_inicial: int = 1,
        max_pages: Optional[int] = None,
    ) -> List[ContractData]:
        """
        Search for homologated contracts in the last N months.

        Args:
            meses: Number of months to look back (default 12)
            setores: Optional list of sector keywords for filtering
            pagina_inicial: Starting page number (default 1)
            max_pages: Maximum number of pages to fetch (default None = all)

        Returns:
            List of ContractData objects

        Raises:
            PNCPAPIError: If API request fails after retries
        """
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=meses * 30)

        logger.info(
            f"Querying PNCP homologated contracts from {data_inicial.date()} to {data_final.date()}"
        )

        contracts = []
        pagina = pagina_inicial

        while True:
            # Query page
            page_contracts = self._query_page(
                data_inicial=data_inicial.strftime("%Y%m%d"),
                data_final=data_final.strftime("%Y%m%d"),
                pagina=pagina,
            )

            if not page_contracts:
                break

            # Filter by sector keywords if provided
            if setores:
                page_contracts = self._filter_by_sector(page_contracts, setores)

            contracts.extend(page_contracts)

            logger.info(
                f"Page {pagina}: {len(page_contracts)} contracts (total: {len(contracts)})"
            )

            # Check if we should continue
            if max_pages and pagina >= max_pages:
                break

            # Check if there are more pages
            # (Note: PNCP API should indicate this in response metadata)
            pagina += 1

            # Safety limit: max 1000 pages (500k contracts)
            if pagina > 1000:
                logger.warning("Reached safety limit of 1000 pages")
                break

        logger.info(f"Total homologated contracts found: {len(contracts)}")
        return contracts

    def _query_page(
        self, data_inicial: str, data_final: str, pagina: int
    ) -> List[ContractData]:
        """
        Query a single page from PNCP /contratos endpoint.

        Args:
            data_inicial: Start date (YYYYMMDD)
            data_final: End date (YYYYMMDD)
            pagina: Page number

        Returns:
            List of ContractData objects from this page
        """
        endpoint = f"{self.BASE_URL}/contratos"
        params = {"dataInicial": data_inicial, "dataFinal": data_final, "pagina": pagina}

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract contracts
            raw_contracts = data.get("data", [])

            # Convert to ContractData objects
            contracts = []
            for raw in raw_contracts:
                try:
                    contract = self._parse_contract(raw)
                    contracts.append(contract)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse contract {raw.get('numeroControlePNCP', 'UNKNOWN')}: {e}"
                    )

            return contracts

        except requests.RequestException as e:
            raise PNCPAPIError(f"Failed to query PNCP /contratos: {e}")

    def _parse_contract(self, raw: Dict[str, Any]) -> ContractData:
        """
        Parse raw PNCP contract data into ContractData object.

        Args:
            raw: Raw contract data from PNCP API

        Returns:
            ContractData object
        """
        return ContractData(
            cnpj=raw["niFornecedor"],
            company_name=raw["nomeRazaoSocialFornecedor"],
            contract_value=Decimal(str(raw["valorInicial"])),
            contract_date=datetime.strptime(raw["dataAssinatura"], "%Y-%m-%d").date(),
            contract_object=raw["objetoContrato"],
            uf=raw["unidadeOrgao"]["ufSigla"],
            municipality=raw["unidadeOrgao"]["municipioNome"],
            contract_id=raw["numeroControlePNCP"],
        )

    def _filter_by_sector(
        self, contracts: List[ContractData], setores: List[str]
    ) -> List[ContractData]:
        """
        Filter contracts by sector keywords in objetoContrato.

        Args:
            contracts: List of contracts
            setores: List of sector names (e.g., ['uniformes', 'facilities'])

        Returns:
            Filtered list of contracts
        """
        # TODO: Load sector keywords from sectors.py
        # For now, simple keyword matching
        from filter import normalize_text

        filtered = []
        for contract in contracts:
            obj_normalized = normalize_text(contract.contract_object)
            for setor in setores:
                if setor.lower() in obj_normalized:
                    filtered.append(contract)
                    break

        return filtered
