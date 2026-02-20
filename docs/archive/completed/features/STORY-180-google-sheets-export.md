# STORY-180: Exportação Automática de Resultados para Google Sheets

**Status:** Aprovada
**Prioridade:** P1 - Alta (melhoria significativa de UX e produtividade)
**Estimativa:** 13 story points (2 sprints)
**Tipo:** Enhancement (Brownfield)
**Épico:** Integrações e Produtividade
**Dependências:** Nenhuma
**Aprovado por:** @pm (Morgan - Engineering Manager)

---

## Contexto

### Necessidade do Usuário

Atualmente, o SmartLic permite apenas **download de Excel (.xlsx)**, exigindo que o usuário:
1. Baixe o arquivo localmente
2. Abra manualmente no Google Sheets (se preferir)
3. Ou importe para o Google Drive

**Solicitação do cliente:**
> "Seria muito mais prático se eu pudesse exportar direto para o Google Sheets e compartilhar com minha equipe instantaneamente, sem precisar baixar e fazer upload manual."

### Benefícios da Integração Google Sheets

| Benefício | Descrição |
|-----------|-----------|
| **Colaboração Instantânea** | Compartilhar planilha com equipe em tempo real |
| **Acesso em qualquer lugar** | Cloud-first, não depende de desktop |
| **Versionamento automático** | Google Sheets mantém histórico de versões |
| **Integração com Google Workspace** | Usuários corporativos já vivem no ecossistema Google |
| **Sem downloads** | Fluxo mais rápido, especialmente em ambientes corporativos restritos |

### Casos de Uso Principais

1. **Analista de Compras:** Exporta resultados para Google Sheets e compartilha link com gerente de contratações
2. **Equipe de Licitações:** Cria planilha colaborativa para monitorar oportunidades e atribuir responsáveis
3. **Consultor de Negócios:** Exporta dados para Google Sheets e cria dashboards com fórmulas personalizadas

---

## Objetivos

### Objetivo Principal

Permitir que usuários exportem resultados de buscas diretamente para Google Sheets com um clique, eliminando passos manuais.

### Objetivos Secundários

- [ ] Manter compatibilidade com download Excel (não substituir, adicionar alternativa)
- [ ] Preservar formatação (cores, estilos, fórmulas) ao exportar para Google Sheets
- [ ] Fornecer link compartilhável instantâneo após exportação
- [ ] Permitir que usuário escolha: "Criar nova planilha" ou "Atualizar planilha existente"

---

## Requisitos Técnicos

### 1. Autenticação Google OAuth 2.0

**Fluxo de autenticação:**
```
User clica "Exportar para Google Sheets"
    ↓
Backend redireciona para Google OAuth consent screen
    ↓
User autoriza acesso ao Google Sheets
    ↓
Backend recebe `authorization_code`
    ↓
Backend troca code por `access_token` + `refresh_token`
    ↓
Backend armazena tokens no banco (criptografados)
```

**Escopo OAuth necessário:**
```
https://www.googleapis.com/auth/spreadsheets
```

**Implementação:**
- Biblioteca: `google-auth-oauthlib` (Python) ou `@google-cloud/local-auth` (Node.js)
- Armazenamento de tokens: Tabela `user_oauth_tokens` no Supabase
- Criptografia: AES-256 para `refresh_token` (nunca armazenar plain text)

### 2. Google Sheets API Integration

**API necessária:** Google Sheets API v4

**Principais operações:**

| Operação | Endpoint | Uso |
|----------|----------|-----|
| **Criar planilha** | `POST /v4/spreadsheets` | Criar nova spreadsheet |
| **Atualizar dados** | `PUT /v4/spreadsheets/{id}/values/{range}` | Inserir dados |
| **Aplicar formatação** | `POST /v4/spreadsheets/{id}:batchUpdate` | Estilos, cores, fórmulas |
| **Obter permissões** | Google Drive API `POST /v3/files/{id}/permissions` | Compartilhamento |

**Exemplo de criação de planilha:**
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials(token=user_access_token)
service = build('sheets', 'v4', credentials=creds)

spreadsheet = {
    'properties': {
        'title': 'SmartLic - Resultados Uniformes - 09/02/2026'
    },
    'sheets': [
        {
            'properties': {
                'title': 'Licitações',
                'gridProperties': {
                    'frozenRowCount': 1  # Freeze header
                }
            }
        }
    ]
}

result = service.spreadsheets().create(body=spreadsheet).execute()
spreadsheet_id = result['spreadsheetId']
spreadsheet_url = result['spreadsheetUrl']
```

### 3. Mapeamento de Formatação Excel → Google Sheets

| Elemento Excel | Google Sheets Equivalente |
|----------------|---------------------------|
| Header verde `#2E7D32` | `backgroundColor: { red: 0.18, green: 0.49, blue: 0.2 }` |
| Bold font | `textFormat: { bold: true }` |
| Currency format `R$` | `numberFormat: { type: 'CURRENCY', pattern: 'R$ #,##0.00' }` |
| Date format `DD/MM/YYYY` | `numberFormat: { type: 'DATE', pattern: 'dd/mm/yyyy' }` |
| Hyperlinks | `=HYPERLINK("url", "texto")` formula |
| Auto-width columns | `autoResizeDimensions` request |
| Frozen header | `frozenRowCount: 1` |

**Implementação de formatação (batch update):**
```python
requests = [
    {
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.18, 'green': 0.49, 'blue': 0.2},
                    'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True},
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    },
    {
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': 0,
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': 11
            }
        }
    }
]

service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={'requests': requests}
).execute()
```

### 4. Backend Architecture

**Novo módulo:** `backend/google_sheets.py`

