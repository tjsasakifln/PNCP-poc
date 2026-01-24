# PRD Técnico: BidIQ Uniformes — POC v0.2

**Versão:** 0.2
**Data:** Janeiro 2026
**Tipo:** Especificação técnica de implementação

---

## 1. ESCOPO FUNCIONAL

### 1.1 Fluxo de execução

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERFACE WEB                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Seleção de UFs (multi-select)                            │  │
│  │  [SC] [PR] [RS] [SP] [RJ] [MG] ... [Todos]               │  │
│  │                                                           │  │
│  │  Período: [Data Inicial] — [Data Final]                   │  │
│  │                                                           │  │
│  │  [🔍 Buscar Licitações]                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CAMADA DE INGESTÃO                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  PNCP API Client                                          │  │
│  │  - Retry com exponential backoff                          │  │
│  │  - Circuit breaker                                        │  │
│  │  - Paginação automática                                   │  │
│  │  - Rate limiting (respeitar 429)                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CAMADA DE FILTRAGEM                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Filtros sequenciais (fail-fast):                         │  │
│  │  1. UF ∈ UFs selecionadas                                 │  │
│  │  2. R$ 50.000 ≤ valor ≤ R$ 5.000.000                      │  │
│  │  3. match_keywords(objeto, KEYWORDS_UNIFORMES)            │  │
│  │  4. status = aberta (data_abertura > now)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CAMADA DE SAÍDA                             │
│  ┌────────────────────┐    ┌────────────────────────────────┐  │
│  │  Excel Generator   │    │  LLM Summary (GPT-4.1-nano)    │  │
│  │  - openpyxl        │    │  - Structured output           │  │
│  │  - Formatação      │    │  - Resumo executivo            │  │
│  │  - Auto-width      │    │  - Destaques por categoria     │  │
│  └────────────────────┘    └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        INTERFACE WEB                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  📊 Resumo (GPT-4.1-nano)                                 │  │
│  │  "Encontradas 23 licitações de uniformes totalizando      │  │
│  │   R$ 4.2M. Destaque: Prefeitura de Joinville com edital   │  │
│  │   de R$ 850k para uniformes escolares..."                 │  │
│  │                                                           │  │
│  │  [📥 Download Excel (23 licitações)]                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Parâmetros do sistema

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `VALOR_MIN` | R$ 50.000,00 | Eliminar micro-compras com baixo ROI |
| `VALOR_MAX` | R$ 5.000.000,00 | Limite operacional típico de PMEs |
| `MAX_DIAS_BUSCA` | 30 | Limitar carga na API |
| `TIMEOUT_REQUEST` | 30s | Tolerância para API lenta |
| `MAX_RETRIES` | 5 | Tentativas antes de falha definitiva |
| `BACKOFF_BASE` | 2s | Base do exponential backoff |
| `BACKOFF_MAX` | 60s | Teto do backoff |
| `PAGE_SIZE` | 500 | Máximo permitido pela API PNCP |

---

## 2. INTEGRAÇÃO PNCP

### 2.1 Endpoint utilizado

```
GET https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao
```

**Documentação oficial:** https://pncp.gov.br/api/consulta/swagger-ui/index.html

### 2.2 Parâmetros de request

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `dataInicial` | string (YYYY-MM-DD) | Sim | Data inicial de publicação |
| `dataFinal` | string (YYYY-MM-DD) | Sim | Data final de publicação |
| `uf` | string | Não | Sigla do estado (filtro server-side) |
| `pagina` | int | Sim | Página atual (1-indexed) |
| `tamanhoPagina` | int | Sim | Itens por página (max 500) |

### 2.3 Estrutura de resposta

```json
{
  "data": [
    {
      "codigoCompra": "12345678-0001-2026",
      "objetoCompra": "AQUISIÇÃO DE UNIFORMES ESCOLARES PARA REDE MUNICIPAL",
      "valorTotalEstimado": 850000.00,
      "valorTotalHomologado": null,
      "dataPublicacaoPncp": "2026-01-20T10:30:00",
      "dataAberturaProposta": "2026-02-15T09:00:00",
      "dataEncerramentoProposta": "2026-02-14T18:00:00",
      "modalidadeNome": "Pregão Eletrônico",
      "situacaoCompraNome": "Publicada",
      "uf": "SC",
      "municipio": "Joinville",
      "nomeOrgao": "Prefeitura Municipal de Joinville",
      "cnpjOrgao": "12.345.678/0001-90",
      "esferaId": "M",
      "linkSistemaOrigem": "https://compras.joinville.sc.gov.br/...",
      "linkPncp": "https://pncp.gov.br/app/editais/12345678-0001-2026"
    }
  ],
  "totalRegistros": 1523,
  "totalPaginas": 4,
  "paginaAtual": 1,
  "tamanhoPagina": 500,
  "temProximaPagina": true
}
```

### 2.4 Campos extraídos para processamento

| Campo API | Campo interno | Tipo | Nullable |
|-----------|---------------|------|----------|
| `codigoCompra` | `pncp_id` | string | Não |
| `objetoCompra` | `objeto` | string | Não |
| `valorTotalEstimado` | `valor` | float | Sim |
| `dataPublicacaoPncp` | `data_publicacao` | datetime | Não |
| `dataAberturaProposta` | `data_abertura` | datetime | Sim |
| `modalidadeNome` | `modalidade` | string | Sim |
| `situacaoCompraNome` | `situacao` | string | Sim |
| `uf` | `uf` | string | Não |
| `municipio` | `municipio` | string | Sim |
| `nomeOrgao` | `orgao` | string | Sim |
| `cnpjOrgao` | `cnpj_orgao` | string | Sim |
| `esferaId` | `esfera` | string | Sim |
| `linkPncp` | `link` | string | Não |

---

## 3. LÓGICA DE RETRY E RESILIÊNCIA

### 3.1 Estratégia de retry

