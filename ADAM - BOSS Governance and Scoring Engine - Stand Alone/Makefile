# BOSS AI Governance & Risk Engine — developer Makefile.
#
# Run `make help` for a categorized list of targets. The Makefile is the
# single source of truth that CI pipelines, docs, and local development
# all drive through, so changes here affect every environment.

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
UV ?= uv
VENV ?= .venv
DOCKER ?= docker
COMPOSE ?= $(DOCKER) compose
HELM ?= helm
KUBECTL ?= kubectl
NPM ?= npm

IMAGE_REPO ?= ghcr.io/hercamo/boss-engine
IMAGE_TAG ?= 3.2.0
IMAGE = $(IMAGE_REPO):$(IMAGE_TAG)

BOSS_API_URL ?= http://127.0.0.1:8080
REPORTS ?= .reports

.DEFAULT_GOAL := help
.PHONY: help \
        venv install install-dev clean \
        lint format typecheck test test-unit test-integration test-schema \
        coverage security audit \
        api run dev \
        graph-seed graph-dryrun \
        console-install console-dev console-build \
        docker-build docker-run docker-push docker-scan \
        compose-up compose-down compose-logs \
        helm-lint helm-template helm-test helm-package \
        k8s-validate k8s-apply k8s-delete \
        release check check-all ci reports-clean

##@ General

help:  ## Show this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
	/^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 } \
	/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Environment

venv:  ## Create a local virtualenv in $(VENV).
	$(PYTHON) -m venv $(VENV)
	@echo "Activate with: source $(VENV)/bin/activate"

install:  ## Install runtime dependencies only.
	$(PIP) install --upgrade pip
	$(PIP) install -e '.'

install-dev:  ## Install full dev stack (lint, test, adapters, neo4j, metrics).
	$(PIP) install --upgrade pip
	$(PIP) install -e '.[dev]'
	pre-commit install || true

clean: reports-clean  ## Remove caches and build artifacts.
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -prune -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -prune -exec rm -rf {} +

reports-clean:
	rm -rf $(REPORTS)

##@ Quality Gates

lint:  ## Run ruff (lint only).
	ruff check boss_core boss_api boss_graph boss_adapters examples scripts tests

format:  ## Run ruff formatter (autofix).
	ruff format boss_core boss_api boss_graph boss_adapters examples scripts tests
	ruff check --fix boss_core boss_api boss_graph boss_adapters examples scripts tests

typecheck:  ## Run mypy in strict mode.
	mypy boss_core boss_api boss_graph boss_adapters

security:  ## Run bandit against the service code.
	bandit -r boss_core boss_api boss_graph boss_adapters -c pyproject.toml

audit:  ## Run pip-audit against the locked dependency set.
	pip-audit -r <(pip freeze) --strict || true

##@ Tests

test: test-unit  ## Default test suite (unit).

test-unit:  ## Run the fast unit suite.
	mkdir -p $(REPORTS)
	pytest -m "not integration and not schemathesis" \
	       --junitxml=$(REPORTS)/junit-unit.xml \
	       --cov --cov-report=xml:$(REPORTS)/coverage.xml \
	       --cov-report=term-missing

test-integration:  ## Run integration tests (spins up docker-compose if needed).
	pytest -m integration \
	       --junitxml=$(REPORTS)/junit-integration.xml \
	       -vv

test-schema:  ## Run Schemathesis property tests against a running API.
	BOSS_API_URL=$(BOSS_API_URL) \
	schemathesis run $(BOSS_API_URL)/v1/openapi.json \
	   --checks all --workers 4 \
	   --junit-xml $(REPORTS)/junit-schemathesis.xml

coverage: test-unit  ## Alias for test-unit; prints the coverage summary.
	@echo "coverage xml written to $(REPORTS)/coverage.xml"

##@ API

api:  ## Import-check the FastAPI app and print the route table.
	$(PYTHON) -c "from boss_api.app import create_app; app=create_app(); \
	               print('\n'.join(f'{r.path:35s} {sorted(r.methods) if hasattr(r,\"methods\") else \"\"}' for r in app.routes))"

run:  ## Run the API with uvicorn on localhost:8080.
	uvicorn boss_api.app:create_app --factory --host 0.0.0.0 --port 8080 --reload

dev: run  ## Alias for 'run'.

