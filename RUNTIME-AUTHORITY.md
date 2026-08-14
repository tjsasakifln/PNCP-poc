# Runtime authority: SmartLic

```yaml
authority_version: 1
effective_at: 2026-08-14
decision: ADR-STRAT-002
smartlic:
  role: legacy_migration_source
  permanent_runtime: none
  product_deployment: forbidden
  public_canonical: false
canonical_public:
  domain: confenge.com.br
  repository: tjsasakifln/web-cfg
migration:
  owners:
    - https://github.com/tjsasakifln/web-cfg/issues/62
    - https://github.com/tjsasakifln/SmartLic/issues/2115
  bridge_status: target_not_yet_authorized
  bridge_rule: url_specific_redirects_only
  netcup_rebuild_authorized: false
observed_dns_2026_08_14:
  smartlic.tech: 69.46.46.88
  api.smartlic.tech: 1us7c4ob.up.railway.app
observed_http_2026_08_14:
  smartlic.tech: railway_edge_fallback_404
  api.smartlic.tech: railway_edge_fallback_404
netcup_cleanup_2026_08_14:
  smartlic_units: not_found
  quarantined_units: /root/retired-smartlic-units-20260814
  retained_for_sunset_review: [/opt/smartlic, /etc/smartlic]
```

The DNS observations are evidence, not approval. Neither endpoint is a current
product runtime. No service may be rebuilt on Netcup merely to replace Railway.
