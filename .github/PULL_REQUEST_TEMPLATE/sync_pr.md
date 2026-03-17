# Sync skills from skills-catalog

This PR updates the managed skills under `{{target_path}}` from `{{source_repo}}` at commit `{{source_sha}}`.

**Target repo:** {{target_repo}}
**Target path:** {{target_path}}
**Source repo:** {{source_repo}}
**Source commit:** {{source_sha}}
**Sync metadata:** `{{sync_metadata_path}}`

**Skills included**
{{skills_bullets}}

Please run repo CI and perform a smoke check. If this is safe, merge.

If you need to revert:
- Revert this PR, or
- Restore the previous commit from the target repo.

Automated checks:
- [ ] CI passes
- [ ] Smoke test of local skill usage passes
