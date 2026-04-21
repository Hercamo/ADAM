# ADAM DNA Tool

**AI-Powered Conversational Engine for Autonomy Doctrine & Architecture Model Configuration**

Version 1.1.0 | April 2026
Aligned to ADAM book v1.4 (canonical 5 Governor Agents, BOSS v3.2 weights, 81+ Agent Mesh, Seven Cross-Cutting Planes, Three-Tier Sovereignty, 8 SEAL Objectives).

## Overview

The ADAM DNA Tool replaces the static ADAM DNA Questionnaire with an intelligent, AI-powered conversational interface. Instead of manually filling out a 13-section questionnaire, users upload their existing strategy documents, financial reports, compliance docs, and org charts — the AI analyzes them, extracts relevant information, asks targeted follow-up questions, and builds the complete DNA configuration interactively.

The tool produces a DNA JSON that feeds directly into the existing **ADAM DNA Deployment Tool** to generate Infrastructure-as-Code, configuration bundles, and deployment specifications for any supported platform.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ADAM DNA Tool                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │   React UI   │───▶│   FastAPI Backend             │  │
│  │  Chat + Prog │    │                              │  │
│  │  + Deploy    │◀───│  ┌──────────┐ ┌───────────┐  │  │
│  └──────────────┘    │  │ AI Engine│ │Doc Ingest │  │  │
│                      │  │ OpenAI   │ │DOCX/PPTX  │  │  │
│                      │  │ Claude   │ │PDF/CSV    │  │  │
│                      │  │ Azure AI │ │URL Fetch  │  │  │
│                      │  └──────────┘ └───────────┘  │  │
│                      │                              │  │
│                      │  ┌──────────┐ ┌───────────┐  │  │
│                      │  │DNA Build │ │Deploy     │  │  │
│                      │  │JSON Gen  │─│Bridge     │──┼──┼──▶ DNA Deployment Tool
│                      │  └──────────┘ └───────────┘  │  │    (IaC, Configs, Docs)
│                      └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Features

- **Conversational AI Interface** — Chat-based interaction powered by OpenAI GPT-4o, Anthropic Claude, or Azure OpenAI
- **Document Ingestion** — Upload DOCX, PPTX, PDF, CSV, JSON, XLSX files or fetch from URLs
- **Intelligent Extraction** — AI analyzes uploaded documents and pre-fills DNA sections automatically
- **13-Section DNA Coverage** — Complete coverage of all ADAM DNA Questionnaire sections
- **Real-Time Progress Tracking** — Visual sidebar showing section completion percentages
- **DNA Validation** — Validates completeness and consistency before deployment
- **Deployment Integration** — Directly triggers the ADAM DNA Deployment Tool for artifact generation
- **Multi-Platform Support** — Azure, AWS, GCP, Kubernetes, Azure Local (on-premises)
- **Kubernetes-Native** — Helm charts for deployment on any cloud or on-premises K8s cluster

## Quick Start

### Prerequisites
- Docker & Docker Compose (for local development)
- An API key for at least one AI provider (OpenAI, Anthropic, or Azure OpenAI)

### Local Development

```bash
# 1. Navigate to the tool directory
cd "ADAM DNA TOOL"

# 2. Copy environment file and add your API keys
cp .env.example .env
# Edit .env and set OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Launch with Docker Compose
docker compose up --build

# 4. Open in browser
open http://localhost:3000
```

### Kubernetes Deployment

```bash
# 1. Create a Kubernetes secret with your API keys
kubectl create secret generic adam-dna-secrets \
  --from-literal=OPENAI_API_KEY='sk-your-key' \
  --from-literal=ANTHROPIC_API_KEY='sk-ant-your-key' \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)"

# 2. Install with Helm
helm install adam-dna ./k8s/helm/adam-dna-tool \
  --set ingress.hosts[0].host=adam-dna.your-domain.com \
  --set backend.env.AI_PROVIDER=openai

# 3. Verify
kubectl get pods -l app.kubernetes.io/name=adam-dna-tool
```

## Project Structure

