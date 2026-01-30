# Event Dictionary

**Version:** 1.0
**Last Updated:** 2026-01-30
**Purpose:** Complete reference for all tracked events in BidIQ Uniformes (DescompLicita) POC

---

## Event Naming Convention

**Format:** `{noun}_{verb}` (lowercase, snake_case)

**Examples:**
- ✅ `search_started`, `download_completed`, `page_load`
- ❌ `SearchStarted`, `downloadComplete`, `pageLoad`

**Versioning:**
- No version suffix on current events
- If schema changes significantly, use `_v2` suffix
- Example: `search_started_v2` (not yet needed)

---

## Standard Properties (All Events)

Every event automatically includes these properties:

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `timestamp` | ISO 8601 | Event occurrence time (UTC) | `2026-01-30T14:23:45.123Z` |
| `environment` | String | Runtime environment | `production` or `development` |
| `distinct_id` | String | Anonymous user identifier (Mixpanel auto-generated) | `18c12345-6789-abcd-ef01-234567890abc` |

**Privacy Note:** No personally identifiable information (PII) is tracked. All users are anonymous.

---

## Event Catalog

### 1. Page Lifecycle Events

#### `page_load`

**Description:** User enters the application (page loads)

**When Triggered:** On application mount (first render)

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `path` | String | ✅ | Current page path | `/` |
| `referrer` | String | ⚠️ | HTTP referrer (or "direct") | `https://google.com` or `direct` |
| `user_agent` | String | ✅ | Browser user agent string | `Mozilla/5.0 (Windows NT 10.0; Win64; x64)...` |

**Example Payload:**
```json
{
  "event": "page_load",
  "properties": {
    "path": "/",
    "timestamp": "2026-01-30T14:23:45.123Z",
    "environment": "production",
    "referrer": "direct",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  }
}
```

**Usage:**
- Track daily/weekly/monthly active users (DAU/WAU/MAU)
- Identify traffic sources (referrer analysis)
- Detect browser/device distribution

---

#### `page_exit`

**Description:** User leaves the application (navigates away or closes tab)

**When Triggered:** On `beforeunload` browser event

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `path` | String | ✅ | Page path at exit | `/` |
| `session_duration_ms` | Number | ✅ | Session length in milliseconds | `125430` |
| `session_duration_readable` | String | ✅ | Human-readable session length | `125s` |

**Example Payload:**
```json
{
  "event": "page_exit",
  "properties": {
    "path": "/",
    "session_duration_ms": 125430,
    "session_duration_readable": "125s",
    "timestamp": "2026-01-30T14:25:50.553Z",
    "environment": "production"
  }
}
```

**Usage:**
- Calculate average session duration
- Identify bounce rate (exits <30s without search)
- Understand engagement depth

**Note:** May not fire reliably on mobile browsers or if user force-closes browser.

---

### 2. Search Events

#### `search_started`

**Description:** User initiates a procurement opportunity search

**When Triggered:** On search form submit (button click)

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `ufs` | Array<String> | ✅ | Selected Brazilian states (UF codes) | `["SC", "PR", "RS"]` |
| `uf_count` | Number | ✅ | Number of selected states | `3` |
| `date_range_days` | Number | ✅ | Search window in days | `7` |
| `search_mode` | Enum | ✅ | Search type: "setor" or "termos" | `setor` |
| `setor_id` | String | ⚠️ | Sector ID (if search_mode = "setor") | `vestuario` |
| `custom_terms` | Array<String> | ⚠️ | Custom keywords (if search_mode = "termos") | `["uniforme", "jaleco"]` |
| `custom_terms_count` | Number | ⚠️ | Number of custom keywords | `2` |

**Example Payload (Sector Mode):**
```json
{
  "event": "search_started",
  "properties": {
    "ufs": ["SC", "PR"],
    "uf_count": 2,
    "date_range_days": 7,
    "search_mode": "setor",
    "setor_id": "vestuario",
    "timestamp": "2026-01-30T14:24:00.000Z",
    "environment": "production"
  }
}
```