```python
"""
Integração com Google Sheets API para exportação de licitações.
"""

from typing import Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsExporter:
    """Exportador de licitações para Google Sheets."""

    def __init__(self, access_token: str):
        """
        Args:
            access_token: OAuth 2.0 access token do usuário
        """
        self.creds = Credentials(token=access_token)
        self.service = build('sheets', 'v4', credentials=self.creds)

    async def create_spreadsheet(
        self,
        licitacoes: list[dict],
        title: str = "SmartLic - Resultados"
    ) -> dict[str, Any]:
        """
        Cria nova planilha no Google Sheets.

        Args:
            licitacoes: Lista de dicionários com dados das licitações
            title: Título da planilha

        Returns:
            {
                'spreadsheet_id': str,
                'spreadsheet_url': str,
                'total_rows': int
            }

        Raises:
            HttpError: Se falhar ao criar planilha (quota, auth, etc)
        """
        # 1. Criar planilha vazia
        spreadsheet = self._create_empty_spreadsheet(title)
        spreadsheet_id = spreadsheet['spreadsheetId']

        # 2. Inserir dados
        self._populate_data(spreadsheet_id, licitacoes)

        # 3. Aplicar formatação
        self._apply_formatting(spreadsheet_id, len(licitacoes))

        return {
            'spreadsheet_id': spreadsheet_id,
            'spreadsheet_url': spreadsheet['spreadsheetUrl'],
            'total_rows': len(licitacoes)
        }

    async def update_spreadsheet(
        self,
        spreadsheet_id: str,
        licitacoes: list[dict]
    ) -> dict[str, Any]:
        """
        Atualiza planilha existente.

        Args:
            spreadsheet_id: ID da planilha Google Sheets
            licitacoes: Novos dados

        Returns:
            {
                'spreadsheet_id': str,
                'spreadsheet_url': str,
                'total_rows': int,
                'updated_at': str (ISO 8601)
            }
        """
        # 1. Limpar dados antigos (manter header)
        self._clear_data(spreadsheet_id)

        # 2. Inserir novos dados
        self._populate_data(spreadsheet_id, licitacoes)

        # 3. Re-aplicar formatação
        self._apply_formatting(spreadsheet_id, len(licitacoes))

        return {
            'spreadsheet_id': spreadsheet_id,
            'spreadsheet_url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
            'total_rows': len(licitacoes),
            'updated_at': datetime.utcnow().isoformat()
        }

    def _create_empty_spreadsheet(self, title: str) -> dict:
        """Cria planilha vazia com configuração inicial."""
        spreadsheet = {
            'properties': {'title': title},
            'sheets': [{
                'properties': {
                    'title': 'Licitações',
                    'gridProperties': {'frozenRowCount': 1}
                }
            }]
        }
        return self.service.spreadsheets().create(body=spreadsheet).execute()

    def _populate_data(self, spreadsheet_id: str, licitacoes: list[dict]):
        """Insere dados na planilha."""
        headers = [
            'Código', 'Objeto', 'Órgão', 'UF', 'Município',
            'Valor (R$)', 'Modalidade', 'Data Publicação',
            'Data Abertura', 'Status', 'Link PNCP'
        ]

        rows = [headers]
        for lic in licitacoes:
            rows.append([
                lic.get('codigoCompra', ''),
                lic.get('objetoCompra', '')[:200],  # Truncate
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

        body = {'values': rows}
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Licitações!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

    def _apply_formatting(self, spreadsheet_id: str, total_rows: int):
        """Aplica estilos (header verde, currency, etc)."""
        requests = [
            # Header verde com texto branco
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.18, 'green': 0.49, 'blue': 0.2},
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
            # Formato moeda para coluna F (Valor)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': total_rows + 1,
                        'startColumnIndex': 5,
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
            # Auto-resize colunas
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 11
                    }
                }
            }
        ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

    def _clear_data(self, spreadsheet_id: str):
        """Limpa dados preservando header."""
        self.service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='Licitações!A2:K'
        ).execute()
```

**Novo endpoint:** `POST /api/export/google-sheets`

```python
from fastapi import APIRouter, Depends, HTTPException
from schemas import GoogleSheetsExportRequest
from google_sheets import GoogleSheetsExporter
from auth import get_current_user

router = APIRouter(prefix="/api/export", tags=["export"])

@router.post("/google-sheets")
async def export_to_google_sheets(
    request: GoogleSheetsExportRequest,
    user = Depends(get_current_user)
):
    """
    Exporta resultados para Google Sheets.

    Request Body:
        {
            "licitacoes": [...],
            "title": "SmartLic - Uniformes - 09/02/2026",
            "mode": "create" | "update",
            "spreadsheet_id": "optional, required for mode=update"
        }

    Response:
        {
            "success": true,
            "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
            "total_rows": 142
        }
    """
    # 1. Obter access_token do usuário
    access_token = await get_user_google_token(user.id)
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Google Sheets não autorizado. Por favor, conecte sua conta Google."
        )

    # 2. Criar exportador
    exporter = GoogleSheetsExporter(access_token)

    try:
        # 3. Executar exportação
        if request.mode == "create":
            result = await exporter.create_spreadsheet(
                licitacoes=request.licitacoes,
                title=request.title
            )
        else:  # update
            if not request.spreadsheet_id:
                raise HTTPException(
                    status_code=400,
                    detail="spreadsheet_id obrigatório para mode=update"
                )
            result = await exporter.update_spreadsheet(
                spreadsheet_id=request.spreadsheet_id,
                licitacoes=request.licitacoes
            )

        return {
            "success": True,
            **result
        }

    except HttpError as e:
        if e.resp.status == 403:
            raise HTTPException(
                status_code=403,
                detail="Sem permissão para acessar Google Sheets. Verifique autorização."
            )
        elif e.resp.status == 429:
            raise HTTPException(
                status_code=429,
                detail="Limite de API do Google Sheets excedido. Tente novamente em alguns minutos."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao exportar para Google Sheets: {str(e)}"
            )
```

