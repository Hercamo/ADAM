# ADAM-AGT Plugin Integration Artifacts

This directory contains technical configuration and schema files for the ADAM-AGT Plugin, which integrates the Microsoft Agent Governance Toolkit (AGT) with ADAM's autonomous enterprise governance framework.

## Overview

The ADAM-AGT Plugin bridges two major systems:
- **ADAM** (Autonomous Decision Architecture Model): Enterprise governance model with CORE Engine, BOSS Score, 81-Agent Mesh, and Flight Recorder
- **AGT** (Agent Governance Toolkit): Microsoft's 7-package agent runtime providing policy enforcement, trust mesh, compliance, and SRE capabilities

## File Structure

### Configuration Files (`config/`)

1. **adam-agt-plugin-manifest.json** (6.5 KB)
   - Plugin definition and metadata
   - AGT package dependencies
   - Deployment targets (K8s, Docker, bare-metal)
   - Package registry configuration
   - Integration points with ADAM components

2. **agt-policy-engine-config.yaml** (11.1 KB)
   - AGT Agent OS integration with ADAM's Policy & Risk Plane
   - Policy language support (YAML, OPA Rego, Cedar)
   - BOSS score thresholds triggering policy enforcement
   - Latency targets (<0.1ms p99)
   - Escalation routing to Exception Economy
   - Audit logging and versioning

3. **agt-agent-mesh-config.yaml** (11.7 KB)
   - AGT Agent Mesh integration with ADAM's 81-agent topology
   - DID (Decentralized Identity) configuration for agent identity
   - Ed25519 key management and X25519 encryption
   - Inter-Agent Trust Protocol (IATP) settings
   - Trust scoring (0-1000 scale mapped to ADAM authority levels)
   - mTLS/A2A protocol configuration
   - Network segmentation and chaos engineering

4. **agt-runtime-config.yaml** (13.1 KB)
   - AGT Agent Runtime with ADAM's orchestration plane
   - Execution ring definitions (Ring 0-4) mapped to ADAM's 5 agent layers
   - Saga orchestration with ADAM's 4 enforcement hooks
   - Kill switch triggers mapped to BOSS OHSHAT tier
   - Recovery strategies (retry, failover, circuit breaker, compensation, escalation)
   - Resource management and execution limits

5. **agt-sre-config.yaml** (12.5 KB)
   - Agent SRE configuration for ADAM's 81-agent mesh
   - Service Level Objectives (SLOs) per agent class
   - Error budget allocation and tracking
   - Circuit breaker configuration
   - Chaos engineering scenarios for resilience testing
   - Incident response integration
   - Post-incident review and continuous improvement

6. **agt-compliance-config.yaml** (15.1 KB)
   - Agent Compliance mapping to regulatory frameworks
   - EU AI Act, DORA, NIS2, Singapore IMDA, HIPAA, SOC2 alignment
   - BOSS Regulatory dimension feed
   - Automated compliance checking and audit report generation
   - Continuous monitoring and remediation tracking
   - Flight Recorder evidence integration

### Schema Files (`schemas/`)

All schemas use JSON Schema Draft-07 format with comprehensive documentation and examples.

1. **adam-agt-trust-score-schema.json** (17.9 KB)
   - Trust score format for AGT agent mesh integrated with ADAM BOSS
   - Two-dimensional trust surface:
     - **Agent Trust (0-1000)**: Evaluates agent reliability/compliance
     - **BOSS Score (0-100)**: Evaluates action context/risk
   - Authority level mapping based on trust score
   - Factor-based trust scoring (latency, compliance, errors, anomalies, security incidents)
   - Trust trend analysis and history
   - Hash-chain linkage to Flight Recorder
   - Escalation paths and approval workflows

2. **adam-agt-policy-contract-schema.json** (19.4 KB)
   - Policy contracts bridging AGT Agent OS with ADAM invocation contracts
   - ADAM policy provenance tracking
   - BOSS score thresholds for policy activation
   - Autonomy budget impact calculation
   - ADAM's 4 enforcement hooks integration:
     - Pre-decision validation
     - During-execution monitoring
     - Post-completion validation
     - Exception handling and escalation
   - AGT Agent OS metadata and enforcement config
   - Testing, validation, and audit trail
   - Cryptographic signature and verification

