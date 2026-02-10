# Google Sheets Integration Guide - SmartLic

**STORY-180:** Google Sheets Export Feature

## Overview

The Google Sheets integration allows users to export procurement search results directly to Google Sheets with one click, eliminating manual download and upload steps. Exported spreadsheets maintain professional formatting (green headers, currency symbols, hyperlinks) and are immediately shareable with team members.

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **Instant Collaboration** | Share results with team via Google Sheets link |
| **Cloud-First** | Access from any device, no desktop software needed |
| **Version History** | Google Sheets automatically tracks changes |
| **Real-Time Updates** | Update existing spreadsheets to refresh data |
| **Workspace Integration** | Works seamlessly with Google Workspace |

---

## Setup Instructions

### Prerequisites

- Google Cloud Project (for OAuth credentials)
- Supabase account (for database)
- Railway account (for production deployment)

### 1. Google Cloud Project Setup

#### Create Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Name: `SmartLic Production`
4. Click "Create"

#### Enable APIs

Navigate to **APIs & Services** → **Library** and enable:

- ✅ **Google Sheets API v4**
- ✅ **Google Drive API v3** (optional, for future sharing features)

#### Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `SmartLic Web Client`
5. **Authorized redirect URIs:**
   - Development: `http://localhost:8000/api/auth/google/callback`
   - Production: `https://api.smartlic.tech/api/auth/google/callback`
6. Click **Create**
7. **Download JSON** and store securely

#### Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. User Type: **External** (or Internal if you have a Google Workspace organization)
3. App Information:
   - App name: `SmartLic`
   - User support email: Your email
   - Developer contact: Your email
4. Scopes:
   - Click **Add or Remove Scopes**
   - Select: `https://www.googleapis.com/auth/spreadsheets`
5. Test users: Add your development team emails
6. Click **Save and Continue**

### 2. Environment Variables

#### Backend (`.env`)

```bash
# Google Sheets Integration (STORY-180)
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Encryption key for OAuth tokens (AES-256)
# Generate with: openssl rand -base64 32
ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# OAuth redirect URI (must match Google Cloud config)
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

#### Generate Encryption Key

```bash
# On Linux/Mac
openssl rand -base64 32