**Example Payload (Custom Terms Mode):**
```json
{
  "event": "search_started",
  "properties": {
    "ufs": ["SP"],
    "uf_count": 1,
    "date_range_days": 15,
    "search_mode": "termos",
    "custom_terms": ["uniforme escolar", "fardamento"],
    "custom_terms_count": 2,
    "timestamp": "2026-01-30T14:24:00.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Track total searches per day/week
- Identify most searched states (UF popularity)
- Measure multi-state search adoption
- Understand sector vs. custom terms preference

---

#### `search_completed`

**Description:** Search finishes successfully with results

**When Triggered:** On successful API response from `/api/buscar`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `time_elapsed_ms` | Number | ✅ | Search duration in milliseconds | `18532` |
| `time_elapsed_readable` | String | ✅ | Human-readable duration | `18s` |
| `total_raw` | Number | ✅ | Unfiltered PNCP results count | `1523` |
| `total_filtered` | Number | ✅ | Filtered opportunities count | `87` |
| `filter_efficiency` | Number | ✅ | Filtering ratio (%) | `5.71` |
| `opportunities_found` | Number | ✅ | Same as `total_filtered` | `87` |
| `setor_id` | String | ⚠️ | Sector ID (if applicable) | `vestuario` |
| `search_mode` | Enum | ✅ | Search type | `setor` |

**Example Payload:**
```json
{
  "event": "search_completed",
  "properties": {
    "time_elapsed_ms": 18532,
    "time_elapsed_readable": "18s",
    "total_raw": 1523,
    "total_filtered": 87,
    "filter_efficiency": 5.71,
    "opportunities_found": 87,
    "setor_id": "vestuario",
    "search_mode": "setor",
    "timestamp": "2026-01-30T14:24:18.532Z",
    "environment": "production"
  }
}
```

**Usage:**
- Measure search performance (response time P50/P95)
- Calculate search success rate
- Analyze filter effectiveness
- Track opportunities discovered per search

---

#### `search_failed`

**Description:** Search encounters an error

**When Triggered:** On API error or exception during search

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `error_message` | String | ✅ | User-friendly error message | `Erro ao buscar licitações` |
| `error_type` | String | ✅ | Error class/type | `TypeError` or `unknown` |
| `ufs` | Array<String> | ⚠️ | UFs from failed search | `["SC"]` |
| `setor_id` | String | ⚠️ | Sector ID (if applicable) | `vestuario` |
| `search_mode` | Enum | ⚠️ | Search type | `setor` |

**Example Payload:**
```json
{
  "event": "search_failed",
  "properties": {
    "error_message": "Erro ao buscar licitações. Tente novamente.",
    "error_type": "NetworkError",
    "ufs": ["SC", "PR"],
    "setor_id": "vestuario",
    "search_mode": "setor",
    "timestamp": "2026-01-30T14:24:05.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Monitor error rate trends
- Identify most common error types
- Correlate errors with specific UFs or sectors
- Trigger alerts on error spikes

---

#### `search_progress_stage`

**Description:** Search progresses through loading stages

**When Triggered:** On loading stage transition (5 stages total)

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `stage` | Number | ✅ | Current stage (1-5) | `3` |
| `ufs` | Array<String> | ✅ | UFs being searched | `["SC"]` |
| `setor_id` | String | ⚠️ | Sector ID (if applicable) | `vestuario` |

**Example Payload:**
```json
{
  "event": "search_progress_stage",
  "properties": {
    "stage": 3,
    "ufs": ["SC", "PR"],
    "setor_id": "vestuario",
    "timestamp": "2026-01-30T14:24:08.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Track user experience through loading process
- Identify if users see all 5 stages
- Understand perceived wait time

---

### 3. Download Events

#### `download_started`

**Description:** User clicks "Baixar Excel" button

**When Triggered:** On download button click

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `download_id` | String | ✅ | Unique download identifier (UUID) | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `total_filtered` | Number | ✅ | Number of opportunities in Excel | `87` |
| `opportunities_count` | Number | ✅ | Same as `total_filtered` | `87` |

**Example Payload:**
```json
{
  "event": "download_started",
  "properties": {
    "download_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "total_filtered": 87,
    "opportunities_count": 87,
    "timestamp": "2026-01-30T14:25:00.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Track download initiation rate (result → download)
- Measure user intent to act on results

---

#### `download_completed`

**Description:** Excel file successfully downloaded

**When Triggered:** On successful file download response

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `download_id` | String | ✅ | Download identifier (from `download_started`) | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `time_elapsed_ms` | Number | ✅ | Download time in milliseconds | `2341` |
| `time_elapsed_readable` | String | ✅ | Human-readable duration | `2s` |
| `file_size_bytes` | Number | ✅ | Excel file size in bytes | `45678` |
| `file_size_readable` | String | ✅ | Human-readable file size | `44.6 KB` |

**Example Payload:**
```json
{
  "event": "download_completed",
  "properties": {
    "download_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "time_elapsed_ms": 2341,
    "time_elapsed_readable": "2s",
    "file_size_bytes": 45678,
    "file_size_readable": "44.6 KB",
    "timestamp": "2026-01-30T14:25:02.341Z",
    "environment": "production"
  }
}
```

**Usage:**
- Measure download success rate
- Track download performance
- Identify slow downloads (>5s)

---

#### `download_failed`

**Description:** Excel download encounters an error

**When Triggered:** On download API error or exception

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `download_id` | String | ✅ | Download identifier | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `error_message` | String | ✅ | User-friendly error message | `Erro ao baixar Excel` |
| `error_type` | String | ✅ | Error class/type | `NetworkError` or `unknown` |

**Example Payload:**
```json
{
  "event": "download_failed",
  "properties": {
    "download_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "error_message": "Erro ao baixar Excel. Tente novamente.",
    "error_type": "NotFoundError",
    "timestamp": "2026-01-30T14:25:02.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Monitor download reliability
- Identify download failure patterns
- Trigger alerts on high failure rate

---

### 4. Loading Progress Events

#### `loading_stage_reached`

**Description:** User sees a specific loading stage during search

**When Triggered:** On loading stage transition (5 stages total)

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `stage` | Number | ✅ | Stage number (1-5) | `3` |
| `stage_index` | Number | ✅ | Zero-based stage index (0-4) | `2` |
| `total_stages` | Number | ✅ | Total stages (always 5) | `5` |
| `time_in_stage_ms` | Number | ✅ | Time spent in this stage (ms) | `3456` |
| `time_in_stage_readable` | String | ✅ | Human-readable stage time | `3s` |

**Example Payload:**
```json
{
  "event": "loading_stage_reached",
  "properties": {
    "stage": 3,
    "stage_index": 2,
    "total_stages": 5,
    "time_in_stage_ms": 3456,
    "time_in_stage_readable": "3s",
    "timestamp": "2026-01-30T14:24:11.456Z",
    "environment": "production"
  }
}
```

**Usage:**
- Identify slowest loading stage (bottleneck)
- Measure time distribution across stages
- Optimize perceived performance

---

#### `loading_abandoned`

**Description:** User navigates away during loading (before search completes)

**When Triggered:** On `beforeunload` while search is in progress

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `last_stage` | Number | ✅ | Last stage user saw (1-5) | `3` |
| `last_stage_index` | Number | ✅ | Zero-based stage index (0-4) | `2` |
| `time_in_current_stage_ms` | Number | ✅ | Time in last stage (ms) | `15234` |
| `total_stages` | Number | ✅ | Total stages (always 5) | `5` |
| `total_time_ms` | Number | ✅ | Total time before abandonment (ms) | `32105` |

**Example Payload:**
```json
{
  "event": "loading_abandoned",
  "properties": {
    "last_stage": 3,
    "last_stage_index": 2,
    "time_in_current_stage_ms": 15234,
    "total_stages": 5,
    "total_time_ms": 32105,
    "timestamp": "2026-01-30T14:24:32.105Z",
    "environment": "production"
  }
}
```

**Usage:**
- Measure abandonment rate (% of searches abandoned)
- Identify at which stage users give up
- Trigger alerts if abandonment >10%

---

### 5. Onboarding Events (Feature #3)

#### `onboarding_completed`

**Description:** User finishes the interactive product tour

**When Triggered:** On Shepherd.js tour completion

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `completion_time` | Number | ✅ | Timestamp of completion (epoch ms) | `1706624700000` |

**Example Payload:**
```json
{
  "event": "onboarding_completed",
  "properties": {
    "completion_time": 1706624700000,
    "timestamp": "2026-01-30T14:25:00.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Track onboarding completion rate
- Measure feature adoption among new users

---

#### `onboarding_dismissed`

**Description:** User dismisses/skips the product tour early

**When Triggered:** On Shepherd.js tour cancel or skip

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `dismissed_at` | Number | ✅ | Timestamp of dismissal (epoch ms) | `1706624650000` |

**Example Payload:**
```json
{
  "event": "onboarding_dismissed",
  "properties": {
    "dismissed_at": 1706624650000,
    "timestamp": "2026-01-30T14:24:10.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Measure tour abandonment rate
- Identify if tour is too long/complex

---

#### `onboarding_step`

**Description:** User progresses through a tour step

**When Triggered:** On Shepherd.js step change

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `step_id` | String | ✅ | Shepherd.js step identifier | `welcome` |
| `step_index` | Number | ✅ | Zero-based step number | `0` |

**Example Payload:**
```json
{
  "event": "onboarding_step",
  "properties": {
    "step_id": "search-form",
    "step_index": 2,
    "timestamp": "2026-01-30T14:24:25.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Track step-by-step progression
- Identify where users drop off in tour
- Measure time spent per step

---

### 6. Saved Searches Events (Feature #1)

#### `saved_search_created`

**Description:** User saves a search configuration

**When Triggered:** On successful saved search creation

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `search_name` | String | ✅ | User-provided search name | `Uniformes SC/PR` |
| `search_mode` | Enum | ✅ | Search type: "setor" or "termos" | `setor` |
| `setor_id` | String | ⚠️ | Sector ID (if search_mode = "setor") | `vestuario` |
| `ufs` | Array<String> | ✅ | Saved UF selection | `["SC", "PR"]` |
| `date_range_days` | Number | ✅ | Saved date range | `7` |

**Example Payload:**
```json
{
  "event": "saved_search_created",
  "properties": {
    "search_name": "Uniformes SC/PR Semanal",
    "search_mode": "setor",
    "setor_id": "vestuario",
    "ufs": ["SC", "PR"],
    "date_range_days": 7,
    "timestamp": "2026-01-30T14:26:00.000Z",
    "environment": "production"
  }
}
```

**Usage:**
- Track saved search adoption rate
- Measure repeat user behavior
- Identify most saved configurations

---

## Event Flow Examples

### Happy Path: Successful Search → Download

```
1. page_load
2. search_started (ufs: ["SC"], setor_id: "vestuario")
3. search_progress_stage (stage: 1)
4. loading_stage_reached (stage: 1)
5. search_progress_stage (stage: 2)
6. loading_stage_reached (stage: 2)
7. search_progress_stage (stage: 3)
8. loading_stage_reached (stage: 3)
9. search_progress_stage (stage: 4)
10. loading_stage_reached (stage: 4)
11. search_progress_stage (stage: 5)
12. loading_stage_reached (stage: 5)
13. search_completed (total_filtered: 87)
14. download_started (download_id: "abc-123")
15. download_completed (file_size_bytes: 45678)
16. page_exit (session_duration_ms: 125430)
```

### Error Path: Search Failure

```
1. page_load
2. search_started
3. search_progress_stage (stage: 1)
4. loading_stage_reached (stage: 1)
5. search_failed (error_message: "Erro ao buscar")
6. page_exit
```

### Abandonment Path: Loading Abandoned

```
1. page_load
2. search_started
3. search_progress_stage (stage: 1)
4. loading_stage_reached (stage: 1)
5. search_progress_stage (stage: 2)
6. loading_stage_reached (stage: 2)
7. loading_abandoned (last_stage: 2)
8. page_exit
```

---

## Testing Events

### Development Environment

1. **Enable Debug Mode:**
   ```javascript
   // In browser console
   mixpanel.get_config('debug'); // Should return true in development
   ```

2. **View Events:**
   - Open browser console (F12)
   - Look for Mixpanel logs: `[Mixpanel] Tracking: event_name`

3. **Manually Trigger:**
   ```javascript
   // In browser console
   mixpanel.track('test_event', { test_property: 'test_value' });
   ```

### Production Environment

1. **Live View:**
   - Mixpanel → Reports → Live View
   - See events in real-time as they're tracked

2. **Insights:**
   - Mixpanel → Reports → Insights
   - Query events by name
   - View property distributions

---

## Data Retention

**Mixpanel Free Tier:**
- **Event History:** 1 year
- **User Profiles:** Unlimited
- **Data Export:** CSV/API available

**After 1 Year:**
- Events are aggregated (daily/weekly/monthly)
- Detailed event-level data is deleted
- Aggregate metrics remain

**Best Practice:**
- Export critical data quarterly for long-term archival
- Store in data warehouse (future enhancement)

---

## Privacy & Compliance

### LGPD Compliance (Brazilian Data Protection Law)

**Data Collected:**
- ✅ Anonymous user identifiers (Mixpanel distinct_id)
- ✅ Aggregate usage metrics (search counts, response times)
- ✅ Technical data (user_agent, referrer)

**Data NOT Collected:**
- ❌ Names, emails, phone numbers
- ❌ IP addresses (Mixpanel IP geo-location disabled)
- ❌ Personally identifiable information (PII)

**User Rights:**
- Data deletion: Contact @devops to anonymize/delete user data
- Data export: Request via Mixpanel API

---

## Changelog

### Version 1.0 (2026-01-30)
- Initial event dictionary
- 15 events documented
- Standard properties defined
- Event flow examples added

---

**Questions?** Contact @analyst or refer to `docs/analytics/mixpanel-dashboard-configuration.md`
