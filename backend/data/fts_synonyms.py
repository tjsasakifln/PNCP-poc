"""STORY-5.4 (TD-SYS-015): Portuguese-BR legal/procurement synonyms map.

Used by `datalake_query.expand_synonyms()` to widen `to_tsquery` / websearch
input BEFORE it reaches PostgreSQL. Supabase Cloud doesn't expose the
`$SHAREDIR/tsearch_data` filesystem, so synonym dictionaries at the DB level
are not available to us. Query rewriting in Python is the practical
equivalent: each canonical term expands into `(term | synonym1 | synonym2)`
at query build time.

Design choices:

- Keys are already lowercased, accent-preserved canonical forms.
- Values include both accented and unaccented variants (Postgres 'portuguese'
  config keeps accents; the `public.portuguese_smartlic` config we register in
  migration `20260415000001_fts_portuguese_smartlic.sql` adds an `unaccent`
  filter so both forms match the same lexeme — but until that migration is
  deployed everywhere the redundant unaccented alt buys robustness).
- Curated conservatively — false-positive broadening is a precision killer
  in FTS ranking. Start with ~50 terms covering the big-4: modalidade,
  objeto, esfera, tipo-licitação.
- NOT a bi-directional map. "pregao" expands to its family; reverse lookup
  is NOT needed (we only rewrite incoming queries, never labels).

When adding a new synonym group, keep it in the comment block near the top
of the group so reviewers see intent.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Modalidade — the variant explosion is the most common mismatch source.
# ---------------------------------------------------------------------------

_MODALIDADE = {
    "pregao": ("pregão", "pregao_eletronico", "pregão_eletrônico", "pregao_presencial"),
    "pregão": ("pregao", "pregao_eletronico", "pregão_eletrônico"),
    "concorrencia": ("concorrência", "concorrencia_publica", "concorrência_pública"),
    "concorrência": ("concorrencia", "concorrencia_publica"),
    "dispensa": ("dispensa_eletrônica", "dispensa_eletronica", "dispensa_de_licitacao"),
    "inexigibilidade": ("inexigibilidade_de_licitacao", "inexigibilidade_de_licitação"),
    "chamamento": ("chamamento_publico", "chamamento_público"),
    "credenciamento": ("credenciamento_publico", "credenciamento_público"),
    "leilao": ("leilão", "leilao_publico", "leilão_público"),
    "rdc": ("regime_diferenciado_de_contratacoes",),
    "srp": ("sistema_de_registro_de_precos", "sistema_de_registro_de_preços"),
}

# ---------------------------------------------------------------------------
# Objeto de contratação — high-recall expansions (safer than precision ones).
# ---------------------------------------------------------------------------

_OBJETO = {
    "aquisicao": ("aquisição", "compra", "fornecimento"),
    "aquisição": ("aquisicao", "compra", "fornecimento"),
    "contratacao": ("contratação", "prestacao", "prestação"),
    "contratação": ("contratacao", "prestacao"),
    "servicos": ("serviços",),
    "serviços": ("servicos",),
    "obras": ("obra", "empreitada"),
    "construcao": ("construção",),
    "construção": ("construcao",),
    "manutencao": ("manutenção", "conservacao", "conservação"),
    "manutenção": ("manutencao",),
    "reforma": ("reformulacao", "reformulação"),
    "pavimentacao": ("pavimentação", "recapeamento"),
    "pavimentação": ("pavimentacao",),
    "limpeza": ("higienizacao", "higienização", "conservacao", "conservação"),
    "transporte": ("locomocao", "locomoção", "frete"),
    "alimentacao": ("alimentação", "merenda", "refeicao", "refeição"),
    "alimentação": ("alimentacao", "merenda"),
    "saude": ("saúde",),
    "saúde": ("saude",),
    "educacao": ("educação", "ensino"),
    "educação": ("educacao", "ensino"),
    "seguranca": ("segurança", "vigilancia", "vigilância"),
    "segurança": ("seguranca",),
}

# ---------------------------------------------------------------------------
# Esfera / tipo — short list, low risk.
# ---------------------------------------------------------------------------

_ESFERA = {
    "federal": ("uniao", "união", "federativa"),
    "estadual": ("estado",),
    "municipal": ("municipio", "município", "prefeitura"),
    "prefeitura": ("municipal", "municipio", "município"),
    "autarquia": ("autarquico", "autárquico"),
    "fundacao": ("fundação",),
    "fundação": ("fundacao",),
}

# ---------------------------------------------------------------------------
# Consolidated lookup — all sections merged. Importers use only this.
# ---------------------------------------------------------------------------

SYNONYMS: dict[str, tuple[str, ...]] = {
    **_MODALIDADE,
    **_OBJETO,
    **_ESFERA,
}


def expand_term(term: str) -> tuple[str, ...]:
    """Return (term, *synonyms) for a single lowercased term.

    Caller responsibility to lowercase the input. Accent is preserved (we
    store both accented and unaccented as keys where relevant, so lookup is
    O(1) and doesn't depend on normalization order).

    If the term has no entry, returns just `(term,)`.
    """
    expansions = SYNONYMS.get(term)
    if not expansions:
        return (term,)
    # Deduplicate while preserving order (term first).
    seen = [term]
    for s in expansions:
        if s not in seen:
            seen.append(s)
    return tuple(seen)
