# ADAM Runtime Governance Interface — Compliance Checklist

**Use this checklist when adopting an alternative runtime implementation instead of AGT.**

Version 1.0 | April 2026 | ADAM AGT Light Plugin

---

## Checklist Purpose

Any runtime enforcement framework adopted for ADAM must satisfy the five RGI (Runtime Governance Interface) domains. This checklist documents the compliance posture for alternative implementations. Complete one checklist per runtime implementation.

If any domain is marked ❌ or ⚠️, the gap must be documented as a BOSS Security Impact risk acceptance record and logged to the Flight Recorder with compensating controls specified.

---

## RGI-01: Policy Enforcement

**Requirement**: Intercept every agent action at the invocation boundary; evaluate against active policies; permit, deny, or escalate in <0.1ms p99.

| Criterion | AGT Answer | Your Implementation |
|---|---|---|
| Actions intercepted at invocation boundary (not just scheduling) | ✅ Agent OS sidecar | |
| Evaluation latency p99 target | ✅ <0.1ms | |
| Fail-closed default (deny if policy evaluation fails) | ✅ | |
| YAML / Rego / Cedar policy format support | ✅ All three | |
| CORE Engine Rego export compatible | ✅ | |
| Integration with BOSS Score gate | ✅ | |

**Compliance Status**: [ ] Fully Satisfied  [ ] Partially Satisfied (document gaps below)  [ ] Not Satisfied

**Gaps and Compensating Controls**:
```
[Document any deviations and how they are compensated]
```

---

## RGI-02: Agent Identity

**Requirement**: Issue and verify non-forgeable cryptographic identity for every agent; support mTLS between agents; revoke compromised identities without service interruption.

| Criterion | AGT Answer | Your Implementation |
|---|---|---|
| Non-forgeable cryptographic identity per agent | ✅ DIDs + Ed25519 | |
| Identity scheme | ✅ W3C DID (did:azure) | |
| Revocation without service interruption | ✅ DID revocation registry | |
| mTLS between all agent pods | ✅ Istio + Agent Mesh | |
| Continuous trust re-evaluation (per-interaction) | ✅ IATP 0-1000 score | |
| Trust score for Two-Dimensional Trust Model | ✅ 0-1000 scale | |

**Note on Trust Scoring**: If your implementation does not provide a continuous 0-1000 trust score per agent, the Two-Dimensional Trust Model (BOSS Score + Agent Trust) must be documented as partially implemented. BOSS Score alone remains the primary governance control; agent trust scoring becomes a binary trusted/untrusted determination.

**Compliance Status**: [ ] Fully Satisfied  [ ] Partially Satisfied  [ ] Not Satisfied

---

## RGI-03: Execution Containment

**Requirement**: Enforce privilege boundaries on agent execution; prevent lateral movement; support emergency shutdown.

| Criterion | AGT Answer | Your Implementation |
|---|---|---|
| Privilege containment model | ✅ 4-ring (0-3) | |
| Cross-privilege escalation architecturally blocked | ✅ Admission controller | |
| Emergency shutdown (OHSHAT-tier aligned) | ✅ Kill switch | |
| Compensating transaction / saga support for rollback | ✅ Agent Runtime sagas | |
| Ring assignments stored in CORE Graph Agent vertices | ✅ | |

**Alternative Minimum**: If a 4-ring model is not used, document the privilege model and map to ADAM's authority levels (Meta-Governance, Governor Agent, Orchestration, Work Group).

**Compliance Status**: [ ] Fully Satisfied  [ ] Partially Satisfied  [ ] Not Satisfied

---

## RGI-04: Telemetry Emission

**Requirement**: Emit structured audit events for every action evaluation; include BOSS Score inputs; OpenTelemetry-compatible; Flight Recorder integration required.

| Criterion | AGT Answer | Your Implementation |
|---|---|---|
| OpenTelemetry W3C trace context compatible | ✅ | |
| intent_id propagated in baggage | ✅ | |
| agent_id propagated in baggage | ✅ | |
| BOSS Score dimension inputs emitted | ✅ Security Impact, Regulatory Impact | |
| ADAM RGI-04 adapter available | ✅ ADAM-proprietary (included in plugin) | |
| Quantitative SLOs and error budgets | ✅ Agent SRE | |
| Circuit breaker state emitted | ✅ | |

**Mandatory**: An ADAM-proprietary RGI-04 adapter is required regardless of runtime implementation. The adapter bridges OpenTelemetry spans to Flight Recorder event format with hash-chaining and HSM signing. If using an alternative runtime, extend the RGI-04 adapter's event type mapping configuration.

**Compliance Status**: [ ] Fully Satisfied  [ ] Partially Satisfied  [ ] Not Satisfied

---

## RGI-05: Tool and Plugin Governance

**Requirement**: Verify integrity of all external tools and plugins before agent invocation; maintain signed manifest registry; support revocation.

| Criterion | AGT Answer | Your Implementation |
|---|---|---|
| Signed manifests required for all external tools | ✅ Ed25519 | |
| Trusted publisher key registry | ✅ | |
| Revocation registry checked before invocation | ✅ | |
| MCP v2 tool invocation contract compatible | ✅ | |
| Unsigned tool invocation blocked (not just logged) | ✅ | |

**Compliance Status**: [ ] Fully Satisfied  [ ] Partially Satisfied  [ ] Not Satisfied

---

## Summary

| RGI Domain | Status | BOSS Risk Acceptance Required? |
|---|---|---|
| RGI-01: Policy Enforcement | | |
| RGI-02: Agent Identity | | |
| RGI-03: Execution Containment | | |
| RGI-04: Telemetry Emission | | |
| RGI-05: Tool/Plugin Governance | | |

**Overall Compliance**: [ ] All five domains fully satisfied  [ ] Partial (BOSS risk acceptance completed)  [ ] Non-compliant (do not deploy to production)

**Completed by**:
**Date**:
**Runtime implementation name and version**:
**Reviewed by (CISO or designate)**:
