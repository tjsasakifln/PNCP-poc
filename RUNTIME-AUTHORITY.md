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
  bridge_status: engineering_ready_live_cutover_blocked
  tls_path: caddy_acme_san_apex_www_to_127.0.0.1:8765
  destination_ip: owner_supplied_BRIDGE_PUBLIC_IPV4
  bridge_rule: url_specific_redirects_only
  manifesto_sha256: c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d
  manifesto_commit: 3f112bfbd9e6b042691e1c09812af00f42735adb
  manifesto_commit_cited_after_68_rebase: dad3414c7a0073d0c1860d19704cff7e2a6e3b24
  execute_redirects: 11
  default_status: 410
  netcup_rebuild_authorized: false
observed_dns_2026_08_14:
  smartlic.tech: 69.46.46.88
  www.smartlic.tech: 69.46.46.117
  api.smartlic.tech: 1us7c4ob.up.railway.app
observed_http_2026_08_14:
  smartlic.tech: railway_edge_fallback_404
  www.smartlic.tech: tls_san_mismatch
  api.smartlic.tech: railway_edge_fallback_404
netcup_cleanup_2026_08_14:
  smartlic_units: not_found
  quarantined_units: /root/retired-smartlic-units-20260814
  retained_for_sunset_review: [/opt/smartlic, /etc/smartlic]
```

The DNS observations are evidence, not approval. Neither endpoint is a current
product runtime. No service may be rebuilt on Netcup merely to replace Railway.
