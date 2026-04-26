# Security Policy

BOSS is a governance substrate. A vulnerability in BOSS is, by
construction, a vulnerability in the safety of every agent it
adjudicates. We take reports seriously.

## Supported versions

| Version | Supported |
| ------- | --------- |
| 3.2.x   | Yes       |
| 3.1.x   | Critical fixes only |
| < 3.1   | No        |

Security fixes are released as patch versions against the latest
minor line (currently `3.2.x`, tracking **BOSS Formulas v3.2** and
**ADAM v1.6**). Older minors receive fixes only for critical
(CVSSv4 ≥ 9.0) or OHSHAT-class (composite > 75) issues.

## Reporting a vulnerability

**Do not file a public GitHub issue for security bugs.** Instead:

1. Email **security@adam-book.org** with the subject line
   `[BOSS-ENGINE] <short description>`.
2. Include a proof-of-concept or, at minimum, a reproducible
   description.
3. Optionally encrypt with our PGP key (fingerprint published on
   the ADAM book repository's `SECURITY.md` root).

You will receive acknowledgement within **2 business days** and a
triage decision within **7 calendar days**. We follow [coordinated
disclosure](https://about.gitlab.com/handbook/security/disclosure/)
and will work with you on a disclosure timeline, normally 90 days
from acknowledgement.

## What qualifies

In scope:

- Authentication/authorization bypass in the REST API.
- Tamper-detection bypass in the Flight Recorder hash chain
  (including hash-chain forks or reorder attacks that still verify).
- Composite-score manipulation that causes a true OHSHAT intent to
  route below OHSHAT (or vice versa) via crafted input.
- Injection through any adapter (LangGraph/OpenAI/AI Foundry/CrewAI)
  that escapes the `boss_guard` translation layer.
- Credential exposure, SSRF, RCE, or SQL/Cypher injection in
  `boss_graph`.
- Dependency vulnerabilities that are actually reachable from BOSS
  code (not transitive CVEs that only affect unused surfaces).

Out of scope:

- Self-XSS, clickjacking on a page without sensitive actions.
- DoS requiring > 10× normal traffic that is not addressable at the
  library level.
- Missing security headers on local development servers.
- Issues that require a malicious director with write access to the
  tier configuration — that is a governance failure, not a
  technical vulnerability.

## Rewards

This project is research-grade, not a commercial product. We do not
offer a cash bounty. We do offer:

- Credit in `CHANGELOG.md` and the reference manual's acknowledgements.
- A named hash-chain "genesis" entry in a published ADAM release —
  your Flight Recorder event becomes part of the permanent record.

## Threat model assumptions

BOSS assumes:

- The **process running `boss_api`** is trusted; anything with code
  execution on that host can forge hashes.
- The **Neo4j/graph store** is integrity-protected by its operator.
  If your attacker can write to the `Receipt` relationship directly,
  they can overwrite evidence — run Neo4j with audit logging and
  append-only replicas.
- The **Flight Recorder file path** (`BOSS_FLIGHT_RECORDER_PATH`)
  is owned by the API's service account with `0600` permissions.
- **JWT verification** (when `BOSS_REQUIRE_JWT=1`) is done against
  the configured issuer — we do not ship a default issuer.

BOSS does **not** assume:

- That adapter inputs are well-formed. Every adapter path normalizes
  through `schemas.IntentObject` and rejects malformed payloads
  with a structured error.
- That the clock is monotonic. Receipts record wall time but chain
  integrity is clock-independent.
