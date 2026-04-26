# Contributing to BOSS Engine

Thank you for considering a contribution. BOSS is small and
deliberately opinionated — changes that broaden the governance
surface, weaken the invariants, or couple the core to a specific
vendor will be politely declined in the base product - but forks are possible. Changes that sharpen, test, or
document the existing spec are very welcome.
Book revisions are not needed for forks, but may be needed for some requests. Understand that the 'book' is multiple (more than 14) supporting Word files in the ADAM GitHub main.
ADAM GitHub: 
www.github.com/Hercamo/ADAM


## Ground rules

1. **The ADAM book is the spec.** If you think the math or the
   Exception Economy is wrong, open a discussion issue first —
   a PR that changes a formula without a book change is a
   non-starter.
2. **Load-bearing invariants must not break.** The eight
   invariants in [`tests/TESTING.md`](tests/TESTING.md) are
   enforced by unit tests. A PR that disables or relaxes any of
   them needs a written rationale and a book revision.
3. **Adapters stay thin.** LangGraph is our one deep integration.
   Every other adapter (OpenAI Agents, AI Foundry, CrewAI) is a
   translator. Do not pull vendor SDKs into `boss_core`.
4. **No network in tests.** Unit tests must complete in under one
   second on a laptop. API tests use `httpx.ASGITransport`; graph
   tests use `InMemoryGraph`.

## Development environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,test]"
pre-commit install

# Run everything CI runs:
make lint test
```

Node for the console:

```bash
cd boss_console
npm ci
npm run dev
```

## Style

- **Python**: formatted by `ruff format`, linted by `ruff check`,
  typed with `mypy --strict`. Bandit runs on every push.
- **TypeScript**: formatted by Prettier, linted by ESLint's
  recommended + `@typescript-eslint/recommended` rules.
- **Cypher**: one statement per paragraph, uppercase keywords,
  parameters prefixed with `$`.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`,
  `test:`, `refactor:`, `chore:`). Scope is optional; use the
  package name when useful (`feat(api): add /v1/config/tiers`).

## Branching and PRs

1. Fork, then branch off `main`: `git checkout -b feat/short-name`.
2. Commit early and often. Squash-merge is used on the server side.
3. Open a PR against `main`. The template asks for:
   - A short summary of *why*.
   - A checklist of affected invariants.
   - A test plan.
4. CI must be green. Reviewers will look for:
   - Tests exercising the change.
   - No new dependencies in `boss_core`.
   - No change to a load-bearing invariant without a book reference.

## Adding a framework

To add a compliance framework (for example, **NIST SP 800-53 R5**):

1. Add a node in `boss_graph/seed.cypher` with its canonical name,
   URL, and version.
2. Map its controls to one or more dimensions in the same file.
3. Add a test in `tests/test_api_health_and_config.py::test_frameworks`
   that asserts the new node is present after seeding.
4. Document the mapping in the reference manual (Part IX —
   Compliance Mapping).

## Adding an adapter

Adapters live in `boss_adapters/`. A new adapter must:

1. Implement the `BossAdapter` protocol in `boss_adapters/base.py`.
2. Translate the vendor's tool-call shape into
   `schemas.IntentObject`. If the vendor's shape cannot carry the
   full intent, document the gap.
3. Not import from the vendor's SDK directly — accept dicts and
   Pydantic models.
4. Ship a test in `tests/test_adapters.py` with at least one
   happy-path and one malformed-payload case.

## Licensing and DCO

By contributing you agree that your contributions are licensed
under the Apache License 2.0 (see `LICENSE`). Sign off each commit
with `git commit -s` — the DCO check on the PR requires a
`Signed-off-by:` trailer.

## Questions

- **Bug reports**: use the Issues template.
- **Security reports**: see [`SECURITY.md`](SECURITY.md) — do
  **not** open an issue.
- **Design discussion**: GitHub Discussions, or email
  `adam@adam-book.org`.
