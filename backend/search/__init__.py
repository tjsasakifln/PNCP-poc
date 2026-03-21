"""search package — SYS-004 backend package grouping.

Provides a new import path for search-related modules:
  - search.pipeline (from search_pipeline)
  - search.cache (from search_cache)
  - search.context (from search_context)
  - search.state_manager (from search_state_manager)
  - search.consolidation (from consolidation)

All original import paths (e.g., ``from search_pipeline import X``)
continue to work via the unchanged top-level modules.
"""
