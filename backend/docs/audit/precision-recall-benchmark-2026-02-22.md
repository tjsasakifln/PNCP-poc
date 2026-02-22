# CRIT-FLT-009: Precision/Recall Benchmark — 2026-02-22

**Generated:** 2026-02-22 16:21:00
**Pipeline:** Keyword matching (`filter.py:match_keywords`)
**Dataset:** 450 labeled procurement descriptions (15 relevant + 15 irrelevant per sector)
**Sectors:** 15

## Targets

| Metric | Minimum | Ideal |
|--------|---------|-------|
| Precision | >= 85% | >= 95% |
| Recall | >= 70% | >= 85% |
| Cross-sector FP rate | < 30% | < 10% |

## Consolidated Results

| Sector | Precision | Recall | TP | FP | FN | TN | Sample | Status |
|--------|-----------|--------|----|----|----|----|--------|--------|
| Vestuário e Uniformes (`vestuario`) | 100.0% | 100.0% | 15 | 0 | 0 | 15 | 30 | **PASS** |
| Alimentos e Merenda (`alimentos`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| Hardware e Equipamentos de TI (`informatica`) | 93.8% | 100.0% | 15 | 1 | 0 | 14 | 30 | **PASS** |
| Mobiliário (`mobiliario`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| Papelaria e Material de Escritório (`papelaria`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| Engenharia, Projetos e Obras (`engenharia`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| Software e Sistemas (`software`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| Facilities e Manutenção (`facilities`) | 100.0% | 100.0% | 15 | 0 | 0 | 15 | 30 | **PASS** |
| Saúde (`saude`) | 88.2% | 100.0% | 15 | 2 | 0 | 13 | 30 | **PASS** |
| Vigilância e Segurança Patrimonial (`vigilancia`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| Transporte e Veículos (`transporte`) | 100.0% | 100.0% | 15 | 0 | 0 | 15 | 30 | **PASS** |
| Manutenção e Conservação Predial (`manutencao_predial`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| Engenharia Rodoviária e Infraestrutura Viária (`engenharia_rodoviaria`) | 100.0% | 86.7% | 13 | 0 | 2 | 15 | 30 | **PASS** |
| Materiais Elétricos e Instalações (`materiais_eletricos`) | 91.7% | 73.3% | 11 | 1 | 4 | 14 | 30 | **PASS** |
| Materiais Hidráulicos e Saneamento (`materiais_hidraulicos`) | 100.0% | 93.3% | 14 | 0 | 1 | 15 | 30 | **PASS** |
| **AGGREGATE** | **98.1%** | **93.8%** | **211** | **4** | **14** | **221** | **450** | **ALL PASS** |

**Sectors passing:** 15/15
**Aggregate precision:** 98.1%
**Aggregate recall:** 93.8%

## Cross-Sector Collision Analysis

**Collision rate:** 22.7%

Cross-sector overlap is expected behavior — real procurement descriptions
naturally mention multiple domains (e.g., "construção de UBS" matches both
engenharia and saúde). In the live pipeline, users search for ONE sector at
a time, so cross-sector matches don't affect user-facing precision.

### Top Collision Pairs

| Sector A | Sector B | Items |
|----------|----------|-------|
| `informatica` | `software` | 10 |
| `engenharia` | `engenharia_rodoviaria` | 7 |
| `facilities` | `saude` | 4 |
| `engenharia` | `manutencao_predial` | 4 |
| `engenharia` | `materiais_hidraulicos` | 3 |
| `engenharia` | `mobiliario` | 2 |
| `mobiliario` | `saude` | 2 |
| `engenharia` | `saude` | 2 |
| `facilities` | `vigilancia` | 2 |
| `engenharia` | `materiais_eletricos` | 2 |
| `saude` | `vestuario` | 1 |
| `vestuario` | `vigilancia` | 1 |
| `alimentos` | `saude` | 1 |
| `alimentos` | `facilities` | 1 |
| `informatica` | `saude` | 1 |

## Per-Sector Detail

### Vestuário e Uniformes (`vestuario`)

- **Precision:** 100.0%
- **Recall:** 100.0%
- **Keywords:** 91
- **Exclusions:** 175
- **Context gates:** 10

**No false positives or false negatives detected.**

### Alimentos e Merenda (`alimentos`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 85
- **Exclusions:** 41
- **Context gates:** 12

**False Negatives:**
- `Contratação de empresa para alimentação escolar no município`

### Hardware e Equipamentos de TI (`informatica`)

- **Precision:** 93.8%
- **Recall:** 100.0%
- **Keywords:** 83
- **Exclusions:** 48
- **Context gates:** 8

**False Positives:**
- `Aquisição de software e licenças de sistema operacional` → matched: ['software', 'sistema operacional']

### Mobiliário (`mobiliario`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 75
- **Exclusions:** 119
- **Context gates:** 16

**False Negatives:**
- `Compra de longarinas para sala de espera do hospital`

### Papelaria e Material de Escritório (`papelaria`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 69
- **Exclusions:** 30
- **Context gates:** 16

**False Negatives:**
- `Aquisição de toner e cartucho para impressoras do escritório`

### Engenharia, Projetos e Obras (`engenharia`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 106
- **Exclusions:** 61
- **Context gates:** 9

**False Negatives:**
- `Projeto de fundação e estrutura para prédio administrativo`

### Software e Sistemas (`software`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 98
- **Exclusions:** 143
- **Context gates:** 7

**False Negatives:**
- `Contratação de plataforma de ensino a distância EAD`

### Facilities e Manutenção (`facilities`)

- **Precision:** 100.0%
- **Recall:** 100.0%
- **Keywords:** 113
- **Exclusions:** 104
- **Context gates:** 9

**No false positives or false negatives detected.**

### Saúde (`saude`)

- **Precision:** 88.2%
- **Recall:** 100.0%
- **Keywords:** 268
- **Exclusions:** 85
- **Context gates:** 7

**False Positives:**
- `Construção de unidade básica de saúde no bairro norte` → matched: ['saude', 'saúde']
- `Serviço de vigilância patrimonial para hospital municipal` → matched: ['hospital']

### Vigilância e Segurança Patrimonial (`vigilancia`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 84
- **Exclusions:** 52
- **Context gates:** 4

**False Negatives:**
- `Serviço de ronda motorizada para patrimônio público`

### Transporte e Veículos (`transporte`)

- **Precision:** 100.0%
- **Recall:** 100.0%
- **Keywords:** 130
- **Exclusions:** 44
- **Context gates:** 7

**No false positives or false negatives detected.**

### Manutenção e Conservação Predial (`manutencao_predial`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 69
- **Exclusions:** 68
- **Context gates:** 2

**False Negatives:**
- `Serviço de conservação predial incluindo pintura e reparos`

### Engenharia Rodoviária e Infraestrutura Viária (`engenharia_rodoviaria`)

- **Precision:** 100.0%
- **Recall:** 86.7%
- **Keywords:** 76
- **Exclusions:** 25
- **Context gates:** 2

**False Negatives:**
- `Restauração do pavimento asfáltico da avenida central`
- `Drenagem pluvial e pavimentação de ruas no bairro`

### Materiais Elétricos e Instalações (`materiais_eletricos`)

- **Precision:** 91.7%
- **Recall:** 73.3%
- **Keywords:** 61
- **Exclusions:** 37
- **Context gates:** 4

**False Positives:**
- `Construção de subestação com obra civil incluída` → matched: ['subestacao', 'subestação']

**False Negatives:**
- `Aquisição de cabos e fios elétricos para instalação predial`
- `Compra de fita isolante e conectores elétricos para manutenção`
- `Fornecimento de painéis elétricos para centro de distribuição`
- `Aquisição de medidores de energia elétrica e relés de proteção`

### Materiais Hidráulicos e Saneamento (`materiais_hidraulicos`)

- **Precision:** 100.0%
- **Recall:** 93.3%
- **Keywords:** 79
- **Exclusions:** 22
- **Context gates:** 6

**False Negatives:**
- `Fornecimento de caixas d'água e reservatórios de polietileno`

## Methodology

1. **Dataset:** 450 manually curated procurement descriptions (30 per sector)
2. **Pipeline:** `filter.py:match_keywords()` — keyword matching with exclusions, context gates, and word boundaries
3. **Classification:** Each item labeled as relevant (should match) or irrelevant (should not match)
4. **Metrics:** Precision = TP/(TP+FP), Recall = TP/(TP+FN)
5. **Threshold:** Precision >= 85%, Recall >= 70% per sector

## Changes Made (CRIT-FLT-009)

### sectors_data.yaml

1. **alimentos:** Added 8 animal feed exclusions (ração, alimentos para animais, etc.)
2. **engenharia_rodoviaria:** Added 14 traffic infrastructure keywords (rotatória, semáforo, ciclovia, etc.)
3. **materiais_hidraulicos:** Added 16 plural form keywords (tubos PVC, torneiras, mangueiras, etc.)
4. **facilities:** Added 10 services keywords (copeiragem, dedetização, lavanderia, etc.)
5. **facilities:** Removed pest control terms from exclusions (they are legitimate facilities services)
6. **manutencao_predial:** Added 9 building maintenance keywords (esquadrias, pintura interna/externa, etc.)

### Tests

- `backend/tests/test_precision_recall_benchmark.py` — 78 tests (15 parametrized + 63 edge cases)
- Ground truth: 450 labeled items (15 relevant + 15 irrelevant × 15 sectors)

---
*Report generated by `scripts/generate_benchmark_report.py` on 2026-02-22*