```
ADAM DNA TOOL/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── api/
│   │   │   └── routes.py      # REST + WebSocket API endpoints
│   │   ├── ai/
│   │   │   ├── providers.py   # OpenAI/Anthropic/Azure provider abstraction
│   │   │   └── adam_system_prompt.py  # ADAM knowledge base & prompt builder
│   │   ├── core/
│   │   │   └── config.py      # Application configuration (env vars)
│   │   ├── dna/
│   │   │   └── dna_builder.py # DNA JSON builder & export
│   │   ├── ingestion/
│   │   │   └── document_processor.py  # File upload & URL processing
│   │   ├── models/
│   │   │   └── session.py     # Session, DNA state, progress models
│   │   └── services/
│   │       ├── conversation_engine.py # AI conversation orchestrator
│   │       └── deployment_bridge.py   # Bridge to DNA Deployment Tool
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React + Tailwind frontend
│   ├── src/
│   │   ├── App.jsx            # Main application with phase management
│   │   ├── components/
│   │   │   ├── Header.jsx     # Top bar with progress & AI provider
│   │   │   ├── Sidebar.jsx    # Phase navigation & document list
│   │   │   ├── ChatPanel.jsx  # Conversational chat interface
│   │   │   └── DeployPanel.jsx # Deployment configuration & trigger
│   │   └── services/
│   │       └── api.js         # API client for backend communication
│   ├── Dockerfile
│   └── package.json
├── k8s/                        # Kubernetes deployment
│   └── helm/
│       └── adam-dna-tool/     # Helm chart
│           ├── Chart.yaml
│           ├── values.yaml    # Configuration values
│           └── templates/     # K8s manifests
├── docker-compose.yaml         # Local development compose
├── .env.example               # Environment variable template
└── README.md                  # This file
```

## DNA Configuration Process

The tool walks users through these phases:

1. **Document Ingestion** — Upload strategy docs, financial reports, compliance docs, org charts
2. **Section 1: Doctrine Identity** — Mission, vision, principles, sacred boundaries, director roles
3. **Section 2: Culture Graph** — Values as trade-offs, behavioral norms, public vs internal posture
4. **Section 3: Objectives Graph** — Mandates, goals, aspirational objectives
5. **Section 4: Rules & Expectations** — Hard rules (zero tolerance) and soft expectations
6. **Section 5: Enterprise Memory** — Financial, rights, customer, regulatory, strategy drift subgraphs
7. **Section 6: BOSS Scoring** — Dimension weights, routing thresholds, exception economy
8. **Section 7: Intent & Conflict** — Risk tolerances, urgency levels, doctrine conflict arbitration
9. **Section 8: Agent Architecture** — Domain governor config, work groups, digital twins
10. **Section 9: Flight Recorder** — Evidence retention, tamper-evidence, audit requirements
11. **Section 10: Products & Services** — Product inventory, ecosystem, competitive differentiation
12. **Section 11: Temporal & Regional** — Seasonal patterns, regional overrides
13. **Section 12: Cloud Infrastructure** — Multi-cloud topology, compute sizing, sovereignty
14. **Section 13: Resilience & Security** — Disaster posture, idempotency, threat model
15. **Review & Validate** — Comprehensive DNA review and gap analysis
16. **Deploy** — Generate deployment artifacts for selected platforms

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions` | Create new DNA configuration session |
| GET | `/api/sessions/{id}` | Get session state and progress |
| POST | `/api/sessions/{id}/messages` | Send a message to the AI assistant |
| POST | `/api/sessions/{id}/upload` | Upload a document for analysis |
| POST | `/api/sessions/{id}/fetch-url` | Fetch and analyze content from a URL |
| POST | `/api/sessions/{id}/advance-phase` | Move to next configuration phase |
| GET | `/api/sessions/{id}/progress` | Get detailed completion progress |
| GET | `/api/sessions/{id}/dna` | Get current DNA JSON |
| POST | `/api/sessions/{id}/deploy` | Trigger deployment generation |
| POST | `/api/sessions/{id}/deploy/validate` | Validate DNA for deployment |
| WS | `/api/ws/{id}` | WebSocket for real-time chat |

## AI Providers

| Provider | Model | Configuration |
|----------|-------|---------------|
| OpenAI | GPT-4o, GPT-4o-mini | `OPENAI_API_KEY` |
| Anthropic | Claude Opus, Claude Sonnet | `ANTHROPIC_API_KEY` |
| Azure OpenAI | Any Azure-hosted model | `AZURE_OPENAI_API_KEY` + endpoint + deployment |

Switch providers at runtime via the UI dropdown or `AI_PROVIDER` environment variable.

## Integration with DNA Deployment Tool

The ADAM DNA Tool generates a `adam-dna-parsed.json` that is format-compatible with the existing DNA Deployment Tool's questionnaire parser output. The Deployment Bridge can:

1. **Generate DNA JSON** — Export the conversationally-built DNA as JSON
2. **Trigger Generators** — Call the DNA Deployment Tool's generators programmatically
3. **Produce All Artifacts** — IaC (Terraform/Bicep/CloudFormation/Helm), configs, and DOCX specs

## Security Considerations

- API keys stored in Kubernetes Secrets (use external secrets manager in production)
- Non-root container execution
- CORS restricted to configured origins
- File upload size limits enforced
- No persistent storage of AI conversation content beyond session TTL
- TLS termination at ingress

## License

ADAM — Autonomy Doctrine & Architecture Model
Copyright 2026. All rights reserved.
