# STORY-184: Lead Deduplication Specification

**Date:** 2026-02-10
**Analyst:** @analyst (Atlas)
**Requirement Source:** User feedback during discovery

---

## 🎯 Business Requirement

> "Cada relatório gerado pelo workflow deve ser armazenado e consultado por execuções posteriores de forma a garantir que cada nova execução traga leads inéditos."

**Translation:** Every lead prospecting report must be stored and checked against in future executions to ensure only **NEW leads** are returned (no duplicates).

---

## 🏗️ Technical Specification

### Storage Strategy

#### Option 1: File-Based Storage (MVP - RECOMMENDED)

**Location:** `docs/leads/history/`

**Structure:**
```
docs/leads/
├── leads-2026-02-10.md           # Current execution output
├── leads-2026-02-15.md
├── leads-2026-02-20.md
└── history/
    ├── leads-index.json          # Master index of all leads
    └── cnpj-history.json         # Fast lookup by CNPJ
```

**`cnpj-history.json` Schema:**
```json
{
  "version": "1.0",
  "last_updated": "2026-02-10T15:30:00Z",
  "total_leads": 157,
  "leads": [
    {
      "cnpj": "19560932000117",
      "company_name": "JTS COMERCIO DE ALIMENTOS LTDA",
      "first_discovered": "2026-02-10T15:30:00Z",
      "last_seen": "2026-02-10T15:30:00Z",
      "times_discovered": 1,
      "qualification_score": 8.7,
      "contact_made": false,
      "converted": false,
      "notes": "Sent initial outreach 2026-02-12"
    },
    {
      "cnpj": "12345678000190",
      "company_name": "EMPRESA EXEMPLO LTDA",
      "first_discovered": "2026-01-15T10:00:00Z",
      "last_seen": "2026-02-10T15:30:00Z",
      "times_discovered": 3,
      "qualification_score": 9.2,
      "contact_made": true,
      "converted": true,
      "notes": "Converted to subscriber on 2026-01-20"
    }
  ]
}
```

#### Option 2: Database Storage (Future Enhancement)

**Table:** `lead_history`

```sql
CREATE TABLE lead_history (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) UNIQUE NOT NULL,
  company_name VARCHAR(255),
  first_discovered TIMESTAMP NOT NULL,
  last_seen TIMESTAMP NOT NULL,
  times_discovered INT DEFAULT 1,
  qualification_score DECIMAL(3,1),
  contact_made BOOLEAN DEFAULT FALSE,
  converted BOOLEAN DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lead_history_cnpj ON lead_history(cnpj);
CREATE INDEX idx_lead_history_converted ON lead_history(converted);
```

---

## 🔄 Workflow Integration

### Updated Data Flow

```
*acha-leads --sectors uniformes --months 12
    ↓
[1] Query PNCP API (homologated contracts)
    ↓
[2] Extract winning CNPJs
    ↓
[3] 🆕 LOAD HISTORY: Read cnpj-history.json
    ↓
[4] 🆕 FILTER DUPLICATES: Exclude CNPJs already in history
    ↓
[5] Receita Federal API (enrich NEW CNPJs only)
    ↓
[6] Calculate dependency score
    ↓
[7] Filter high-dependency (≥70%)
    ↓
[8] Web search for contact data
    ↓
[9] OpenAI personalized messages
    ↓
[10] Qualification scoring
    ↓
[11] 🆕 UPDATE HISTORY: Add new leads to cnpj-history.json
    ↓
[12] Output: Markdown document with ONLY NEW leads
```

---

## 📝 Implementation Details

### Deduplication Logic

```python
def filter_new_leads(candidates: List[str], history_file: str = "docs/leads/history/cnpj-history.json") -> List[str]:
    """
    Filter out CNPJs that have already been discovered.

    Args:
        candidates: List of CNPJs from PNCP query
        history_file: Path to CNPJ history JSON

    Returns:
        List of NEW CNPJs (not in history)
    """
    import json
    from pathlib import Path

    history_path = Path(history_file)

    # Load existing history
    if history_path.exists():
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        existing_cnpjs = set(lead["cnpj"] for lead in history["leads"])
    else:
        existing_cnpjs = set()

    # Filter for new CNPJs only
    new_cnpjs = [cnpj for cnpj in candidates if cnpj not in existing_cnpjs]

    return new_cnpjs


def update_history(new_leads: List[Dict], history_file: str = "docs/leads/history/cnpj-history.json"):
    """
    Add new leads to history file.

    Args:
        new_leads: List of lead dictionaries (from workflow output)
        history_file: Path to CNPJ history JSON
    """
    import json
    from pathlib import Path
    from datetime import datetime

    history_path = Path(history_file)

    # Create history directory if needed
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing history
    if history_path.exists():
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = {
            "version": "1.0",
            "last_updated": None,
            "total_leads": 0,
            "leads": []
        }

    # Add new leads
    now = datetime.utcnow().isoformat() + "Z"
    for lead in new_leads:
        history["leads"].append({
            "cnpj": lead["cnpj"],
            "company_name": lead["company_name"],
            "first_discovered": now,
            "last_seen": now,
            "times_discovered": 1,
            "qualification_score": lead["qualification_score"],
            "contact_made": False,
            "converted": False,
            "notes": ""
        })

    # Update metadata
    history["last_updated"] = now
    history["total_leads"] = len(history["leads"])

    # Save updated history
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return history["total_leads"]
```