##@ Graph

graph-dryrun:  ## Print the schema + seed statements without applying them.
	$(PYTHON) -m boss_graph.loader --schema boss_graph/schema.cypher \
	                                --seed boss_graph/seed.cypher \
	                                --dry-run

graph-seed:  ## Apply schema.cypher + seed.cypher against $(BOSS_NEO4J_URI).
	$(PYTHON) -m boss_graph.loader \
	    --uri "$${BOSS_NEO4J_URI:?set BOSS_NEO4J_URI}" \
	    --user "$${BOSS_NEO4J_USER:-neo4j}" \
	    --password "$${BOSS_NEO4J_PASSWORD:?set BOSS_NEO4J_PASSWORD}" \
	    --schema boss_graph/schema.cypher \
	    --seed boss_graph/seed.cypher

##@ Evidence Console

console-install:  ## npm ci for the React console.
	cd boss_console && $(NPM) ci --no-audit --no-progress

console-dev:  ## Run the React console dev server (Vite).
	cd boss_console && BOSS_API_URL=$(BOSS_API_URL) $(NPM) run dev

console-build:  ## Build the production console bundle.
	cd boss_console && $(NPM) run build

##@ Docker

docker-build:  ## Build the BOSS Engine container image.
	DOCKER_BUILDKIT=1 $(DOCKER) build -t $(IMAGE) .

docker-run:  ## Run the image locally on port 8080.
	$(DOCKER) run --rm -p 8080:8080 $(IMAGE)

docker-push:  ## Push the image to the configured registry.
	$(DOCKER) push $(IMAGE)

docker-scan:  ## Trivy scan (install locally from github.com/aquasecurity/trivy).
	trivy image --severity HIGH,CRITICAL --ignore-unfixed $(IMAGE)

##@ Compose

compose-up:  ## docker compose up (engine only).
	$(COMPOSE) up --build -d

compose-down:  ## Tear down the compose stack.
	$(COMPOSE) down -v

compose-logs:
	$(COMPOSE) logs -f engine

##@ Helm

helm-lint:  ## Lint the Helm chart.
	$(HELM) lint deploy/helm/boss-engine

helm-template:  ## Render chart templates for review.
	$(HELM) template boss-engine deploy/helm/boss-engine \
	    --namespace boss-engine --create-namespace

helm-test:  ## Render + kubeconform validate the Helm output.
	$(HELM) template boss-engine deploy/helm/boss-engine | \
	    kubeconform -strict -summary -output text -kubernetes-version 1.30.0

helm-package:  ## Package the chart into a tgz under deploy/charts.
	mkdir -p deploy/charts
	$(HELM) package deploy/helm/boss-engine -d deploy/charts

##@ Raw Kubernetes manifests

k8s-validate:  ## Validate the raw K8s manifests with kubeconform.
	kubeconform -strict -summary -output text -kubernetes-version 1.30.0 deploy/k8s/*.yaml

k8s-apply:  ## Apply the raw manifests to the current kube-context.
	$(KUBECTL) apply -f deploy/k8s/00-namespace.yaml
	$(KUBECTL) apply -f deploy/k8s/10-serviceaccount.yaml
	$(KUBECTL) apply -f deploy/k8s/20-configmap.yaml
	@echo "Apply your real Secret separately (see deploy/k8s/21-secret.example.yaml)."
	$(KUBECTL) apply -f deploy/k8s/30-deployment.yaml
	$(KUBECTL) apply -f deploy/k8s/31-service.yaml
	$(KUBECTL) apply -f deploy/k8s/40-hpa.yaml
	$(KUBECTL) apply -f deploy/k8s/41-poddisruptionbudget.yaml
	$(KUBECTL) apply -f deploy/k8s/50-networkpolicy.yaml

k8s-delete:
	$(KUBECTL) delete -f deploy/k8s || true

##@ Composite

check: lint typecheck test-unit  ## Fast pre-push check (no docker / k8s).

check-all: check security helm-lint helm-test  ## Full local CI mirror.

ci: check-all  ## Target run by GitHub Actions.

release:  ## Tag + build + push. Requires IMAGE_TAG override.
	@test -n "$(IMAGE_TAG)" || (echo "IMAGE_TAG required" && exit 1)
	$(MAKE) docker-build docker-push