```python
from dataclasses import dataclass
from enum import Enum
import time
import random

class RetryStrategy(Enum):
    EXPONENTIAL_BACKOFF = "exponential"
    LINEAR_BACKOFF = "linear"
    IMMEDIATE = "immediate"

@dataclass
class RetryConfig:
    max_retries: int = 5
    base_delay: float = 2.0        # segundos
    max_delay: float = 60.0        # segundos
    exponential_base: float = 2.0
    jitter: bool = True            # Adiciona randomização
    retryable_status_codes: tuple = (408, 429, 500, 502, 503, 504)
    retryable_exceptions: tuple = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.ChunkedEncodingError,
    )

def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calcula delay para próxima tentativa usando exponential backoff.

    Fórmula: min(base_delay * (exponential_base ^ attempt), max_delay)
    Com jitter: delay * random(0.5, 1.5)

    Exemplo com config padrão:
    - Attempt 0: 2s
    - Attempt 1: 4s
    - Attempt 2: 8s
    - Attempt 3: 16s
    - Attempt 4: 32s
    - Attempt 5: 60s (capped)
    """
    delay = min(
        config.base_delay * (config.exponential_base ** attempt),
        config.max_delay
    )

    if config.jitter:
        delay *= random.uniform(0.5, 1.5)

    return delay
```

### 3.2 Cliente HTTP resiliente

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Generator, Any
import logging

logger = logging.getLogger(__name__)

class PNCPClient:
    """Cliente resiliente para API do PNCP."""

    BASE_URL = "https://pncp.gov.br/api/consulta/v1"

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self.session = self._create_session()
        self._request_count = 0
        self._last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Cria sessão com retry automático via urllib3."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.base_delay,
            status_forcelist=self.config.retryable_status_codes,
            allowed_methods=["GET"],
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        session.headers.update({
            "User-Agent": "BidIQ-POC/0.2",
            "Accept": "application/json"
        })

        return session

    def _rate_limit(self):
        """Rate limiting básico: max 10 requests/segundo."""
        MIN_INTERVAL = 0.1  # 100ms entre requests

        elapsed = time.time() - self._last_request_time
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)

        self._last_request_time = time.time()
        self._request_count += 1

    def fetch_page(
        self,
        data_inicial: str,
        data_final: str,
        uf: str | None = None,
        pagina: int = 1,
        tamanho: int = 500
    ) -> dict:
        """
        Busca uma página de licitações.

        Raises:
            PNCPAPIError: Em caso de falha após todas as tentativas
            PNCPRateLimitError: Se rate limited (429) persistir
        """
        self._rate_limit()

        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": pagina,
            "tamanhoPagina": tamanho
        }

        if uf:
            params["uf"] = uf

        url = f"{self.BASE_URL}/contratacoes/publicacao"

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(f"Request {url} params={params} attempt={attempt}")

                response = self.session.get(
                    url,
                    params=params,
                    timeout=30
                )

                # Rate limit específico
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited. Aguardando {retry_after}s")
                    time.sleep(retry_after)
                    continue

                # Sucesso
                if response.status_code == 200:
                    return response.json()

                # Erro não-retryable
                if response.status_code not in self.config.retryable_status_codes:
                    raise PNCPAPIError(
                        f"API retornou status {response.status_code}: {response.text}"
                    )

                # Erro retryable - aguarda e tenta novamente
                delay = calculate_delay(attempt, self.config)
                logger.warning(
                    f"Erro {response.status_code}. "
                    f"Tentativa {attempt + 1}/{self.config.max_retries + 1}. "
                    f"Aguardando {delay:.1f}s"
                )
                time.sleep(delay)

            except self.config.retryable_exceptions as e:
                delay = calculate_delay(attempt, self.config)
                logger.warning(
                    f"Exceção {type(e).__name__}: {e}. "
                    f"Tentativa {attempt + 1}/{self.config.max_retries + 1}. "
                    f"Aguardando {delay:.1f}s"
                )
                time.sleep(delay)

        raise PNCPAPIError(
            f"Falha após {self.config.max_retries + 1} tentativas"
        )

    def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: list[str] | None = None,
        on_progress: callable = None
    ) -> Generator[dict, None, None]:
        """
        Busca todas as licitações com paginação automática.

        Args:
            data_inicial: Data inicial (YYYY-MM-DD)
            data_final: Data final (YYYY-MM-DD)
            ufs: Lista de UFs para filtrar (None = todas)
            on_progress: Callback(current_page, total_pages, items_so_far)

        Yields:
            dict: Cada licitação individualmente
        """
        # Se UFs específicas, fazer uma busca por UF (mais eficiente)
        if ufs:
            for uf in ufs:
                yield from self._fetch_by_uf(
                    data_inicial, data_final, uf, on_progress
                )
        else:
            yield from self._fetch_by_uf(
                data_inicial, data_final, None, on_progress
            )

    def _fetch_by_uf(
        self,
        data_inicial: str,
        data_final: str,
        uf: str | None,
        on_progress: callable
    ) -> Generator[dict, None, None]:
        """Busca paginada para uma UF específica ou todas."""
        pagina = 1
        total_paginas = None
        items_fetched = 0

        while True:
            response = self.fetch_page(
                data_inicial=data_inicial,
                data_final=data_final,
                uf=uf,
                pagina=pagina
            )

            data = response.get("data", [])
            total_paginas = response.get("totalPaginas", 1)
            total_registros = response.get("totalRegistros", 0)

            if on_progress:
                on_progress(pagina, total_paginas, items_fetched + len(data))

            for item in data:
                yield item
                items_fetched += 1

            # Verificar se há próxima página
            if not response.get("temProximaPagina", False):
                break

            if pagina >= total_paginas:
                break

            pagina += 1

        logger.info(
            f"UF={uf or 'TODAS'}: {items_fetched} licitações em {pagina} páginas"
        )


class PNCPAPIError(Exception):
    """Erro na comunicação com API do PNCP."""
    pass