### 5. Frontend Implementation

**Novo componente:** `frontend/components/GoogleSheetsExportButton.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FaGoogle } from 'react-icons/fa';
import { toast } from 'sonner';

interface GoogleSheetsExportButtonProps {
  licitacoes: any[];
  searchLabel: string;
  disabled?: boolean;
}

export default function GoogleSheetsExportButton({
  licitacoes,
  searchLabel,
  disabled = false
}: GoogleSheetsExportButtonProps) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);

    try {
      const response = await fetch('/api/export/google-sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          licitacoes,
          title: `SmartLic - ${searchLabel} - ${new Date().toLocaleDateString('pt-BR')}`,
          mode: 'create'
        })
      });

      if (!response.ok) {
        const error = await response.json();

        if (response.status === 401) {
          // Redirecionar para OAuth flow
          window.location.href = '/api/auth/google?redirect=/buscar';
          return;
        }

        throw new Error(error.detail || 'Erro ao exportar');
      }

      const result = await response.json();

      // Abrir planilha em nova aba
      window.open(result.spreadsheet_url, '_blank');

      toast.success(`Planilha criada com sucesso! (${result.total_rows} licitações)`);

    } catch (error: any) {
      toast.error(`Falha ao exportar: ${error.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <Button
      onClick={handleExport}
      disabled={disabled || exporting || licitacoes.length === 0}
      variant="outline"
      className="flex items-center gap-2"
    >
      <FaGoogle className="text-[#4285F4]" />
      {exporting ? 'Exportando...' : 'Exportar para Google Sheets'}
    </Button>
  );
}
```

**Integração em `app/buscar/page.tsx`:**

```typescript
import GoogleSheetsExportButton from '@/components/GoogleSheetsExportButton';

// ... dentro do componente, após resultados

{result && (
  <div className="flex gap-4 items-center">
    {/* Botão Excel existente */}
    <Button
      onClick={downloadExcel}
      disabled={downloading}
    >
      {downloading ? 'Baixando...' : 'Baixar Excel'}
    </Button>

    {/* NOVO: Botão Google Sheets */}
    <GoogleSheetsExportButton
      licitacoes={result.licitacoes}
      searchLabel={searchLabel}
      disabled={loading}
    />
  </div>
)}
```

### 6. Database Schema

**Nova tabela:** `user_oauth_tokens`

```sql
CREATE TABLE user_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'google', 'microsoft', etc
    access_token TEXT NOT NULL,     -- Criptografado AES-256
    refresh_token TEXT,             -- Criptografado AES-256
    expires_at TIMESTAMPTZ NOT NULL,
    scope TEXT NOT NULL,            -- 'https://www.googleapis.com/auth/spreadsheets'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, provider)
);

CREATE INDEX idx_user_oauth_tokens_user_id ON user_oauth_tokens(user_id);
CREATE INDEX idx_user_oauth_tokens_expires_at ON user_oauth_tokens(expires_at);
```

**Nova tabela:** `google_sheets_exports` (histórico)

```sql
CREATE TABLE google_sheets_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    spreadsheet_id VARCHAR(255) NOT NULL,
    spreadsheet_url TEXT NOT NULL,
    search_params JSONB NOT NULL, -- {ufs, dataInicial, dataFinal, setor, ...}
    total_rows INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_google_sheets_exports_user_id ON google_sheets_exports(user_id);
CREATE INDEX idx_google_sheets_exports_created_at ON google_sheets_exports(created_at DESC);
```

---

## Acceptance Criteria (AC)

### AC1: OAuth Configuration ✅

- [ ] Backend configurado com Google Cloud Project
- [ ] OAuth 2.0 Client ID criado (Web Application)
- [ ] Redirect URI configurado: `https://smartlic.tech/api/auth/google/callback`
- [ ] Escopo `https://www.googleapis.com/auth/spreadsheets` habilitado
- [ ] Credentials armazenados em variáveis de ambiente seguras

**Teste:**
```bash
# Verificar env vars
echo $GOOGLE_OAUTH_CLIENT_ID
echo $GOOGLE_OAUTH_CLIENT_SECRET

# Teste de autenticação
curl -X GET http://localhost:8000/api/auth/google
# Deve retornar redirect 302 para consent screen
```

### AC2: Token Storage and Encryption ✅

- [ ] Tabela `user_oauth_tokens` criada no Supabase
- [ ] Função de criptografia AES-256 implementada
- [ ] Access token e refresh token armazenados criptografados
- [ ] Função de refresh automático quando access token expira

**Teste:**
```sql
-- Verificar tokens criptografados (não devem estar em plain text)
SELECT
    user_id,
    provider,
    LENGTH(access_token) as token_length,
    expires_at
FROM user_oauth_tokens
WHERE provider = 'google';

-- Token deve ter ~500+ chars (AES-256 encrypted)
```

### AC3: Google Sheets Creation ✅

