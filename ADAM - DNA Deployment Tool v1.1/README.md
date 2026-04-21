# ADAM DNA Deployment Tool

**Autonomy Doctrine & Architecture Model — DNA Deployment Specification Generator**

Version 1.1 | April 2026 — aligned with the current ADAM Book and canonical BOSS scoring (Section 1.3 directive: version tokens stripped from in-text cross-references; resolve to latest named artifact).

## Overview

This tool reads a completed ADAM DNA Questionnaire (.docx) and generates comprehensive DNA Deployment Specifications for all supported platforms. It extracts all 13 sections of the questionnaire and produces Infrastructure-as-Code templates, configuration bundles, and professional Word documents tailored to each deployment target.

## Supported Platforms

| Platform | IaC Format | Description |
|----------|-----------|-------------|
| **Azure** | Terraform + Bicep | Primary cloud deployment with full ADAM governance plane |
| **AWS** | Terraform + CloudFormation | Warm standby or primary alternative |
| **Google Cloud** | Terraform | Full GCP-native deployment |
| **Kubernetes** | Helm + Kustomize + YAML | Open source deployment on any K8s cluster |
| **Azure Local** | Bicep + Scripts | On-premises failover (survival mode, 30% capacity) |

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Generate for specific platforms
python adam_dna_tool.py --input questionnaire.docx --platforms azure,aws

# Generate for all platforms
python adam_dna_tool.py --input questionnaire.docx --platforms all

# Custom output directory
python adam_dna_tool.py --input questionnaire.docx --platforms k8s --output ./my-output

# Verbose mode
python adam_dna_tool.py --input questionnaire.docx --platforms all --verbose
```

## Generated Output

For each platform, the tool generates:

1. **Word Document (.docx)** — Professional deployment specification with architecture details, BOSS scoring config, agent registry, and deployment procedures
2. **Infrastructure-as-Code** — Ready-to-deploy Terraform, Bicep, CloudFormation, or Helm templates
3. **Configuration Bundle** — JSON/YAML configs including CORE Graph seed data, BOSS policies (OPA/Rego), agent registry, Intent Object schemas, and governance configuration

## ADAM Architecture Components

- **CORE Engine** — Culture, Objectives, Rules, Expectations graph database
- **BOSS Scoring** — 7-dimension Business Operations Sovereignty Score (0-100)
- **81+ Agent Mesh** — 7 canonical classes: Meta-Governance, Governor Agent, Orchestration, Human Interface, Digital Twin, Corporate Work Group, AI-Centric Division
- **Flight Recorder** — Immutable, hash-chained evidence store
- **Cryptographic Vault** — HSM-backed authorization proofs
- **Exception Economy** — Human directors manage exceptions, not workflows

## DNA Questionnaire Sections

1. Doctrine Identity & Constitutional Foundation
2. CORE Engine — Culture Graph
3. CORE Engine — Objectives Graph
4. CORE Engine — Rules & Expectations Graph
5. CORE Subgraphs — Enterprise Memory
6. BOSS Scoring & Exception Economy Configuration
7. Intent Object & Doctrine Conflict Configuration
8. Agentic Architecture & Domain Configuration
9. Flight Recorder & Evidence Architecture
10. Products, Services & Operational Domain
11. Temporal & Regional Variance Configuration
12. Cloud Infrastructure Sizing & Sovereignty Architecture
13. Resilience, Idempotency & Security Posture