class PNCPRateLimitError(PNCPAPIError):
    """Rate limit excedido."""
    pass
```

### 3.3 Tratamento de erros por tipo

| Código HTTP | Classificação | Ação |
|-------------|---------------|------|
| 200 | Sucesso | Processar resposta |
| 400 | Client error | Falhar imediatamente (bug no código) |
| 401/403 | Auth error | Falhar imediatamente (não esperado) |
| 404 | Not found | Falhar imediatamente (endpoint incorreto) |
| 408 | Timeout | Retry com backoff |
| 429 | Rate limit | Aguardar `Retry-After` header ou 60s |
| 500 | Server error | Retry com backoff |
| 502 | Bad gateway | Retry com backoff |
| 503 | Unavailable | Retry com backoff |
| 504 | Gateway timeout | Retry com backoff |

### 3.4 Circuit breaker (opcional, para uso futuro)

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Operação normal
    OPEN = "open"          # Bloqueando requests
    HALF_OPEN = "half_open"  # Testando recuperação

@dataclass
class CircuitBreaker:
    """
    Circuit breaker para proteger contra falhas cascata.

    Estados:
    - CLOSED: Operação normal, contando falhas
    - OPEN: Bloqueando requests, aguardando timeout
    - HALF_OPEN: Permitindo um request de teste
    """
    failure_threshold: int = 5
    recovery_timeout: int = 30  # segundos

    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = field(default=0)
    last_failure_time: datetime | None = field(default=None)

    def record_success(self):
        """Registra sucesso e reseta contadores."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        """Registra falha e potencialmente abre o circuito."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_execute(self) -> bool:
        """Verifica se request pode ser executado."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._recovery_timeout_elapsed():
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: permite um request de teste
        return True

    def _recovery_timeout_elapsed(self) -> bool:
        if not self.last_failure_time:
            return True

        elapsed = datetime.now() - self.last_failure_time
        return elapsed > timedelta(seconds=self.recovery_timeout)
```

---

## 4. MOTOR DE FILTRAGEM

### 4.1 Keywords de uniformes/fardamentos

```python
KEYWORDS_UNIFORMES: set[str] = {
    # Termos primários (alta precisão)
    "uniforme",
    "uniformes",
    "fardamento",
    "fardamentos",

    # Peças específicas
    "jaleco",
    "jalecos",
    "guarda-pó",
    "guarda-pós",
    "avental",
    "aventais",
    "colete",
    "coletes",
    "camiseta",
    "camisetas",
    "camisa polo",
    "camisas polo",
    "calça",
    "calças",
    "bermuda",
    "bermudas",
    "saia",
    "saias",
    "agasalho",
    "agasalhos",
    "jaqueta",
    "jaquetas",
    "boné",
    "bonés",
    "chapéu",
    "chapéus",
    "meia",
    "meias",

    # Contextos específicos
    "uniforme escolar",
    "uniforme hospitalar",
    "uniforme administrativo",
    "fardamento militar",
    "fardamento escolar",
    "roupa profissional",
    "vestuário profissional",
    "vestimenta",
    "vestimentas",

    # Composições comuns em editais
    "kit uniforme",
    "conjunto uniforme",
    "confecção de uniforme",
    "aquisição de uniforme",
    "fornecimento de uniforme"
}

# Termos de exclusão (evitar falsos positivos)
KEYWORDS_EXCLUSAO: set[str] = {
    "uniformização de procedimento",
    "uniformização de entendimento",
    "uniforme de trânsito",  # sinalização
    "padrão uniforme"        # contexto técnico
}
```

### 4.2 Algoritmo de matching

```python
import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Normaliza texto para matching.
    - Lowercase
    - Remove acentos
    - Remove pontuação excessiva
    - Normaliza espaços
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove acentos (NFD + remove combining chars)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # Normaliza espaços e pontuação
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def match_keywords(
    objeto: str,
    keywords: set[str],
    exclusions: set[str] | None = None
) -> tuple[bool, list[str]]:
    """
    Verifica se objeto contém keywords de uniformes.

    Returns:
        tuple: (match: bool, matched_keywords: list[str])
    """
    objeto_norm = normalize_text(objeto)

    # Verificar exclusões primeiro
    if exclusions:
        for exc in exclusions:
            if normalize_text(exc) in objeto_norm:
                return False, []

    # Buscar keywords
    matched = []
    for kw in keywords:
        kw_norm = normalize_text(kw)

        # Match por palavra completa (word boundary)
        pattern = rf"\b{re.escape(kw_norm)}\b"
        if re.search(pattern, objeto_norm):
            matched.append(kw)

    return len(matched) > 0, matched


def filter_licitacao(
    licitacao: dict,
    ufs_selecionadas: set[str],
    valor_min: float = 50_000.0,
    valor_max: float = 5_000_000.0
) -> tuple[bool, str | None]:
    """
    Aplica todos os filtros a uma licitação.

    Returns:
        tuple: (aprovada: bool, motivo_rejeicao: str | None)

    Filtros aplicados em ordem (fail-fast):
    1. UF válida
    2. Valor dentro da faixa
    3. Match de keywords
    4. Status aberto (data_abertura futura)
    """
    # 1. Filtro de UF
    uf = licitacao.get("uf", "")
    if uf not in ufs_selecionadas:
        return False, f"UF '{uf}' não selecionada"

    # 2. Filtro de valor
    valor = licitacao.get("valorTotalEstimado")
    if valor is None:
        return False, "Valor não informado"

    if not (valor_min <= valor <= valor_max):
        return False, f"Valor R$ {valor:,.2f} fora da faixa"

    # 3. Filtro de keywords
    objeto = licitacao.get("objetoCompra", "")
    match, keywords_found = match_keywords(
        objeto,
        KEYWORDS_UNIFORMES,
        KEYWORDS_EXCLUSAO
    )

    if not match:
        return False, "Não contém keywords de uniformes"

    # 4. Filtro de status (data abertura futura)
    data_abertura_str = licitacao.get("dataAberturaProposta")
    if data_abertura_str:
        try:
            data_abertura = datetime.fromisoformat(
                data_abertura_str.replace("Z", "+00:00")
            )
            if data_abertura < datetime.now(data_abertura.tzinfo):
                return False, "Prazo encerrado"
        except ValueError:
            pass  # Se não conseguir parsear, ignora este filtro

    return True, None


def filter_batch(
    licitacoes: list[dict],
    ufs_selecionadas: set[str],
    valor_min: float = 50_000.0,
    valor_max: float = 5_000_000.0
) -> tuple[list[dict], dict]:
    """
    Filtra batch de licitações e retorna estatísticas.

    Returns:
        tuple: (aprovadas: list[dict], stats: dict)
    """
    aprovadas = []
    stats = {
        "total": len(licitacoes),
        "aprovadas": 0,
        "rejeitadas_uf": 0,
        "rejeitadas_valor": 0,
        "rejeitadas_keyword": 0,
        "rejeitadas_prazo": 0,
        "rejeitadas_outros": 0
    }

    for lic in licitacoes:
        aprovada, motivo = filter_licitacao(
            lic, ufs_selecionadas, valor_min, valor_max
        )

        if aprovada:
            aprovadas.append(lic)
            stats["aprovadas"] += 1
        else:
            if "UF" in (motivo or ""):
                stats["rejeitadas_uf"] += 1
            elif "Valor" in (motivo or ""):
                stats["rejeitadas_valor"] += 1
            elif "keyword" in (motivo or ""):
                stats["rejeitadas_keyword"] += 1
            elif "Prazo" in (motivo or ""):
                stats["rejeitadas_prazo"] += 1
            else:
                stats["rejeitadas_outros"] += 1

    return aprovadas, stats
```

