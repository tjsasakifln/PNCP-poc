# Upstream — aiox-kaizen-v2

Este squad é **vendored** (cópia congelada) do registry público:

- **Registry:** https://github.com/SynkraAI/aiox-squads
- **Source path:** `squads/kaizen-v2/`
- **Commit SHA:** `66118db856ef655b8cf5ba44eda963ad4d0b1d78`
- **Fetch date:** 2026-03-15
- **License:** ver `LICENSE` neste diretório (se presente) ou no registry upstream

## Por que vendored (não submodule)

- Registry sem release cadence formal
- Branch paralelo do SmartLic não deve introduzir submodule (vetor de drift em CI/pre-commit)
- Resync é operação consciente: `git clone https://github.com/SynkraAI/aiox-squads.git /tmp/aiox-sync && rsync -a /tmp/aiox-sync/squads/kaizen-v2/ /mnt/d/pncp-poc/squads/aiox-kaizen-v2/ --exclude='config/smartlic-overlay.yaml' --exclude='*.smartlic.md' --exclude='UPSTREAM.md'`

## Customização local (overlay)

- Arquivos com sufixo **`.smartlic.md`** são overlays locais — criados no SmartLic
- `config/smartlic-overlay.yaml` contém overrides B2G sem editar arquivos upstream
- Estes arquivos são ignorados no resync (rsync exclude acima)

## Exclusões intencionais do vendor



- Nenhuma — vendor completo

## Próxima revisão

Agendar via `aiox-kaizen-v2` trimestralmente. Se upstream publicar release com breaking change no schema, re-vendor em PR dedicado.
