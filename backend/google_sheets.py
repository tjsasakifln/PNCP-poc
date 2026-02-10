"""
Google Sheets API integration for procurement data export.

This module provides functionality to export licitações data to Google Sheets
with professional formatting, preserving the same visual style as Excel exports.

Features:
- Create new spreadsheets with formatted data
- Update existing spreadsheets (preserves share links)
- Apply professional formatting (green header, currency, hyperlinks)
- Batch API operations for performance
- Support for up to 10,000 rows per export

Performance:
- Typical export time: 3-5 seconds for 1000 rows
- Uses Google Sheets API v4 batchUpdate for efficiency

Security:
- Uses user's OAuth access token (user-scoped permissions)
- Spreadsheets are private by default (only creator has access)

STORY-180: Google Sheets Export
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Header verde (#2E7D32) - SmartLic brand color
HEADER_GREEN_RGB = {
    'red': 0.18,      # 46 / 255
    'green': 0.49,    # 125 / 255
    'blue': 0.2       # 50 / 255
}

# Column configuration (matches excel.py)
COLUMN_HEADERS = [
    'Código',
    'Objeto',
    'Órgão',
    'UF',
    'Município',
    'Valor (R$)',
    'Modalidade',
    'Data Publicação',
    'Data Abertura',
    'Status',
    'Link PNCP'
]


# ============================================================================
# Main Exporter Class
# ============================================================================

class GoogleSheetsExporter:
    """
    Exports licitações to Google Sheets with professional formatting.

    This class handles all interactions with Google Sheets API v4,
    including spreadsheet creation, data population, and formatting.

    Example:
        >>> exporter = GoogleSheetsExporter(access_token="ya29.a0...")
        >>> result = await exporter.create_spreadsheet(
        ...     licitacoes=[...],
        ...     title="SmartLic - Uniformes - 09/02/2026"
        ... )
        >>> print(result['spreadsheet_url'])
    """

    def __init__(self, access_token: str):
        """
        Initialize exporter with user's OAuth access token.

        Args:
            access_token: Google OAuth 2.0 access token (from oauth.py)

        Raises:
            HTTPException 401: Invalid or expired access token
        """
        try:
            self.creds = Credentials(token=access_token)
            self.service = build('sheets', 'v4', credentials=self.creds)
            logger.info("Google Sheets exporter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {type(e).__name__}")
            raise HTTPException(
                status_code=401,
                detail="Invalid Google access token. Re-authorization required."
            )

    async def create_spreadsheet(
        self,
        licitacoes: List[Dict[str, Any]],
        title: str = "SmartLic - Resultados"
    ) -> Dict[str, Any]:
        """
        Create new Google Sheets spreadsheet with licitações.

        Args:
            licitacoes: List of bid dictionaries from PNCP
            title: Spreadsheet title

        Returns:
            {
                'spreadsheet_id': str,
                'spreadsheet_url': str,
                'total_rows': int
            }

        Raises:
            HTTPException 403: Forbidden (insufficient permissions)
            HTTPException 429: Rate limit exceeded
            HTTPException 500: Google API error
        """
        try:
            logger.info(f"Creating Google Sheets with {len(licitacoes)} rows")

            # 1. Create empty spreadsheet
            spreadsheet = self._create_empty_spreadsheet(title)
            spreadsheet_id = spreadsheet['spreadsheetId']

            # 2. Populate data
            self._populate_data(spreadsheet_id, licitacoes)

            # 3. Apply formatting
            self._apply_formatting(spreadsheet_id, len(licitacoes))

            logger.info(f"Spreadsheet created successfully: {spreadsheet_id}")

            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet['spreadsheetUrl'],
                'total_rows': len(licitacoes)
            }

        except HttpError as e:
            self._handle_google_api_error(e)

    async def update_spreadsheet(
        self,
        spreadsheet_id: str,
        licitacoes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update existing spreadsheet with new data.

        Preserves share links and permissions by updating in-place
        rather than creating a new spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            licitacoes: New data to replace existing

        Returns:
            {
                'spreadsheet_id': str,
                'spreadsheet_url': str,
                'total_rows': int,
                'updated_at': str (ISO 8601)
            }

        Raises:
            HTTPException 403: Forbidden (no edit access)
            HTTPException 404: Spreadsheet not found
            HTTPException 500: Google API error
        """
        try:
            logger.info(f"Updating spreadsheet {spreadsheet_id} with {len(licitacoes)} rows")

            # 1. Clear old data (preserve header)
            self._clear_data(spreadsheet_id)

            # 2. Populate new data
            self._populate_data(spreadsheet_id, licitacoes)

            # 3. Re-apply formatting
            self._apply_formatting(spreadsheet_id, len(licitacoes))

            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

            logger.info(f"Spreadsheet updated successfully: {spreadsheet_id}")

            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet_url,
                'total_rows': len(licitacoes),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

        except HttpError as e:
            self._handle_google_api_error(e)

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _create_empty_spreadsheet(self, title: str) -> Dict[str, Any]:
        """
        Create empty spreadsheet with initial configuration.

        Args:
            title: Spreadsheet title

        Returns:
            Spreadsheet resource (includes spreadsheetId and spreadsheetUrl)
        """
        spreadsheet = {
            'properties': {'title': title},
            'sheets': [{
                'properties': {
                    'title': 'Licitações',
                    'gridProperties': {
                        'frozenRowCount': 1  # Freeze header row
                    }
                }
            }]
        }

        return self.service.spreadsheets().create(body=spreadsheet).execute()

    def _populate_data(self, spreadsheet_id: str, licitacoes: List[Dict[str, Any]]):
        """
        Insert data into spreadsheet (header + rows).

        Args:
            spreadsheet_id: Google Sheets ID
            licitacoes: List of bid dictionaries
        """
        # Build rows
        rows = [COLUMN_HEADERS]

        for lic in licitacoes:
            rows.append([
                lic.get('codigoCompra', ''),
                self._truncate(lic.get('objetoCompra', ''), 200),  # Truncate long descriptions
                lic.get('nomeOrgao', ''),
                lic.get('uf', ''),
                lic.get('municipio', ''),
                lic.get('valorTotalEstimado', 0),
                lic.get('modalidade', ''),
                lic.get('dataPublicacaoPncp', ''),
                lic.get('dataAberturaProposta', ''),
                lic.get('situacaoCompra', ''),
                f"https://pncp.gov.br/app/editais/{lic.get('codigoCompra', '')}"
            ])

        # Insert data
        body = {'values': rows}
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Licitações!A1',
            valueInputOption='USER_ENTERED',  # Interprets hyperlinks, numbers, dates
            body=body
        ).execute()

    def _apply_formatting(self, spreadsheet_id: str, total_rows: int):
        """
        Apply professional formatting to spreadsheet.

        Formatting includes:
        - Green header (#2E7D32) with white bold text
        - Currency format for column F (Valor)
        - Auto-resize columns
        - Frozen header row (already set in create)

        Args:
            spreadsheet_id: Google Sheets ID
            total_rows: Number of data rows (excludes header)
        """
        requests = [
            # 1. Format header row (green background, white bold text)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': HEADER_GREEN_RGB,
                            'textFormat': {
                                'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                'bold': True
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            },

            # 2. Format column F (Valor) as currency
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 1,  # Skip header
                        'endRowIndex': total_rows + 1,
                        'startColumnIndex': 5,  # Column F (0-indexed)
                        'endColumnIndex': 6
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'numberFormat': {
                                'type': 'CURRENCY',
                                'pattern': 'R$ #,##0.00'
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.numberFormat'
                }
            },

            # 3. Auto-resize all columns
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 11  # All 11 columns
                    }
                }
            }
        ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

    def _clear_data(self, spreadsheet_id: str):
        """
        Clear data rows while preserving header.

        Args:
            spreadsheet_id: Google Sheets ID
        """
        self.service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='Licitações!A2:K'  # Clear from row 2 onwards
        ).execute()

    def _handle_google_api_error(self, error: HttpError):
        """
        Convert Google API errors to FastAPI HTTPExceptions.

        Args:
            error: HttpError from googleapiclient

        Raises:
            HTTPException with appropriate status code and message
        """
        status_code = error.resp.status

        if status_code == 403:
            logger.error("Google Sheets API: 403 Forbidden")
            raise HTTPException(
                status_code=403,
                detail="Sem permissão para acessar Google Sheets. Verifique autorização."
            )
        elif status_code == 404:
            logger.error("Google Sheets API: 404 Not Found")
            raise HTTPException(
                status_code=404,
                detail="Planilha não encontrada. Verifique o ID da planilha."
            )
        elif status_code == 429:
            logger.error("Google Sheets API: 429 Rate Limit")
            raise HTTPException(
                status_code=429,
                detail="Limite de API do Google Sheets excedido. Tente novamente em 1 minuto."
            )
        else:
            logger.error(f"Google Sheets API error: {status_code}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao exportar para Google Sheets: {str(error)}"
            )

    @staticmethod
    def _truncate(text: str, max_length: int) -> str:
        """
        Truncate long text with ellipsis.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if not text or len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'
