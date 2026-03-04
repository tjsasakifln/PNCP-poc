# STORY-COPY-382: Corrigir inglês residual em emails e padronizar registro linguístico

**Prioridade:** P3 (polish — emails são touch points de retenção)
**Escopo:** `backend/templates/emails/alert_digest.py`, `backend/templates/emails/digest.py`
**Estimativa:** XS
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

Inglês residual nos templates de email: "Top oportunidades" (anglicismo desnecessário), valores sem formatação BR consistente.

- **Cluster 6 (Olivetto):** "O melhor texto é aquele que parece não ter autor" — inglês residual é marca de autor.
- **Cluster 7 (Settle):** Digest emails são retenção; cada detalhe diminui ou aumenta confiança.

## Critérios de Aceitação

- [ ] AC1: `alert_digest.py:240` — "Top oportunidades" → "Melhores oportunidades"
- [ ] AC2: Verificar todos os templates de email para inglês residual (buscar palavras em inglês)
- [ ] AC3: Confirmar que todos os acentos estão corretos nos templates (ver STORY-COPY-370 AC5)
- [ ] AC4: "Viabilidade media" → "Viabilidade média" em `_VIABILITY_COLORS`

## Copy Recomendada

```python
# alert_digest.py header
"Melhores oportunidades — {alert_name}"

# _VIABILITY_COLORS
"media": {"bg": "#fff8e1", "text": "#f57f17", "label": "Viabilidade média"},
```

## Princípios Aplicados

- **Olivetto (Copy Brasileira):** Consistência linguística e invisibilidade do autor
- **Settle (Email):** Digest emails são retenção; cada detalhe conta

## Evidência

- Atual: `alert_digest.py:22` — "Viabilidade media" sem acento
- Atual: `alert_digest.py:240` — "Top oportunidades" anglicismo