---

## 5. GERAÇÃO DE EXCEL

### 5.1 Estrutura da planilha

| Coluna | Campo | Formato | Largura |
|--------|-------|---------|---------|
| A | Código PNCP | Texto | 25 |
| B | Objeto | Texto (wrap) | 60 |
| C | Órgão | Texto | 40 |
| D | UF | Texto | 5 |
| E | Município | Texto | 20 |
| F | Valor Estimado | Moeda (R$) | 18 |
| G | Modalidade | Texto | 20 |
| H | Data Publicação | Data (DD/MM/YYYY) | 15 |
| I | Data Abertura | Data (DD/MM/YYYY HH:MM) | 18 |
| J | Situação | Texto | 15 |
| K | Link | Hyperlink | 50 |

### 5.2 Implementação

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.hyperlink import Hyperlink
from datetime import datetime
from io import BytesIO

def create_excel(licitacoes: list[dict]) -> BytesIO:
    """
    Gera planilha Excel formatada com licitações.

    Returns:
        BytesIO: Buffer com arquivo Excel pronto para download
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Licitações Uniformes"

    # === ESTILOS ===
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    cell_alignment = Alignment(vertical="top", wrap_text=True)
    currency_format = 'R$ #,##0.00'
    date_format = 'DD/MM/YYYY'
    datetime_format = 'DD/MM/YYYY HH:MM'

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # === HEADERS ===
    headers = [
        ("Código PNCP", 25),
        ("Objeto", 60),
        ("Órgão", 40),
        ("UF", 6),
        ("Município", 20),
        ("Valor Estimado", 18),
        ("Modalidade", 20),
        ("Publicação", 12),
        ("Abertura", 16),
        ("Situação", 15),
        ("Link", 15)
    ]

    for col, (header_name, width) in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width

    # Congelar header
    ws.freeze_panes = "A2"

    # === DADOS ===
    for row_idx, lic in enumerate(licitacoes, start=2):
        # A: Código PNCP
        ws.cell(row=row_idx, column=1, value=lic.get("codigoCompra", ""))

        # B: Objeto
        ws.cell(row=row_idx, column=2, value=lic.get("objetoCompra", ""))

        # C: Órgão
        ws.cell(row=row_idx, column=3, value=lic.get("nomeOrgao", ""))

        # D: UF
        ws.cell(row=row_idx, column=4, value=lic.get("uf", ""))

        # E: Município
        ws.cell(row=row_idx, column=5, value=lic.get("municipio", ""))

        # F: Valor (formatado como moeda)
        valor_cell = ws.cell(row=row_idx, column=6, value=lic.get("valorTotalEstimado"))
        valor_cell.number_format = currency_format

        # G: Modalidade
        ws.cell(row=row_idx, column=7, value=lic.get("modalidadeNome", ""))

        # H: Data Publicação
        data_pub = parse_datetime(lic.get("dataPublicacaoPncp"))
        pub_cell = ws.cell(row=row_idx, column=8, value=data_pub)
        if data_pub:
            pub_cell.number_format = date_format

        # I: Data Abertura
        data_abertura = parse_datetime(lic.get("dataAberturaProposta"))
        abertura_cell = ws.cell(row=row_idx, column=9, value=data_abertura)
        if data_abertura:
            abertura_cell.number_format = datetime_format

        # J: Situação
        ws.cell(row=row_idx, column=10, value=lic.get("situacaoCompraNome", ""))

        # K: Link (hyperlink)
        link = lic.get("linkPncp") or f"https://pncp.gov.br/app/editais/{lic.get('codigoCompra', '')}"
        link_cell = ws.cell(row=row_idx, column=11, value="Abrir")
        link_cell.hyperlink = link
        link_cell.font = Font(color="0563C1", underline="single")

        # Aplicar bordas e alinhamento em todas as células da linha
        for col in range(1, 12):
            cell = ws.cell(row=row_idx, column=col)
            cell.border = thin_border
            cell.alignment = cell_alignment

    # === LINHA DE TOTAIS ===
    total_row = len(licitacoes) + 2
    ws.cell(row=total_row, column=5, value="TOTAL:").font = Font(bold=True)

    total_cell = ws.cell(
        row=total_row,
        column=6,
        value=f"=SUM(F2:F{total_row - 1})"
    )
    total_cell.number_format = currency_format
    total_cell.font = Font(bold=True)

    # === METADATA (aba separada) ===
    ws_meta = wb.create_sheet("Metadata")
    ws_meta["A1"] = "Gerado em:"
    ws_meta["B1"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ws_meta["A2"] = "Total de licitações:"
    ws_meta["B2"] = len(licitacoes)
    ws_meta["A3"] = "Valor total estimado:"
    ws_meta["B3"] = sum(l.get("valorTotalEstimado", 0) or 0 for l in licitacoes)
    ws_meta["B3"].number_format = currency_format

    # Salvar em buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer


def parse_datetime(value: str | None) -> datetime | None:
    """Parse datetime string do PNCP."""
    if not value:
        return None

    try:
        # Formato ISO com timezone
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass

    try:
        # Formato sem timezone
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pass

    try:
        # Apenas data
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
```

### 5.3 Filename convention

```python
def generate_filename(ufs: list[str], data_inicial: str, data_final: str) -> str:
    """
    Gera nome do arquivo Excel.

    Formato: bidiq_uniformes_{UFs}_{data_inicial}_{data_final}.xlsx
    Exemplo: bidiq_uniformes_SC-PR-RS_2026-01-01_2026-01-20.xlsx
    """
    ufs_str = "-".join(sorted(ufs)) if len(ufs) <= 5 else f"{len(ufs)}UFs"
    return f"bidiq_uniformes_{ufs_str}_{data_inicial}_{data_final}.xlsx"
```

---

## 6. RESUMO VIA LLM

### 6.1 Configuração do modelo

| Parâmetro | Valor |
|-----------|-------|
| Model | `gpt-4.1-nano` |
| Temperature | 0.3 |
| Max tokens | 500 |
| Response format | Structured output (JSON) |

### 6.2 Schema de resposta

```python
from pydantic import BaseModel, Field

class ResumoLicitacoes(BaseModel):
    """Schema para resumo estruturado das licitações."""

    resumo_executivo: str = Field(
        description="Resumo em 2-3 frases sobre as oportunidades encontradas",
        max_length=500
    )

    total_oportunidades: int = Field(
        description="Número total de licitações"
    )

    valor_total: float = Field(
        description="Soma dos valores estimados em reais"
    )

    destaques: list[str] = Field(
        description="Lista de 3-5 destaques principais (maiores valores, prazos próximos)",
        max_length=5
    )

    distribuicao_uf: dict[str, int] = Field(
        description="Quantidade de licitações por UF"
    )

    alerta_urgencia: str | None = Field(
        default=None,
        description="Alerta se houver licitação com prazo < 7 dias"
    )
```

### 6.3 Implementação

```python
from openai import OpenAI
import json

def gerar_resumo(licitacoes: list[dict]) -> ResumoLicitacoes:
    """
    Gera resumo estruturado das licitações via GPT-4.1-nano.

    Args:
        licitacoes: Lista de licitações filtradas

    Returns:
        ResumoLicitacoes: Resumo estruturado
    """
    if not licitacoes:
        return ResumoLicitacoes(
            resumo_executivo="Nenhuma licitação de uniformes encontrada no período selecionado.",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            distribuicao_uf={},
            alerta_urgencia=None
        )

    # Preparar dados para o LLM (limitar para não exceder contexto)
    dados_resumidos = []
    for lic in licitacoes[:50]:  # Máximo 50 para não estourar tokens
        dados_resumidos.append({
            "objeto": lic.get("objetoCompra", "")[:200],
            "orgao": lic.get("nomeOrgao", ""),
            "uf": lic.get("uf", ""),
            "municipio": lic.get("municipio", ""),
            "valor": lic.get("valorTotalEstimado", 0),
            "abertura": lic.get("dataAberturaProposta", "")
        })

    client = OpenAI()

    system_prompt = """Você é um analista de licitações especializado em uniformes e fardamentos.
