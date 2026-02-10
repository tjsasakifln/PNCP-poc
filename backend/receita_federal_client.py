"""
Receita Federal Client - Query company data by CNPJ.

This client uses the ReceitaWS API (free public API) to enrich company data.

Rate Limit: 3 requests/minute (STRICT)
Caching Strategy: File-based cache (company data is static)

STORY-184: Lead Prospecting Workflow
"""

import logging
import time
import json
from typing import Optional, Dict
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from collections import deque

import requests

from schemas_lead_prospecting import CompanyData
from exceptions import PNCPAPIError


logger = logging.getLogger(__name__)


class ReceitaFederalAPIError(PNCPAPIError):
    """Receita Federal API error."""

    pass


class RateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, max_requests: int = 3, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default 60s)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    def wait_if_needed(self):
        """Block until a request slot is available."""
        now = time.time()

        # Remove requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # If at limit, wait for oldest request to age out
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 1
            if sleep_time > 0:
                logger.info(
                    f"Rate limit reached, waiting {sleep_time:.1f}s before next request"
                )
                time.sleep(sleep_time)

        # Record this request
        self.requests.append(time.time())


class CompanyDataCache:
    """File-based cache for company data."""

    def __init__(self, cache_dir: str = ".cache/receita_federal"):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, cnpj: str) -> Optional[CompanyData]:
        """
        Get cached company data.

        Args:
            cnpj: CNPJ (14 digits)

        Returns:
            CompanyData if cached, None otherwise
        """
        cache_file = self.cache_dir / f"{cnpj}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Convert date strings back to date objects
                if data.get("data_abertura"):
                    data["data_abertura"] = datetime.strptime(
                        data["data_abertura"], "%Y-%m-%d"
                    ).date()

                return CompanyData(**data)
            except Exception as e:
                logger.warning(f"Failed to load cache for CNPJ {cnpj}: {e}")
                return None
        return None

    def set(self, cnpj: str, company_data: CompanyData):
        """
        Cache company data.

        Args:
            cnpj: CNPJ (14 digits)
            company_data: CompanyData object to cache
        """
        cache_file = self.cache_dir / f"{cnpj}.json"
        try:
            # Convert to dict and handle date serialization
            data = company_data.model_dump()
            if isinstance(data.get("data_abertura"), date):
                data["data_abertura"] = data["data_abertura"].isoformat()

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Failed to cache data for CNPJ {cnpj}: {e}")


class ReceitaFederalClient:
    """Client for Receita Federal API (ReceitaWS)."""

    BASE_URL = "https://www.receitaws.com.br/v1/cnpj"

    def __init__(self, cache_dir: str = ".cache/receita_federal"):
        """
        Initialize Receita Federal client.

        Args:
            cache_dir: Directory for cache storage
        """
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(max_requests=3, time_window=60)
        self.cache = CompanyDataCache(cache_dir=cache_dir)

    def consultar_cnpj(self, cnpj: str) -> Optional[CompanyData]:
        """
        Query company data by CNPJ.

        Args:
            cnpj: CNPJ (14 digits, no formatting)

        Returns:
            CompanyData if successful, None if failed

        Raises:
            ReceitaFederalAPIError: If API returns error status
        """
        # Clean CNPJ
        cnpj_clean = cnpj.replace(".", "").replace("/", "").replace("-", "")

        # Check cache first
        cached = self.cache.get(cnpj_clean)
        if cached:
            logger.debug(f"Cache hit for CNPJ {cnpj_clean}")
            return cached

        # Rate limit before API call
        self.rate_limiter.wait_if_needed()

        # Query API
        endpoint = f"{self.BASE_URL}/{cnpj_clean}"

        try:
            response = self.session.get(endpoint, timeout=10)

            if response.status_code == 429:
                raise ReceitaFederalAPIError(
                    "Rate limit exceeded (429) - increase wait time"
                )

            if response.status_code != 200:
                logger.warning(
                    f"Receita Federal API error for CNPJ {cnpj_clean}: {response.status_code}"
                )
                return None

            data = response.json()

            # Check for API error
            if data.get("status") == "ERROR":
                logger.warning(
                    f"Receita Federal API returned error for CNPJ {cnpj_clean}: {data.get('message')}"
                )
                return None

            # Parse response
            company_data = self._parse_response(data)

            # Cache result
            self.cache.set(cnpj_clean, company_data)

            return company_data

        except requests.RequestException as e:
            logger.error(f"Request failed for CNPJ {cnpj_clean}: {e}")
            return None

    def _parse_response(self, data: Dict) -> CompanyData:
        """
        Parse ReceitaWS API response into CompanyData.

        Args:
            data: Raw API response

        Returns:
            CompanyData object
        """
        # Extract CNAE principal
        cnae_principal = None
        cnae_codigo = None
        if data.get("atividade_principal"):
            atividade = data["atividade_principal"][0]
            cnae_principal = atividade.get("text", "N/A")
            cnae_codigo = atividade.get("code", "N/A")

        return CompanyData(
            cnpj=data["cnpj"],
            razao_social=data["nome"],
            nome_fantasia=data.get("fantasia"),
            situacao=data["situacao"],
            porte=data.get("porte", "N/A"),
            capital_social=Decimal(
                str(data.get("capital_social", "0").replace(",", "."))
            ),
            cnae_principal=cnae_principal or "N/A",
            cnae_codigo=cnae_codigo or "N/A",
            data_abertura=datetime.strptime(data["abertura"], "%d/%m/%Y").date(),
            municipio=data["municipio"],
            uf=data["uf"],
            email=data.get("email"),
            telefone=data.get("telefone"),
        )

    def consultar_batch(
        self, cnpjs: list[str], progress_callback: Optional[callable] = None
    ) -> Dict[str, Optional[CompanyData]]:
        """
        Query multiple CNPJs with rate limiting.

        Args:
            cnpjs: List of CNPJs to query
            progress_callback: Optional callback(current, total, cnpj)

        Returns:
            Dict mapping CNPJ to CompanyData (None if failed)
        """
        results = {}
        total = len(cnpjs)

        for i, cnpj in enumerate(cnpjs, 1):
            if progress_callback:
                progress_callback(i, total, cnpj)

            results[cnpj] = self.consultar_cnpj(cnpj)

        return results