- [ ] Endpoint `POST /api/export/google-sheets` implementado
- [ ] Cria nova planilha com título personalizado
- [ ] Insere header verde (#2E7D32) com 11 colunas
- [ ] Insere dados de licitações (até 10.000 linhas suportadas)
- [ ] Aplica formatação: moeda, datas, hyperlinks
- [ ] Auto-resize de colunas
- [ ] Freeze primeira linha (header)

**Teste:**
```bash
# Exportar 100 licitações
curl -X POST http://localhost:8000/api/export/google-sheets \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "licitacoes": [...],
    "title": "Teste Export - Uniformes",
    "mode": "create"
  }'

# Resposta esperada:
{
  "success": true,
  "spreadsheet_id": "1BxiMVs0...",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
  "total_rows": 100
}
```

**Validação manual:**
1. Abrir `spreadsheet_url` no navegador
2. Verificar header verde com colunas corretas
3. Verificar coluna "Valor (R$)" formatada como moeda
4. Verificar coluna "Link PNCP" como hyperlink clicável

### AC4: Update Existing Spreadsheet ✅

- [ ] Endpoint suporta `mode: "update"`
- [ ] Limpa dados antigos (preserva header)
- [ ] Insere novos dados
- [ ] Re-aplica formatação
- [ ] Atualiza campo `last_updated_at` na tabela `google_sheets_exports`

**Teste:**
```bash
# Atualizar planilha existente
curl -X POST http://localhost:8000/api/export/google-sheets \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "licitacoes": [...],
    "mode": "update",
    "spreadsheet_id": "1BxiMVs0..."
  }'
```

### AC5: Frontend Button Integration ✅

- [ ] Componente `GoogleSheetsExportButton` criado
- [ ] Botão aparece ao lado do botão "Baixar Excel"
- [ ] Ícone do Google (colorido #4285F4)
- [ ] Texto: "Exportar para Google Sheets"
- [ ] Estado de loading: "Exportando..." com spinner
- [ ] Desabilitado quando `licitacoes.length === 0`

**Teste manual:**
1. Navegar para `/buscar`
2. Executar busca com resultados
3. Verificar que botão "Exportar para Google Sheets" aparece
4. Clicar no botão
5. Se não autenticado, redireciona para OAuth
6. Se autenticado, abre nova aba com planilha criada

### AC6: OAuth Flow (Frontend) ✅

- [ ] Endpoint `GET /api/auth/google` implementado
- [ ] Redireciona para Google consent screen
- [ ] Solicita escopo `https://www.googleapis.com/auth/spreadsheets`
- [ ] Callback `GET /api/auth/google/callback` implementado
- [ ] Armazena tokens no banco de dados
- [ ] Redireciona de volta para página original (`redirect` query param)

**Teste:**
1. Logout de Google no navegador
2. Clicar "Exportar para Google Sheets"
3. Ser redirecionado para tela de login do Google
4. Autorizar acesso ao Google Sheets
5. Ser redirecionado de volta para `/buscar`
6. Tentar exportar novamente (agora deve funcionar sem login)

### AC7: Error Handling ✅

- [ ] **401 Unauthorized:** Redireciona para OAuth flow
- [ ] **403 Forbidden:** Mostra mensagem "Sem permissão. Verifique autorização Google."
- [ ] **429 Rate Limit:** Mostra "Limite de API excedido. Tente em 1 minuto."
- [ ] **500 Server Error:** Mostra "Erro ao exportar. Tente novamente."
- [ ] Todas as mensagens de erro exibidas via `toast.error()` (Sonner)

**Teste:**
```bash
# Simular erro 429 (rate limit)
# Exportar 20 vezes em 1 minuto → deve retornar 429

# Simular erro 403 (token revogado)
# Revogar acesso em https://myaccount.google.com/permissions
# Tentar exportar → deve retornar 403
```

### AC8: Export History Tracking ✅

- [ ] Cada exportação registrada em `google_sheets_exports`
- [ ] Armazena `search_params` (JSONB) para rastreabilidade
- [ ] Usuário pode visualizar histórico de exportações (UI futura)
- [ ] Endpoint `GET /api/export/google-sheets/history` implementado

**Teste:**
```bash
# Listar histórico
curl -X GET http://localhost:8000/api/export/google-sheets/history \
  -H "Authorization: Bearer $USER_TOKEN"

# Resposta esperada:
{
  "exports": [
    {
      "id": "uuid",
      "spreadsheet_url": "https://docs.google.com/...",
      "total_rows": 142,
      "created_at": "2026-02-09T15:30:00Z",
      "search_params": {
        "ufs": ["SP", "RJ"],
        "setor": "Vestuário e Uniformes"
      }
    }
  ]
}
```

### AC9: Performance and Quotas ✅

- [ ] Suporta até 10.000 licitações por planilha (Google Sheets limit: 10M células)
- [ ] Batch updates (não individual cell updates) para performance
- [ ] Implementa rate limiting (100 requests/100 seconds per user - Google quota)
- [ ] Mostra warning se tentando exportar > 10.000 linhas

**Teste:**
```python
# Teste de performance (exportar 5.000 licitações)
import time

start = time.time()
response = await client.post("/api/export/google-sheets", json={
    "licitacoes": mock_licitacoes_5k,
    "title": "Performance Test",
    "mode": "create"
})
elapsed = time.time() - start

assert response.status_code == 200
assert elapsed < 30  # Deve completar em < 30 segundos
```

### AC10: Documentation ✅

- [ ] README atualizado com seção "Google Sheets Integration"
- [ ] Documentação de setup (criar Google Cloud Project)
- [ ] Documentação de env vars necessárias
- [ ] Exemplos de API endpoints (OpenAPI/Swagger)
- [ ] Troubleshooting guide (erros comuns)

**Arquivos a criar/atualizar:**
- `docs/guides/google-sheets-integration.md` (novo)
- `README.md` (atualizar seção "Features")
- `backend/openapi.yaml` (adicionar endpoints)

---

## Technical Design

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /buscar page                                             │  │
│  │    ├─ Excel Download Button (existing)                    │  │
│  │    └─ GoogleSheetsExportButton (NEW)                      │  │
│  │          ↓ onClick                                         │  │
│  │       POST /api/export/google-sheets                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓ HTTP Request
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  POST /api/export/google-sheets                           │  │
│  │    ↓                                                       │  │
│  │  1. Verify user authentication (JWT)                      │  │
│  │  2. Get Google OAuth token from DB                        │  │
│  │  3. Check if token expired → refresh if needed            │  │
│  │  4. Instantiate GoogleSheetsExporter                      │  │
│  │  5. Call create_spreadsheet() or update_spreadsheet()     │  │
│  │  6. Save export history to DB                             │  │
│  │  7. Return spreadsheet_url                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓ Google Sheets API v4
┌─────────────────────────────────────────────────────────────────┐
│                     Google Cloud Platform                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. POST /v4/spreadsheets (create)                        │  │
│  │  2. PUT /v4/spreadsheets/{id}/values (populate)           │  │
│  │  3. POST /v4/spreadsheets/{id}:batchUpdate (format)       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Sequence Diagram (First Export)

```
User                Frontend          Backend          DB        Google OAuth     Google Sheets
 │                     │                 │              │              │                │
 │ Click "Export"      │                 │              │              │                │
 ├────────────────────>│                 │              │              │                │
 │                     │                 │              │              │                │
 │                     │ POST /api/export/google-sheets│              │                │
 │                     ├────────────────>│              │              │                │
 │                     │                 │              │              │                │
 │                     │                 │ Check token  │              │                │
 │                     │                 ├─────────────>│              │                │
 │                     │                 │              │              │                │
 │                     │                 │ No token ⚠️  │              │                │
 │                     │                 │<─────────────┤              │                │
 │                     │                 │              │              │                │
 │                     │ 401 Unauthorized│              │              │                │
 │                     │<────────────────┤              │              │                │
 │                     │                 │              │              │                │
 │                     │ Redirect to OAuth│             │              │                │
 │<────────────────────┤                 │              │              │                │
 │                     │                 │              │              │                │
 │ Redirected to Google Consent Screen   │              │              │                │
 ├──────────────────────────────────────────────────────────────────>│                │
 │                     │                 │              │              │                │
 │ Authorize           │                 │              │              │                │
 ├────────────────────────────────────────────────────────────────────>│                │
 │                     │                 │              │              │                │
 │ Callback with code  │                 │              │              │                │
 │<────────────────────────────────────────────────────────────────────┤                │
 │                     │                 │              │              │                │
 │                     │ GET /api/auth/google/callback?code=xyz       │                │
 │                     ├────────────────>│              │              │                │
 │                     │                 │              │              │                │
 │                     │                 │ Exchange code for tokens    │                │
 │                     │                 ├─────────────────────────────>│                │
 │                     │                 │              │              │                │
 │                     │                 │ access_token + refresh_token│                │
 │                     │                 │<─────────────────────────────┤                │
 │                     │                 │              │              │                │
 │                     │                 │ Save tokens (encrypted)      │                │
 │                     │                 ├─────────────>│              │                │
 │                     │                 │              │              │                │
 │                     │ Redirect to /buscar            │              │                │
 │<────────────────────┤                 │              │              │                │
 │                     │                 │              │              │                │
 │ Click "Export" again│                 │              │              │                │
 ├────────────────────>│                 │              │              │                │
 │                     │                 │              │              │                │
 │                     │ POST /api/export/google-sheets│              │                │
 │                     ├────────────────>│              │              │                │
 │                     │                 │              │              │                │
 │                     │                 │ Get token ✅ │              │                │
 │                     │                 ├─────────────>│              │                │
 │                     │                 │              │              │                │
 │                     │                 │ access_token │              │                │
 │                     │                 │<─────────────┤              │                │
 │                     │                 │              │              │                │
 │                     │                 │ Create spreadsheet          │                │
 │                     │                 ├────────────────────────────────────────────>│
 │                     │                 │              │              │                │
 │                     │                 │ spreadsheet_id + URL        │                │
 │                     │                 │<────────────────────────────────────────────┤
 │                     │                 │              │              │                │
 │                     │                 │ Populate data│              │                │
 │                     │                 ├────────────────────────────────────────────>│
 │                     │                 │              │              │                │
 │                     │                 │ Apply formatting            │                │
 │                     │                 ├────────────────────────────────────────────>│
 │                     │                 │              │              │                │
 │                     │                 │ Save export history         │                │
 │                     │                 ├─────────────>│              │                │
 │                     │                 │              │              │                │
 │                     │ 200 OK {spreadsheet_url}       │              │                │
 │                     │<────────────────┤              │              │                │
 │                     │                 │              │              │                │
 │ Open spreadsheet in new tab           │              │              │                │
 │<────────────────────┤                 │              │              │                │
```

### Token Refresh Strategy

```python
async def get_user_google_token(user_id: str) -> str | None:
    """
    Retorna access token válido, refreshing se necessário.

    Returns:
        str: Valid access token
        None: Se usuário não autorizou Google Sheets
    """
    # 1. Query token from DB
    token_record = await db.query(
        "SELECT * FROM user_oauth_tokens WHERE user_id = $1 AND provider = 'google'",
        user_id
    )

    if not token_record:
        return None

    # 2. Decrypt tokens
    access_token = decrypt_aes256(token_record['access_token'])
    refresh_token = decrypt_aes256(token_record['refresh_token'])
    expires_at = token_record['expires_at']

    # 3. Check if expired
    if datetime.now(timezone.utc) < expires_at:
        return access_token  # Still valid

    # 4. Refresh token
    logger.info(f"Access token expired for user {user_id}, refreshing...")

    new_tokens = await refresh_google_token(refresh_token)

    # 5. Update DB with new tokens
    await db.execute(
        """
        UPDATE user_oauth_tokens
        SET access_token = $1,
            refresh_token = $2,
            expires_at = $3,
            updated_at = NOW()
        WHERE user_id = $4 AND provider = 'google'
        """,
        encrypt_aes256(new_tokens['access_token']),
        encrypt_aes256(new_tokens['refresh_token']),
        datetime.now(timezone.utc) + timedelta(seconds=new_tokens['expires_in']),
        user_id
    )

    return new_tokens['access_token']


async def refresh_google_token(refresh_token: str) -> dict:
    """
    Troca refresh_token por novo access_token.

    Raises:
        HTTPException: Se refresh token inválido/revogado
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )

        if response.status_code != 200:
            # Refresh token revogado/inválido
            raise HTTPException(
                status_code=401,
                detail="Google authorization expired. Please re-authorize."
            )

        return response.json()
```

---

## Testing Strategy

### Unit Tests

**Backend tests** (`backend/tests/test_google_sheets.py`):

```python
import pytest
from unittest.mock import Mock, patch
from google_sheets import GoogleSheetsExporter

@pytest.fixture
def mock_licitacoes():
    return [
        {
            "codigoCompra": "123456",
            "objetoCompra": "Fornecimento de uniformes escolares",
            "nomeOrgao": "Prefeitura Municipal",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 150000.0,
            "modalidade": "Pregão Eletrônico",
            "dataPublicacaoPncp": "2026-02-01",
            "dataAberturaProposta": "2026-02-15",
            "situacaoCompra": "Aberta"
        }
    ]

@patch('google_sheets.build')
def test_create_spreadsheet_success(mock_build, mock_licitacoes):
    """Testa criação de planilha com sucesso."""
    # Mock Google Sheets API
    mock_service = Mock()
    mock_build.return_value = mock_service

    mock_service.spreadsheets().create().execute.return_value = {
        'spreadsheetId': 'test123',
        'spreadsheetUrl': 'https://docs.google.com/spreadsheets/d/test123'
    }

    # Create exporter
    exporter = GoogleSheetsExporter(access_token='mock_token')

    # Execute
    result = await exporter.create_spreadsheet(
        licitacoes=mock_licitacoes,
        title='Test Spreadsheet'
    )

    # Assertions
    assert result['spreadsheet_id'] == 'test123'
    assert 'spreadsheetUrl' in result['spreadsheet_url']
    assert result['total_rows'] == 1

    # Verify API calls
    mock_service.spreadsheets().create.assert_called_once()
    mock_service.spreadsheets().values().update.assert_called_once()
    mock_service.spreadsheets().batchUpdate.assert_called_once()


@patch('google_sheets.build')
def test_create_spreadsheet_with_formatting(mock_build, mock_licitacoes):
    """Testa aplicação de formatação (header verde, currency, etc)."""
    mock_service = Mock()
    mock_build.return_value = mock_service

    mock_service.spreadsheets().create().execute.return_value = {
        'spreadsheetId': 'test123',
        'spreadsheetUrl': 'https://docs.google.com/...'
    }

    exporter = GoogleSheetsExporter(access_token='mock_token')
    await exporter.create_spreadsheet(mock_licitacoes, title='Test')

    # Verificar que batchUpdate foi chamado com formatação
    batch_update_call = mock_service.spreadsheets().batchUpdate.call_args
    requests = batch_update_call[1]['body']['requests']

    # Verificar header verde
    header_format = requests[0]['repeatCell']['cell']['userEnteredFormat']
    assert header_format['backgroundColor']['green'] == 0.49  # Verde #2E7D32
    assert header_format['textFormat']['bold'] is True

    # Verificar formato moeda
    currency_format = requests[1]['repeatCell']['cell']['userEnteredFormat']
    assert currency_format['numberFormat']['type'] == 'CURRENCY'
    assert 'R$' in currency_format['numberFormat']['pattern']


def test_update_spreadsheet_clears_old_data(mock_build, mock_licitacoes):
    """Testa que update limpa dados antigos antes de inserir novos."""
    mock_service = Mock()
    mock_build.return_value = mock_service

    exporter = GoogleSheetsExporter(access_token='mock_token')
    await exporter.update_spreadsheet(
        spreadsheet_id='existing123',
        licitacoes=mock_licitacoes
    )

    # Verificar que clear foi chamado
    mock_service.spreadsheets().values().clear.assert_called_once_with(
        spreadsheetId='existing123',
        range='Licitações!A2:K'
    )
```

**Frontend tests** (`frontend/__tests__/GoogleSheetsExportButton.test.tsx`):

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GoogleSheetsExportButton from '@/components/GoogleSheetsExportButton';
import { toast } from 'sonner';

jest.mock('sonner');

describe('GoogleSheetsExportButton', () => {
  const mockLicitacoes = [
    { codigoCompra: '123', objetoCompra: 'Test', valorTotalEstimado: 10000 }
  ];

  beforeEach(() => {
    global.fetch = jest.fn();
    jest.clearAllMocks();
  });

  it('renders button with correct label', () => {
    render(
      <GoogleSheetsExportButton
        licitacoes={mockLicitacoes}
        searchLabel="Uniformes"
      />
    );

    expect(screen.getByText('Exportar para Google Sheets')).toBeInTheDocument();
  });

  it('calls API on click', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        spreadsheet_url: 'https://docs.google.com/spreadsheets/d/test123',
        total_rows: 1
      })
    });

    render(
      <GoogleSheetsExportButton
        licitacoes={mockLicitacoes}
        searchLabel="Uniformes"
      />
    );

    fireEvent.click(screen.getByText('Exportar para Google Sheets'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/export/google-sheets',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('Uniformes')
        })
      );
    });
  });

  it('shows success toast and opens spreadsheet', async () => {
    const mockOpen = jest.fn();
    global.open = mockOpen;

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        spreadsheet_url: 'https://docs.google.com/spreadsheets/d/test123',
        total_rows: 42
      })
    });

    render(
      <GoogleSheetsExportButton
        licitacoes={mockLicitacoes}
        searchLabel="Uniformes"
      />
    );

    fireEvent.click(screen.getByText('Exportar para Google Sheets'));

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('42 licitações')
      );
      expect(mockOpen).toHaveBeenCalledWith(
        'https://docs.google.com/spreadsheets/d/test123',
        '_blank'
      );
    });
  });

  it('redirects to OAuth flow on 401', async () => {
    delete window.location;
    window.location = { href: '' } as any;

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Unauthorized' })
    });

    render(
      <GoogleSheetsExportButton
        licitacoes={mockLicitacoes}
        searchLabel="Uniformes"
      />
    );

    fireEvent.click(screen.getByText('Exportar para Google Sheets'));

    await waitFor(() => {
      expect(window.location.href).toBe('/api/auth/google?redirect=/buscar');
    });
  });

  it('shows error toast on failure', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' })
    });

    render(
      <GoogleSheetsExportButton
        licitacoes={mockLicitacoes}
        searchLabel="Uniformes"
      />
    );

    fireEvent.click(screen.getByText('Exportar para Google Sheets'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining('Internal server error')
      );
    });
  });

  it('is disabled when no licitacoes', () => {
    render(
      <GoogleSheetsExportButton
        licitacoes={[]}
        searchLabel="Uniformes"
      />
    );

    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### Integration Tests

**E2E test** (`frontend/e2e-tests/google-sheets-export.spec.ts`):

```typescript
import { test, expect } from '@playwright/test';

test.describe('Google Sheets Export', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Wait for redirect to /buscar
    await expect(page).toHaveURL('/buscar');
  });

  test('should export search results to Google Sheets', async ({ page }) => {
    // 1. Execute search
    await page.click('[data-testid="uf-SP"]');
    await page.click('[data-testid="uf-RJ"]');
    await page.click('button:has-text("Buscar")');

    // Wait for results
    await expect(page.locator('[data-testid="results"]')).toBeVisible();

    // 2. Click Google Sheets export
    const exportButton = page.locator('button:has-text("Exportar para Google Sheets")');
    await expect(exportButton).toBeEnabled();
    await exportButton.click();

    // 3. Check if OAuth required (first time)
    const currentUrl = page.url();

    if (currentUrl.includes('accounts.google.com')) {
      // OAuth flow
      await page.fill('[type="email"]', process.env.GOOGLE_TEST_EMAIL!);
      await page.click('button:has-text("Next")');
      await page.fill('[type="password"]', process.env.GOOGLE_TEST_PASSWORD!);
      await page.click('button:has-text("Next")');

      // Grant permissions
      await page.click('button:has-text("Allow")');

      // Wait for redirect back
      await expect(page).toHaveURL('/buscar');

      // Retry export
      await exportButton.click();
    }

    // 4. Wait for success toast
    await expect(page.locator('.sonner-toast:has-text("Planilha criada")')).toBeVisible();

    // 5. Verify new tab opened with spreadsheet
    const [newTab] = await Promise.all([
      page.waitForEvent('popup'),
      exportButton.click()
    ]);

    await expect(newTab).toHaveURL(/docs\.google\.com\/spreadsheets/);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/export/google-sheets', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });

    // Execute search
    await page.click('[data-testid="uf-SP"]');
    await page.click('button:has-text("Buscar")');
    await expect(page.locator('[data-testid="results"]')).toBeVisible();

    // Click export
    await page.click('button:has-text("Exportar para Google Sheets")');

    // Verify error toast
    await expect(
      page.locator('.sonner-toast:has-text("Falha ao exportar")')
    ).toBeVisible();
  });
});
```

---

## Implementation Checklist

### Phase 1: Google Cloud Setup (2 hours)

- [ ] Criar Google Cloud Project
- [ ] Habilitar Google Sheets API
- [ ] Habilitar Google Drive API (para sharing)
- [ ] Criar OAuth 2.0 Client ID (Web Application)
- [ ] Configurar redirect URIs:
  - `http://localhost:8000/api/auth/google/callback` (dev)
  - `https://smartlic.tech/api/auth/google/callback` (prod)
- [ ] Baixar credentials JSON
- [ ] Adicionar env vars: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`

### Phase 2: Database Schema (1 hour)

- [ ] Criar migration `backend/migrations/012_google_oauth_tokens.sql`
- [ ] Criar migration `backend/migrations/013_google_sheets_exports.sql`
- [ ] Aplicar migrations: `npx supabase db push`
- [ ] Verificar tabelas criadas: `npx supabase db pull`

### Phase 3: Backend OAuth Implementation (6 hours)

- [ ] Implementar `backend/oauth.py`:
  - [ ] `encrypt_aes256()` e `decrypt_aes256()`
  - [ ] `get_authorization_url()`
  - [ ] `exchange_code_for_tokens()`
  - [ ] `save_user_tokens()`
  - [ ] `get_user_google_token()` (com refresh automático)
  - [ ] `refresh_google_token()`
- [ ] Implementar endpoints OAuth:
  - [ ] `GET /api/auth/google` (inicia flow)
  - [ ] `GET /api/auth/google/callback` (callback handler)
  - [ ] `DELETE /api/auth/google` (revoke access)
- [ ] Testes: `backend/tests/test_oauth.py`

### Phase 4: Google Sheets Exporter (8 hours)

- [ ] Implementar `backend/google_sheets.py`:
  - [ ] Classe `GoogleSheetsExporter`
  - [ ] `create_spreadsheet()`
  - [ ] `update_spreadsheet()`
  - [ ] `_create_empty_spreadsheet()`
  - [ ] `_populate_data()`
  - [ ] `_apply_formatting()`
  - [ ] `_clear_data()`
- [ ] Implementar endpoint:
  - [ ] `POST /api/export/google-sheets`
  - [ ] Schema `GoogleSheetsExportRequest` em `backend/schemas.py`
- [ ] Testes: `backend/tests/test_google_sheets.py`

### Phase 5: Export History (3 hours)

- [ ] Implementar `backend/export_history.py`:
  - [ ] `save_export_history()`
  - [ ] `get_user_export_history()`
- [ ] Implementar endpoint:
  - [ ] `GET /api/export/google-sheets/history`
- [ ] Testes: `backend/tests/test_export_history.py`

### Phase 6: Frontend Button (5 hours)

- [ ] Criar `frontend/components/GoogleSheetsExportButton.tsx`
- [ ] Integrar em `frontend/app/buscar/page.tsx`
- [ ] Adicionar ícone Google (react-icons: `FaGoogle`)
- [ ] Implementar loading states e error handling
- [ ] Testes: `frontend/__tests__/GoogleSheetsExportButton.test.tsx`

### Phase 7: Frontend OAuth Flow (3 hours)

- [ ] Criar `frontend/app/api/auth/google/route.ts` (proxy para backend)
- [ ] Criar `frontend/app/api/auth/google/callback/route.ts`
- [ ] Implementar redirect logic
- [ ] Testar fluxo completo (login → authorize → export)

### Phase 8: E2E Testing (4 hours)

- [ ] Criar `frontend/e2e-tests/google-sheets-export.spec.ts`
- [ ] Configurar credenciais Google para testes (env vars)
- [ ] Testar OAuth flow
- [ ] Testar exportação com sucesso
- [ ] Testar error handling (401, 403, 429, 500)

### Phase 9: Documentation (3 hours)

- [ ] Criar `docs/guides/google-sheets-integration.md`
- [ ] Atualizar `README.md` (seção Features)
- [ ] Atualizar `backend/openapi.yaml` (adicionar endpoints)
- [ ] Criar troubleshooting guide

### Phase 10: Production Deployment (2 hours)

- [ ] Configurar env vars em Railway:
  ```bash
  railway variables set GOOGLE_OAUTH_CLIENT_ID="..."
  railway variables set GOOGLE_OAUTH_CLIENT_SECRET="..."
  railway variables set ENCRYPTION_KEY="$(openssl rand -base64 32)"
  ```
- [ ] Aplicar migrations em produção
- [ ] Verificar OAuth redirect URIs em Google Cloud Console
- [ ] Smoke test em produção

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Google Sheets API quota exceeded** | Medium | High | Implementar rate limiting (100 req/100s), cache de exports, warning ao usuário |
| **OAuth token revogado pelo usuário** | Medium | Medium | Graceful error handling, redirecionar para re-auth |
| **Latência na criação de planilhas** | Low | Medium | Mostrar loading state claro, timeout de 30s |
| **Formatação não preservada** | Low | Low | Testes visuais extensivos, fallback sem formatação |
| **Segurança: token leakage** | Low | Critical | AES-256 encryption, HTTPS obrigatório, não logar tokens |

---

## Success Metrics

| Métrica | Baseline | Target | Medição |
|---------|----------|--------|---------|
| **Taxa de adoção** | 0% (feature nova) | 30% dos usuários em 3 meses | Google Analytics event tracking |
| **Tempo médio de exportação** | N/A | < 5 segundos (até 1000 licitações) | Backend logging |
| **Taxa de erro** | N/A | < 2% | Error monitoring (Sentry) |
| **NPS feature** | N/A | > 8/10 | In-app survey após exportação |

---

## File List

### New Files

- [ ] `backend/google_sheets.py` - Google Sheets exporter
- [ ] `backend/oauth.py` - OAuth 2.0 handler
- [ ] `backend/export_history.py` - Export tracking
- [ ] `backend/migrations/012_google_oauth_tokens.sql`
- [ ] `backend/migrations/013_google_sheets_exports.sql`
- [ ] `backend/tests/test_google_sheets.py`
- [ ] `backend/tests/test_oauth.py`
- [ ] `backend/tests/test_export_history.py`
- [ ] `frontend/components/GoogleSheetsExportButton.tsx`
- [ ] `frontend/app/api/auth/google/route.ts`
- [ ] `frontend/app/api/auth/google/callback/route.ts`
- [ ] `frontend/app/api/export/google-sheets/route.ts`
- [ ] `frontend/__tests__/GoogleSheetsExportButton.test.tsx`
- [ ] `frontend/e2e-tests/google-sheets-export.spec.ts`
- [ ] `docs/guides/google-sheets-integration.md`

### Modified Files

- [ ] `backend/main.py` - Adicionar routers de OAuth e export
- [ ] `backend/schemas.py` - Adicionar `GoogleSheetsExportRequest`
- [ ] `backend/requirements.txt` - Adicionar `google-api-python-client`, `google-auth`
- [ ] `frontend/app/buscar/page.tsx` - Integrar `GoogleSheetsExportButton`
- [ ] `frontend/package.json` - Adicionar `react-icons` (se não existir)
- [ ] `README.md` - Documentar feature
- [ ] `backend/openapi.yaml` - Adicionar endpoints de export

---

## Dependencies

### Backend

```txt
# Adicionar ao requirements.txt
google-api-python-client==2.150.0
google-auth==2.35.0
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0
cryptography==43.0.3  # Para AES-256 encryption
```

### Frontend

```json
// Adicionar ao package.json (se não existir)
{
  "dependencies": {
    "react-icons": "^5.4.0"
  }
}
```

---

## Notes

- **Não substituir Excel, adicionar alternativa:** Manter botão "Baixar Excel" para usuários que preferem desktop
- **Privacy:** Google Sheets fica privado por padrão (só usuário tem acesso). Implementar sharing em story futura se necessário
- **Offline mode:** Google Sheets requer conexão. Excel continua sendo opção offline
- **Mobile:** Google Sheets funciona bem em mobile (app + web)
- **Limites:** Google Sheets suporta até 10 milhões de células. Com 11 colunas, limite prático é ~900K linhas (muito acima das necessidades)

---

**Status:** Aguardando aprovação para implementação
**Next Step:** Fase 1 - Google Cloud Setup