### Usage in Workflow

```python
# In backend/lead_prospecting.py (to be created)

def execute_acha_leads(sectors: List[str], months: int, min_score: float):
    """Main workflow execution."""

    # Step 1: Query PNCP for contracts
    contracts = pncp_client.buscar_contratos_homologados(months=months)

    # Step 2: Extract unique CNPJs
    all_cnpjs = list(set(c["niFornecedor"] for c in contracts))
    logger.info(f"Found {len(all_cnpjs)} unique CNPJs from PNCP")

    # Step 3: FILTER NEW LEADS (deduplication)
    new_cnpjs = filter_new_leads(all_cnpjs)
    logger.info(f"After deduplication: {len(new_cnpjs)} NEW leads to process")

    if not new_cnpjs:
        logger.warning("No new leads found - all CNPJs already in history")
        return []

    # Step 4-10: Continue with enrichment, scoring, etc. (only for NEW leads)
    qualified_leads = []
    for cnpj in new_cnpjs:
        # ... (existing logic)
        qualified_leads.append(lead)

    # Step 11: UPDATE HISTORY
    total_leads = update_history(qualified_leads)
    logger.info(f"History updated - Total leads tracked: {total_leads}")

    # Step 12: Output
    return qualified_leads
```

---

## 🎯 Acceptance Criteria (Updated)

### AC10: Lead Deduplication (NEW)

- [ ] Create `docs/leads/history/` directory structure
- [ ] Implement `cnpj-history.json` storage format
- [ ] Implement `filter_new_leads()` function
- [ ] Implement `update_history()` function
- [ ] Integrate deduplication into main workflow
- [ ] Test: Second execution should NOT return same leads as first

**Test Case:**
```python
# First execution
leads_1 = execute_acha_leads(sectors=["uniformes"], months=12, min_score=7.0)
assert len(leads_1) >= 10

# Second execution (immediately after)
leads_2 = execute_acha_leads(sectors=["uniformes"], months=12, min_score=7.0)
assert len(leads_2) == 0  # No new leads

# Verify history file exists
assert os.path.exists("docs/leads/history/cnpj-history.json")

# Verify all leads from first execution are in history
with open("docs/leads/history/cnpj-history.json") as f:
    history = json.load(f)
    history_cnpjs = set(lead["cnpj"] for lead in history["leads"])
    for lead in leads_1:
        assert lead["cnpj"] in history_cnpjs
```

---

## 📊 Output Changes

### Updated Lead Report Header

```markdown
# Lead Prospecting Report - 2026-02-10

**Generated by:** *acha-leads workflow
**Parameters:** sectors=uniformes, months=12, min_score=7.0
**Time Window:** 2025-02-10 to 2026-02-10

**Deduplication:**
- Total Candidates: 234
- Already in History: 187
- **NEW Leads Processed:** 47
- **NEW Qualified Leads:** 12

**History Status:**
- Total Leads in History: 199 (187 + 12)
- First Lead: 2025-12-01
- Most Recent: 2026-02-10

---

## Lead #1 - [NEW] EMPRESA EXEMPLO LTDA ⭐ (Score: 8.7/10)
...
```

### History Management Commands

**View History:**
```bash
*acha-leads-history

# Output:
# Total Leads: 199
# Contacted: 45 (23%)
# Converted: 12 (6%)
# Pending: 142 (71%)
```

**Mark Lead as Contacted:**
```bash
*acha-leads-update --cnpj 19560932000117 --contacted true --notes "Email sent 2026-02-12"
```

**Export History:**
```bash
*acha-leads-export --format csv --output leads-history.csv
```

---

## 🚀 Migration Strategy

### Phase 1: File-Based (MVP)
- Implement `cnpj-history.json`
- Basic deduplication
- Manual management via JSON editing

### Phase 2: Database (Future)
- Migrate to PostgreSQL/Supabase
- CRM-like interface
- Conversion tracking
- Sales pipeline integration

---

## 💡 Business Value

### Before Deduplication
- **Problem:** Same leads appear in every execution
- **Impact:** Wasted time contacting same companies
- **Risk:** Annoying prospects with duplicate outreach

### After Deduplication
- **Benefit:** 100% fresh leads every execution
- **Impact:** Efficient use of sales time
- **Value:** Better prospect experience (no spam)

**ROI Example:**
- Workflow execution: 5 minutes
- Lead research: 10 minutes per lead
- With 50% duplication: 10 minutes × 5 duplicate leads = 50 minutes wasted
- **Time saved per execution: ~50 minutes**

---

## 🔒 Privacy & Compliance

### Data Retention
- **Personal Data:** Only CNPJ (public registry number), no personal info
- **Contact Data:** Business emails/phones (publicly available)
- **LGPD Compliance:** CNPJ is public data, no consent needed

### Right to Forget
- If a company requests removal:
  ```python
  remove_lead_from_history(cnpj="12345678000190", reason="User requested removal")
  ```

---

**Analyst:** @analyst (Atlas)
**Story:** STORY-184
**Phase:** 1 (Discovery)
**Status:** Requirement documented, ready for Phase 2 (Design)