Analise as licitações fornecidas e gere um resumo executivo.

REGRAS:
- Seja direto e objetivo
- Destaque as maiores oportunidades por valor
- Alerte sobre prazos próximos (< 7 dias)
- Mencione a distribuição geográfica
- Use linguagem profissional, não técnica demais
- Valores sempre em reais (R$) formatados
"""

    user_prompt = f"""Analise estas {len(licitacoes)} licitações de uniformes/fardamentos e gere um resumo:

{json.dumps(dados_resumidos, ensure_ascii=False, indent=2)}

Data atual: {datetime.now().strftime("%d/%m/%Y")}
"""

    response = client.beta.chat.completions.parse(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=ResumoLicitacoes,
        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.parsed


def format_resumo_html(resumo: ResumoLicitacoes) -> str:
    """Formata resumo para exibição na interface."""

    html = f"""
    <div class="resumo-container">
        <p class="resumo-executivo">{resumo.resumo_executivo}</p>

        <div class="resumo-stats">
            <div class="stat">
                <span class="stat-value">{resumo.total_oportunidades}</span>
                <span class="stat-label">Licitações</span>
            </div>
            <div class="stat">
                <span class="stat-value">R$ {resumo.valor_total:,.2f}</span>
                <span class="stat-label">Valor Total</span>
            </div>
        </div>

        {"<div class='alerta-urgencia'>⚠️ " + resumo.alerta_urgencia + "</div>" if resumo.alerta_urgencia else ""}

        <div class="destaques">
            <h4>Destaques:</h4>
            <ul>
                {"".join(f"<li>{d}</li>" for d in resumo.destaques)}
            </ul>
        </div>
    </div>
    """

    return html
```

### 6.4 Fallback sem LLM

```python
def gerar_resumo_fallback(licitacoes: list[dict]) -> ResumoLicitacoes:
    """
    Gera resumo básico sem usar LLM (fallback em caso de falha).
    """
    if not licitacoes:
        return ResumoLicitacoes(
            resumo_executivo="Nenhuma licitação encontrada.",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            distribuicao_uf={},
            alerta_urgencia=None
        )

    total = len(licitacoes)
    valor_total = sum(l.get("valorTotalEstimado", 0) or 0 for l in licitacoes)

    # Distribuição por UF
    dist_uf = {}
    for lic in licitacoes:
        uf = lic.get("uf", "N/A")
        dist_uf[uf] = dist_uf.get(uf, 0) + 1

    # Top 3 por valor
    top_valor = sorted(
        licitacoes,
        key=lambda x: x.get("valorTotalEstimado", 0) or 0,
        reverse=True
    )[:3]

    destaques = [
        f"{l.get('nomeOrgao', 'N/A')}: R$ {l.get('valorTotalEstimado', 0):,.2f}"
        for l in top_valor
    ]

    # Verificar urgência
    alerta = None
    hoje = datetime.now()
    for lic in licitacoes:
        abertura = parse_datetime(lic.get("dataAberturaProposta"))
        if abertura and (abertura - hoje).days < 7:
            alerta = f"Licitação com prazo em menos de 7 dias: {lic.get('nomeOrgao', '')}"
            break

    return ResumoLicitacoes(
        resumo_executivo=f"Encontradas {total} licitações de uniformes totalizando R$ {valor_total:,.2f}.",
        total_oportunidades=total,
        valor_total=valor_total,
        destaques=destaques,
        distribuicao_uf=dist_uf,
        alerta_urgencia=alerta
    )
```

---

## 7. INTERFACE WEB

### 7.1 Stack frontend

| Componente | Tecnologia |
|------------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| State | React hooks (useState) |
| HTTP | fetch API |

### 7.2 Estrutura de páginas

```
app/
├── page.tsx           # Página única (SPA)
├── layout.tsx         # Layout base
├── loading.tsx        # Loading state
├── error.tsx          # Error boundary
└── api/
    ├── buscar/
    │   └── route.ts   # POST: buscar licitações
    └── download/
        └── route.ts   # GET: download Excel
```

### 7.3 Componente principal

```tsx
// app/page.tsx
"use client";

import { useState } from "react";

const UFS = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
  "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
  "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

interface Resumo {
  resumo_executivo: string;
  total_oportunidades: number;
  valor_total: number;
  destaques: string[];
  distribuicao_uf: Record<string, number>;
  alerta_urgencia: string | null;
}

interface BuscaResult {
  resumo: Resumo;
  download_id: string;
}

export default function HomePage() {
  const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(
    new Set(["SC", "PR", "RS"])
  );
  const [dataInicial, setDataInicial] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split("T")[0];
  });
  const [dataFinal, setDataFinal] = useState(() => {
    return new Date().toISOString().split("T")[0];
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BuscaResult | null>(null);

  const toggleUf = (uf: string) => {
    const newSet = new Set(ufsSelecionadas);
    if (newSet.has(uf)) {
      newSet.delete(uf);
    } else {
      newSet.add(uf);
    }
    setUfsSelecionadas(newSet);
  };

  const selecionarTodos = () => {
    setUfsSelecionadas(new Set(UFS));
  };

  const limparSelecao = () => {
    setUfsSelecionadas(new Set());
  };

  const buscar = async () => {
    if (ufsSelecionadas.size === 0) {
      setError("Selecione pelo menos um estado");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/buscar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ufs: Array.from(ufsSelecionadas),
          data_inicial: dataInicial,
          data_final: dataFinal
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message || "Erro ao buscar licitações");
      }

      const data = await response.json();
      setResult(data);

    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">
        BidIQ Uniformes
      </h1>

      {/* Seleção de UFs */}
      <section className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="font-medium">Estados de interesse:</label>
          <div className="space-x-2">
            <button
              onClick={selecionarTodos}
              className="text-sm text-blue-600 hover:underline"
            >
              Selecionar todos
            </button>
            <button
              onClick={limparSelecao}
              className="text-sm text-gray-600 hover:underline"
            >
              Limpar
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {UFS.map(uf => (
            <button
              key={uf}
              onClick={() => toggleUf(uf)}
              className={`px-3 py-1 rounded border transition-colors ${
                ufsSelecionadas.has(uf)
                  ? "bg-green-600 text-white border-green-600"
                  : "bg-white text-gray-700 border-gray-300 hover:border-green-400"
              }`}
            >
              {uf}
            </button>
          ))}
        </div>

        <p className="text-sm text-gray-500 mt-2">
          {ufsSelecionadas.size} estado(s) selecionado(s)
        </p>
      </section>

      {/* Período */}
      <section className="mb-6 flex gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Data inicial:
          </label>
          <input
            type="date"
            value={dataInicial}
            onChange={e => setDataInicial(e.target.value)}
            className="border rounded px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Data final:
          </label>
          <input
            type="date"
            value={dataFinal}
            onChange={e => setDataFinal(e.target.value)}
            className="border rounded px-3 py-2"
          />
        </div>
      </section>

      {/* Botão de busca */}
      <button
        onClick={buscar}
        disabled={loading || ufsSelecionadas.size === 0}
        className="w-full bg-green-600 text-white py-3 rounded font-medium
                   hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                   transition-colors"
      >
        {loading ? "Buscando..." : "🔍 Buscar Licitações de Uniformes"}
      </button>

      {/* Loading */}
      {loading && (
        <div className="mt-6 p-4 bg-gray-50 rounded">
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-4">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Consultando API do PNCP... isso pode levar alguns segundos.
          </p>
        </div>
      )}

      {/* Erro */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div className="mt-6 space-y-4">
          {/* Resumo LLM */}
          <div className="p-4 bg-green-50 border border-green-200 rounded">
            <p className="text-lg">{result.resumo.resumo_executivo}</p>

            <div className="flex gap-6 mt-4">
              <div>
                <span className="text-3xl font-bold text-green-700">
                  {result.resumo.total_oportunidades}
                </span>
                <span className="text-sm text-gray-600 block">licitações</span>
              </div>
              <div>
                <span className="text-3xl font-bold text-green-700">
                  R$ {result.resumo.valor_total.toLocaleString("pt-BR")}
                </span>
                <span className="text-sm text-gray-600 block">valor total</span>
              </div>
            </div>

            {result.resumo.alerta_urgencia && (
              <div className="mt-4 p-2 bg-yellow-100 border border-yellow-300 rounded text-yellow-800">
                ⚠️ {result.resumo.alerta_urgencia}
              </div>
            )}

            {result.resumo.destaques.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Destaques:</h4>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {result.resumo.destaques.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Download */}
          <a
            href={`/api/download?id=${result.download_id}`}
            download
            className="block w-full text-center bg-blue-600 text-white py-3 rounded
                       font-medium hover:bg-blue-700 transition-colors"
          >
            📥 Download Excel ({result.resumo.total_oportunidades} licitações)
          </a>
        </div>
      )}
    </main>
  );
}
```

### 7.4 API Route - Buscar

```typescript
// app/api/buscar/route.ts
import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";

// Cache temporário para downloads (em produção usar Redis)
const downloadCache = new Map<string, Buffer>();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ufs, data_inicial, data_final } = body;

    // Validações
    if (!ufs || !Array.isArray(ufs) || ufs.length === 0) {
      return NextResponse.json(
        { message: "Selecione pelo menos um estado" },
        { status: 400 }
      );
    }

    if (!data_inicial || !data_final) {
      return NextResponse.json(
        { message: "Período obrigatório" },
        { status: 400 }
      );
    }

    // Chamar backend Python (ou implementar direto se preferir)
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    const response = await fetch(`${backendUrl}/buscar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ufs, data_inicial, data_final })
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { message: error.detail || "Erro no backend" },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Cachear Excel para download
    const downloadId = randomUUID();
    downloadCache.set(downloadId, Buffer.from(data.excel_base64, "base64"));

    // Limpar cache após 10 minutos
    setTimeout(() => downloadCache.delete(downloadId), 10 * 60 * 1000);

    return NextResponse.json({
      resumo: data.resumo,
      download_id: downloadId
    });

  } catch (error) {
    console.error("Erro na busca:", error);
    return NextResponse.json(
      { message: "Erro interno do servidor" },
      { status: 500 }
    );
  }
}
```

### 7.5 API Route - Download

```typescript
// app/api/download/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json(
      { message: "ID obrigatório" },
      { status: 400 }
    );
  }

  const buffer = downloadCache.get(id);

  if (!buffer) {
    return NextResponse.json(
      { message: "Download expirado ou inválido" },
      { status: 404 }
    );
  }

  const filename = `bidiq_uniformes_${new Date().toISOString().split("T")[0]}.xlsx`;

  return new NextResponse(buffer, {
    headers: {
      "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Content-Length": buffer.length.toString()
    }
  });
}
```

---

## 8. BACKEND API (FASTAPI)

### 8.1 Estrutura

```
backend/
├── main.py            # Entrypoint FastAPI
├── config.py          # Configurações
├── pncp_client.py     # Cliente PNCP com retry
├── filter.py          # Motor de filtragem
├── excel.py           # Gerador Excel
├── llm.py             # Integração GPT
└── schemas.py         # Pydantic models
```

### 8.2 Endpoint principal

```python
# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import base64

app = FastAPI(title="BidIQ Uniformes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar em produção
    allow_methods=["POST"],
    allow_headers=["*"],
)

class BuscaRequest(BaseModel):
    ufs: list[str] = Field(..., min_length=1)
    data_inicial: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_final: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")

class BuscaResponse(BaseModel):
    resumo: ResumoLicitacoes
    excel_base64: str
    total_raw: int
    total_filtrado: int

@app.post("/buscar", response_model=BuscaResponse)
async def buscar_licitacoes(request: BuscaRequest):
    try:
        # 1. Buscar no PNCP
        client = PNCPClient()
        licitacoes_raw = list(client.fetch_all(
            data_inicial=request.data_inicial,
            data_final=request.data_final,
            ufs=request.ufs
        ))

        # 2. Filtrar
        licitacoes_filtradas, stats = filter_batch(
            licitacoes_raw,
            ufs_selecionadas=set(request.ufs),
            valor_min=50_000.0,
            valor_max=5_000_000.0
        )

        # 3. Gerar resumo via LLM
        try:
            resumo = gerar_resumo(licitacoes_filtradas)
        except Exception as e:
            logger.warning(f"Falha no LLM, usando fallback: {e}")
            resumo = gerar_resumo_fallback(licitacoes_filtradas)

        # 4. Gerar Excel
        excel_buffer = create_excel(licitacoes_filtradas)
        excel_base64 = base64.b64encode(excel_buffer.read()).decode()

        return BuscaResponse(
            resumo=resumo,
            excel_base64=excel_base64,
            total_raw=len(licitacoes_raw),
            total_filtrado=len(licitacoes_filtradas)
        )

    except PNCPAPIError as e:
        raise HTTPException(status_code=502, detail=f"Erro na API PNCP: {str(e)}")
    except Exception as e:
        logger.exception("Erro interno")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## 9. DEPENDÊNCIAS

### 9.1 Backend (requirements.txt)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
requests==2.31.0
urllib3==2.1.0
openpyxl==3.1.2
openai==1.10.0
python-dotenv==1.0.0
```

### 9.2 Frontend (package.json)

```json
{
  "name": "bidiq-uniformes",
  "version": "0.2.0",
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  },
  "devDependencies": {
    "@types/node": "20.11.0",
    "@types/react": "18.2.48",
    "autoprefixer": "10.4.17",
    "postcss": "8.4.33",
    "tailwindcss": "3.4.1",
    "typescript": "5.3.3"
  }
}
```

---

## 10. VARIÁVEIS DE AMBIENTE

```bash
# .env
OPENAI_API_KEY=sk-...

# Backend
BACKEND_PORT=8000
LOG_LEVEL=INFO

# PNCP Client
PNCP_TIMEOUT=30
PNCP_MAX_RETRIES=5
PNCP_BACKOFF_BASE=2
PNCP_BACKOFF_MAX=60

# LLM
LLM_MODEL=gpt-4.1-nano
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
```

---

## 11. ESTRUTURA FINAL DE DIRETÓRIOS

```
bidiq-uniformes-poc/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── pncp_client.py
│   ├── filter.py
│   ├── excel.py
│   ├── llm.py
│   ├── schemas.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── api/
│   │       ├── buscar/route.ts
│   │       └── download/route.ts
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 12. LOGGING E OBSERVABILIDADE

### 12.1 Configuração de logging

```python
# backend/config.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    """Configura logging estruturado."""

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

    # Silenciar logs verbosos de libs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

### 12.2 Métricas a coletar

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `pncp_requests_total` | Counter | Total de requests para PNCP |
| `pncp_requests_failed` | Counter | Requests que falharam após retries |
| `pncp_request_duration_seconds` | Histogram | Latência de requests |
| `licitacoes_fetched_total` | Counter | Total de licitações buscadas |
| `licitacoes_filtered_total` | Counter | Total após filtros |
| `excel_generation_duration_seconds` | Histogram | Tempo de geração do Excel |
| `llm_requests_total` | Counter | Chamadas ao GPT |
| `llm_request_duration_seconds` | Histogram | Latência do GPT |
| `llm_fallback_used` | Counter | Vezes que fallback foi usado |

---

## ANEXOS

### A. Mapeamento completo de campos PNCP

```python
PNCP_FIELD_MAP = {
    # Identificação
    "codigoCompra": "pncp_id",
    "numeroCompra": "numero",
    "anoCompra": "ano",

    # Objeto
    "objetoCompra": "objeto",
    "informacaoComplementar": "complemento",

    # Valores
    "valorTotalEstimado": "valor_estimado",
    "valorTotalHomologado": "valor_homologado",

    # Datas
    "dataPublicacaoPncp": "data_publicacao",
    "dataAberturaProposta": "data_abertura",
    "dataEncerramentoProposta": "data_encerramento",
    "dataInclusao": "data_inclusao",
    "dataAtualizacao": "data_atualizacao",

    # Órgão
    "nomeOrgao": "orgao_nome",
    "cnpjOrgao": "orgao_cnpj",
    "codigoUnidade": "unidade_codigo",
    "nomeUnidade": "unidade_nome",

    # Localização
    "uf": "uf",
    "municipio": "municipio",
    "codigoMunicipio": "municipio_codigo",

    # Classificação
    "modalidadeId": "modalidade_id",
    "modalidadeNome": "modalidade",
    "situacaoCompraId": "situacao_id",
    "situacaoCompraNome": "situacao",
    "esferaId": "esfera_id",  # M=Municipal, E=Estadual, F=Federal
    "poderId": "poder_id",    # E=Executivo, L=Legislativo, J=Judiciário

    # Links
    "linkSistemaOrigem": "link_origem",
    "linkPncp": "link_pncp"
}
```

### B. Códigos de modalidade PNCP

| ID | Nome |
|----|------|
| 1 | Leilão - Loss |
| 2 | Diálogo Competitivo |
| 3 | Concurso |
| 4 | Concorrência - Loss |
| 5 | Concorrência - Regime de Contratação Integrada |
| 6 | Pregão - Loss |
| 7 | Dispensa de Licitação |
| 8 | Inexigibilidade de Licitação |
| 9 | Manifestação de Interesse |
| 10 | Pré-qualificação |
| 11 | Credenciamento |
| 12 | Leilão |
| 13 | Concorrência |
| 14 | Pregão |

### C. Exemplo de resposta raw do PNCP

```json
{
  "data": [
    {
      "codigoCompra": "83614912000156-1-000001/2026",
      "numeroCompra": "000001/2026",
      "anoCompra": 2026,
      "objetoCompra": "REGISTRO DE PREÇOS PARA AQUISIÇÃO DE UNIFORMES ESCOLARES (CAMISETAS, CALÇAS, BERMUDAS E AGASALHOS) PARA ALUNOS DA REDE MUNICIPAL DE ENSINO",
      "informacaoComplementar": "Conforme especificações do Termo de Referência",
      "valorTotalEstimado": 487500.00,
      "valorTotalHomologado": null,
      "dataPublicacaoPncp": "2026-01-20T08:00:00Z",
      "dataAberturaProposta": "2026-02-05T09:00:00Z",
      "dataEncerramentoProposta": "2026-02-04T23:59:59Z",
      "modalidadeId": 6,
      "modalidadeNome": "Pregão - Loss",
      "situacaoCompraId": 1,
      "situacaoCompraNome": "Publicada",
      "nomeOrgao": "PREFEITURA MUNICIPAL DE EXEMPLO",
      "cnpjOrgao": "83.614.912/0001-56",
      "codigoUnidade": "1",
      "nomeUnidade": "SECRETARIA DE EDUCAÇÃO",
      "uf": "SC",
      "municipio": "Exemplo",
      "codigoMunicipio": "4205407",
      "esferaId": "M",
      "poderId": "E",
      "linkSistemaOrigem": "https://compras.exemplo.sc.gov.br/pregao/1",
      "linkPncp": "https://pncp.gov.br/app/editais/83614912000156-1-000001/2026"
    }
  ],
  "totalRegistros": 1,
  "totalPaginas": 1,
  "paginaAtual": 1,
  "tamanhoPagina": 500,
  "temProximaPagina": false
}
```

---

**Especificação técnica completa. Implementação estimada: 3-5 dias.**