# On Windows PowerShell
$bytes = New-Object byte[] 32
[Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

⚠️ **IMPORTANT:** Keep `ENCRYPTION_KEY` secure and never commit to version control. Store in password manager.

### 3. Database Migrations

Apply migrations to create required tables:

```bash
cd backend

# Apply migrations
npx supabase db push

# Verify tables created
npx supabase db pull
```

This creates two tables:
- `user_oauth_tokens` - Encrypted OAuth tokens
- `google_sheets_exports` - Export history tracking

### 4. Railway Production Deployment

#### Set Environment Variables

```bash
# Login to Railway
railway login

# Link to project
railway link

# Set environment variables
railway variables set GOOGLE_OAUTH_CLIENT_ID="your-id.apps.googleusercontent.com"
railway variables set GOOGLE_OAUTH_CLIENT_SECRET="your-secret"
railway variables set ENCRYPTION_KEY="$(openssl rand -base64 32)"
railway variables set GOOGLE_OAUTH_REDIRECT_URI="https://api.smartlic.tech/api/auth/google/callback"

# Apply database migrations
railway run npx supabase db push --linked
```

#### Verify Production Configuration

1. Check OAuth redirect URIs in Google Cloud Console
2. Test OAuth flow in production
3. Monitor logs for errors: `railway logs --tail`

---

## User Guide

### How to Export to Google Sheets

1. **Execute a search** in SmartLic
2. **Click "Exportar para Google Sheets"** button (next to "Baixar Excel")
3. **First time only:** Authorize Google Sheets access
   - Click "Allow" on Google consent screen
   - Grant access to create/edit spreadsheets
4. **Spreadsheet opens** in new tab automatically
5. **Share with team:** Click "Share" button in Google Sheets

### Update Existing Spreadsheet

To update an existing spreadsheet (instead of creating a new one):

1. Note the **spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
   ```
2. Currently, "update mode" is available via API only (UI coming in future release)
3. Use `mode: "update"` in API request with `spreadsheet_id`

### View Export History

Export history is tracked in the database. Future release will include:
- "My Exports" page showing all Google Sheets exports
- "Re-open last export" quick action
- Search parameter tracking for reproducibility

---

## Troubleshooting

### Common Errors

#### Error: "Google Sheets não autorizado"

**Cause:** User hasn't authorized Google Sheets access

**Solution:**
1. Click "Exportar para Google Sheets" again
2. Complete OAuth consent flow
3. Grant permission to create/edit spreadsheets

#### Error: "Sem permissão para acessar Google Sheets"

**Cause:** OAuth token revoked or insufficient permissions

**Solution:**
1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find "SmartLic" app
3. Click "Remove Access"
4. Try export again (will prompt for re-authorization)

#### Error: "Limite de API excedido"

**Cause:** Google Sheets API quota exceeded (100 requests per 100 seconds per user)

**Solution:**
1. Wait 60 seconds
2. Try export again
3. For high-volume usage, contact support to discuss quota increases

#### Error: "Export too large: X rows"

**Cause:** Export exceeds 10,000 row limit

**Solution:**
1. Refine search filters to reduce results
2. Export in batches (by UF or date range)
3. Use Excel export for very large datasets (supports unlimited rows)

### Debug Mode

Enable detailed logging in backend:

```bash
# In backend/.env
LOG_LEVEL=DEBUG

# Restart backend
uvicorn main:app --reload
```

Check logs for:
- OAuth token refresh attempts
- Google API error codes
- Database query performance

---

## Security & Privacy

### Token Encryption

- OAuth tokens encrypted at rest using **AES-256 GCM** (Fernet)
- Encryption key never logged or exposed in API responses
- Tokens stored in Supabase with Row Level Security (RLS)

### Data Privacy

- **Spreadsheets are private by default:** Only the user who created the spreadsheet can access it
- **No data stored in SmartLic:** Spreadsheet data lives in user's Google Drive only
- **Export history:** Only metadata stored (spreadsheet ID, URL, row count) - not actual bid data

### Revoking Access

To revoke SmartLic's access to Google Sheets:

1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find "SmartLic"
3. Click "Remove Access"
4. Delete tokens from SmartLic settings (if available in UI)

Revoking access:
- Deletes tokens from SmartLic database
- Does NOT delete existing spreadsheets (they remain in your Google Drive)
- Requires re-authorization for future exports

---

## API Reference

### POST /api/export/google-sheets

Export search results to Google Sheets.

**Request:**
```json
{
  "licitacoes": [...],
  "title": "SmartLic - Uniformes - 09/02/2026",
  "mode": "create",
  "spreadsheet_id": null
}
```

**Response:**
```json
{
  "success": true,
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
  "total_rows": 142
}
```

**Error Codes:**
- `401 Unauthorized` - OAuth required or token expired
- `403 Forbidden` - Token revoked or insufficient permissions
- `429 Too Many Requests` - API quota exceeded
- `500 Internal Server Error` - Google API error

### GET /api/export/google-sheets/history

Get user's export history.

**Response:**
```json
{
  "exports": [
    {
      "id": "uuid",
      "spreadsheet_id": "...",
      "spreadsheet_url": "https://docs.google.com/...",
      "search_params": {"ufs": ["SP", "RJ"], "setor": "Vestuário"},
      "total_rows": 142,
      "created_at": "2026-02-09T15:30:00Z",
      "last_updated_at": "2026-02-09T15:30:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/auth/google

Initiate OAuth flow.

**Query Params:**
- `redirect` - Page to return to after authorization (default: `/buscar`)

**Response:** 302 Redirect to Google consent screen

### GET /api/auth/google/callback

Handle OAuth callback (internal endpoint).

### DELETE /api/auth/google

Revoke Google Sheets access.

**Response:**
```json
{
  "success": true
}
```

---

## Performance Optimization

### Export Speed

| Dataset Size | Expected Time | API Calls |
|--------------|---------------|-----------|
| 100 rows | < 2 seconds | 3 |
| 1000 rows | < 5 seconds | 3 |
| 5000 rows | < 30 seconds | 3 |
| 10000 rows | ~60 seconds | 3 |

### Optimization Techniques

1. **Batch Operations:** Single `values().update()` for all rows
2. **Format Once:** Apply formatting to entire range, not per-cell
3. **Connection Pooling:** Reuse HTTP connections (already in `httpx`)

### Rate Limits

- **Per User:** 100 requests per 100 seconds (Google default)
- **Per Project:** 500 requests per 100 seconds (configurable in Google Cloud Console)

To increase limits:
1. Go to Google Cloud Console
2. Navigate to **APIs & Services** → **Quotas**
3. Search for "Sheets API"
4. Request quota increase

---

## Roadmap

### Planned Features

- [ ] **UI for Update Mode** - Update existing spreadsheets from UI
- [ ] **Export History Page** - View and manage all exports
- [ ] **Folder Organization** - Export to specific Google Drive folder
- [ ] **Sharing Presets** - Save sharing settings for recurring exports
- [ ] **Scheduled Exports** - Automatic weekly/monthly exports

### Future Integrations

- [ ] **Microsoft Excel Online** - Export to OneDrive
- [ ] **Dropbox Paper** - Export to Dropbox spreadsheets
- [ ] **Notion** - Export as Notion database

---

## Support

For issues or questions:
- **GitHub Issues:** [github.com/your-org/smartlic/issues](https://github.com)
- **Email:** support@smartlic.tech
- **InMail:** Use in-app messaging system

---

## Changelog

### v0.1 (2026-02-09) - Initial Release

- ✅ Google Sheets export (create mode)
- ✅ OAuth 2.0 integration
- ✅ Professional formatting (green header, currency, hyperlinks)
- ✅ Export history tracking
- ✅ Error handling and user-friendly messages

**Next:** Update mode UI, export history page
