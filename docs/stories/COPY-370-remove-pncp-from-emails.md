# STORY-COPY-370: Remover "Ver no PNCP" dos emails e substituir por copy neutra

**Prioridade:** P0 (violação de regra)
**Escopo:** `backend/templates/emails/alert_digest.py`, `backend/templates/emails/digest.py`
**Estimativa:** XS
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

A regra do CLAUDE.md é explícita: mencionar "PNCP" em texto voltado ao usuário é PROIBIDO. Os emails de digest exibem "Ver no PNCP →" como link para cada oportunidade, e o footer diz "Viability badges indicam a relevancia" (mistura de inglês com português sem acento).

- **Cluster 6 (Copy Brasileira):** "Viability badges" num email PT-BR é falha grave de registro linguístico.
- **Cluster 2 (UX Writing):** Nenhum termo técnico interno deve vazar para o usuário.

## Critérios de Aceitação

- [ ] AC1: `_render_pncp_link()` retorna "Ver edital completo →" em vez de "Ver no PNCP →"
- [ ] AC2: Footer dos emails substitui "Viability badges indicam a relevancia da oportunidade para seu perfil." por "Os indicadores de viabilidade mostram a compatibilidade da oportunidade com seu perfil."
- [ ] AC3: Docstrings internas podem manter "PNCP" (não é user-facing), mas HTML renderizado não
- [ ] AC4: `alert_digest.py` e `digest.py` ambos corrigidos
- [ ] AC5: Acentos corrigidos em todo o template: "Ola" → "Olá", "nao" → "não", "titulo" → "título", "Orgao" → "Órgão", "numero" → "número", "preferencias" → "preferências", "relevancia" → "relevância", "diario" → "diário", "configuracoes" → "configurações"

## Copy Recomendada

```python
# _render_pncp_link (renomear para _render_edital_link)
f'Ver edital completo &rarr;</a></p>'

# Footer
"Os indicadores de viabilidade mostram a compatibilidade da oportunidade com seu perfil."
```

## Princípios Aplicados

- **Olivetto (Copy Brasileira):** Consistência linguística e invisibilidade do autor
- **Podmajersky (UX Writing):** Nenhum termo técnico interno deve vazar para o usuário

## Evidência

- Atual: `alert_digest.py:137` — "Ver no PNCP" user-facing
- Atual: `alert_digest.py:257`, `digest.py:211` — "Viability badges" em email PT-BR
- Regra CLAUDE.md: "Mentioning PNCP or source names to users is BANNED"
