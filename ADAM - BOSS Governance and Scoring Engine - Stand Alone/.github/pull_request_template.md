## Summary
<!-- What does this change do, and why? -->

## Governance checklist
- [ ] Scoring math unchanged, or changes documented in `docs/BOSS-Engine-Manual.md`
- [ ] Flight Recorder hash-chain semantics preserved (no new mutation path skips logging)
- [ ] Receipts remain append-only (no endpoints added that edit or delete receipts)
- [ ] New frameworks / regulations added to `boss_graph/seed.cypher` with provenance URLs
- [ ] Adapter changes tested against at least one worked example in `examples/`

## Tests
- [ ] `make check-all` passes locally
- [ ] New behavior has a unit test
- [ ] Any new endpoint appears in Schemathesis run (`make test-schema`)

## Rollout notes
<!-- Migrations, feature flags, config keys added, breaking changes, etc. -->