3. **adam-agt-evidence-record-schema.json** (17.1 KB)
   - Evidence records for AGT enforcement actions feeding Flight Recorder
   - Hash-chain linkage fields for immutability
   - WORM (Write-Once-Read-Many) compliance markers
   - Cross-reference to ADAM intent objects
   - Record types: policy enforcement, BOSS updates, agent actions, escalations, trust changes, budget usage, compliance checks, kill switches, sagas, audits, security incidents
   - Support for all regulatory frameworks (EU AI Act, DORA, NIS2, HIPAA, SOC2)
   - Director Constitution context
   - Audit-suitable content for compliance reporting

## Key Integration Concepts

### ADAM Components Referenced

- **CORE Engine**: Policy repository and company culture encoding
- **BOSS Score**: 7-dimension risk assessment (0-100 scale) with 5 escalation tiers
  - SOAP (0-20): Safe and operational
  - MODERATE (21-40): Monitor closely
  - ELEVATED (41-60): Elevated caution required
  - CRITICAL (61-80): Critical monitoring
  - OHSHAT (81-100): Emergency situation

- **81-Agent Mesh**: 5-layer topology
  - Intent/Human Interface Layer (5 agents)
  - Domain Governors/Super Agents (12 agents)
  - Orchestration Layer (24 agents)
  - Work Group Agents (32 agents)
  - Digital Twins/Meta-Governance (8 agents)

- **Policy & Risk Plane**: Runtime policy enforcement
- **Security & Trust Plane**: Identity, access, trust boundaries
- **Flight Recorder**: Hash-chained WORM evidence logging
- **Exception Economy**: Autonomy budgets and escalation routing
- **5-Director Constitution**: CEO, CFO, Legal, Market, CISO

### AGT Components Referenced

- **Agent OS**: Policy engine with multi-language support
- **Agent Mesh**: Cryptographic identity and trust protocols
- **Agent Runtime**: Execution rings, sagas, kill switch
- **Agent SRE**: SLO enforcement, error budgets, chaos engineering
- **Agent Compliance**: Regulatory mapping and audit reports
- **Agent Marketplace**: Plugin signing and verification
- **Agent Lightning**: Reinforcement learning governance

## Configuration Relationships

```
adam-agt-plugin-manifest.json (entry point)
├── agt-policy-engine-config.yaml
│   ├── CORE Engine integration
│   ├── Policy & Risk Plane
│   └── BOSS score thresholds
│
├── agt-agent-mesh-config.yaml
│   ├── 81-Agent Mesh topology
│   ├── DID identity system
│   └── Inter-agent trust protocols
│
├── agt-runtime-config.yaml
│   ├── Execution rings (5 layers)
│   ├── Saga orchestration
│   ├── Kill switch triggers
│   └── Recovery strategies
│
├── agt-sre-config.yaml
│   ├── SLOs per agent class
│   ├── Error budgets
│   └── Chaos scenarios
│
├── agt-compliance-config.yaml
│   ├── Regulatory frameworks
│   ├── BOSS dimension mapping
│   └── Audit report generation
│
└── schemas/
    ├── adam-agt-trust-score-schema.json
    │   └── Trust surface (agent trust × BOSS context)
    ├── adam-agt-policy-contract-schema.json
    │   └── Policy definition with enforcement metadata
    └── adam-agt-evidence-record-schema.json
        └── Flight Recorder evidence integration
```

## Validation

All files have been validated:
- ✓ All JSON files conform to JSON Schema Draft-07
- ✓ All YAML files are syntactically valid
- ✓ Cross-references between files are consistent
- ✓ All ADAM and AGT concepts are properly mapped

## Statistics

- **Total Files**: 9 (6 config + 3 schemas)
- **Total Lines of Code**: 8,573
- **Total Size**: 124.4 KB
- **Format**: Production-quality with inline documentation
- **Comments**: Extensive (>40% of YAML content)

## Usage

These artifacts are used in the ADAM Book's technical chapters on:
1. **AGT Integration Architecture**
2. **Policy Enforcement and Compliance**
3. **Agent Identity and Trust**
4. **Autonomous Execution and Recovery**
5. **Regulatory Alignment**

They serve as reference implementations for enterprises building autonomous governance systems using ADAM and AGT.

## Related Documentation

- ADAM Book v0.4 core concepts
- AGT Package Documentation (7 packages)
- NetStreamX case study examples
- BOSS Score calculation methodology
- Flight Recorder evidence chain procedures
