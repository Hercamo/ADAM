"""
Open Source Kubernetes Deployment Generator for ADAM DNA Specification.
Generates Helm charts & K8s YAML manifests for generic K8s deployment.
"""

from typing import Dict, Any
from .base_generator import BaseGenerator, AGENT_CLASSES

class K8sGenerator(BaseGenerator):
    PLATFORM_NAME = "kubernetes"
    PLATFORM_DISPLAY = "Open Source Kubernetes (Generic)"

    def generate_iac(self) -> Dict[str, str]:
        files = {}
        # Helm Chart
        files[self.write_yaml("helm/adam-platform/Chart.yaml", self._chart_yaml())] = "Helm Chart definition"
        files[self.write_yaml("helm/adam-platform/values.yaml", self._helm_values())] = "Helm values (main)"
        files[self.write_file("helm/adam-platform/templates/namespace.yaml", self._ns_yaml())] = "Namespace definitions"
        files[self.write_file("helm/adam-platform/templates/core-engine.yaml", self._core_engine_yaml())] = "CORE Engine deployment"
        files[self.write_file("helm/adam-platform/templates/boss-scoring.yaml", self._boss_scoring_yaml())] = "BOSS Scoring Engine"
        files[self.write_file("helm/adam-platform/templates/agent-mesh.yaml", self._agent_mesh_yaml())] = "Agent Mesh deployments"
        files[self.write_file("helm/adam-platform/templates/flight-recorder.yaml", self._flight_recorder_yaml())] = "Flight Recorder"
        files[self.write_file("helm/adam-platform/templates/policy-engine.yaml", self._policy_engine_yaml())] = "OPA Policy Engine"
        files[self.write_file("helm/adam-platform/templates/monitoring.yaml", self._monitoring_yaml())] = "Monitoring stack"
        files[self.write_file("helm/adam-platform/templates/rbac.yaml", self._rbac_yaml())] = "RBAC definitions"
        files[self.write_file("helm/adam-platform/templates/network-policies.yaml", self._network_policies_yaml())] = "Network policies"
        # Kustomize base
        files[self.write_file("kustomize/base/kustomization.yaml", self._kustomize_base())] = "Kustomize base"
        return files

    def generate_configs(self) -> Dict[str, str]:
        files = {}
        files[self.write_json("config/adam-k8s-config.json", self._k8s_config())] = "K8s deployment config"
        files[self.write_yaml("config/adam-k8s-values.yaml", self._k8s_values())] = "K8s Helm values override"
        return files

    def _chart_yaml(self) -> Dict:
        return {
            "apiVersion": "v2",
            "name": "adam-platform",
            "description": f"ADAM Autonomous Doctrine & Architecture Model for {self.company_name}",
            "type": "application",
            "version": "1.0.0",
            "appVersion": "1.1",
            "keywords": ["adam", "autonomy", "governance", "ai-agents"],
            "maintainers": [{"name": "ADAM DNA Deployment Tool", "email": "adam@" + self.company_slug + ".com"}],
            "dependencies": [
                {"name": "janusgraph", "version": "~1.0", "repository": "https://charts.bitnami.com/bitnami", "condition": "janusgraph.enabled"},
                {"name": "minio", "version": "~5.0", "repository": "https://charts.min.io/", "condition": "minio.enabled"},
                {"name": "opa", "version": "~6.0", "repository": "https://open-policy-agent.github.io/gatekeeper/charts", "condition": "opa.enabled"},
                {"name": "grafana", "version": "~7.0", "repository": "https://grafana.github.io/helm-charts", "condition": "grafana.enabled"},
                {"name": "prometheus", "version": "~25.0", "repository": "https://prometheus-community.github.io/helm-charts", "condition": "prometheus.enabled"},
            ],
        }

    def _helm_values(self) -> Dict:
        return {
            "global": {
                "company": self.company_name,
                "companySlug": self.company_slug,
                "platform": "kubernetes-opensource",
                "imageRegistry": "ghcr.io/adam-platform",
                "imageTag": "1.1.0",
            },
            "coreEngine": {
                "enabled": True,
                "database": "janusgraph",
                "replicas": 3,
                "resources": {"requests": {"cpu": "16", "memory": "64Gi"}, "limits": {"cpu": "32", "memory": "128Gi"}},
                "persistence": {"enabled": True, "size": "500Gi", "storageClass": "fast-ssd"},
            },
            "bossScoring": {
                "enabled": True,
                "replicas": 3,
                "dimensions": self.get_boss_dimensions(),
                "thresholds": self.get_boss_thresholds(),
                "resources": {"requests": {"cpu": "8", "memory": "32Gi"}, "limits": {"cpu": "16", "memory": "64Gi"}},
            },
            "flightRecorder": {
                "enabled": True,
                "storage": "minio",
                "replicas": 3,
                "retention": {"years": 7},
                "immutable": True,
                "hashChain": True,
            },
            "policyEngine": {
                "enabled": True,
                "engine": "opa-gatekeeper",
                "replicas": 3,
            },
            "agentMesh": {
                "domainGovernors": {"replicas": 3, "resources": {"requests": {"cpu": "8", "memory": "32Gi"}, "limits": {"cpu": "16", "memory": "64Gi", "nvidia.com/gpu": "1"}}},
                "orchestrationAgents": {"replicas": 3, "resources": {"requests": {"cpu": "8", "memory": "32Gi"}, "limits": {"cpu": "16", "memory": "64Gi"}}},
                "humanInterface": {"replicas": 2, "resources": {"requests": {"cpu": "4", "memory": "16Gi"}, "limits": {"cpu": "8", "memory": "32Gi"}}},
                "corporateWorkGroups": {"replicas": 2, "resources": {"requests": {"cpu": "2", "memory": "8Gi"}, "limits": {"cpu": "4", "memory": "16Gi"}}},
                "aiCentricDivision": {"replicas": 2, "resources": {"requests": {"cpu": "4", "memory": "16Gi"}, "limits": {"cpu": "8", "memory": "32Gi"}}},
                "digitalTwins": {"replicas": 2, "resources": {"requests": {"cpu": "16", "memory": "64Gi"}, "limits": {"cpu": "32", "memory": "128Gi", "nvidia.com/gpu": "4"}}},
                "metaGovernance": {"replicas": 2, "resources": {"requests": {"cpu": "4", "memory": "16Gi"}, "limits": {"cpu": "8", "memory": "32Gi"}}},
            },
            "llm": {
                "provider": "ollama",
                "models": {
                    "reasoning": {"name": "llama3.1:70b", "replicas": 3},
                    "execution": {"name": "llama3.1:8b", "replicas": 5},
                    "embedding": {"name": "nomic-embed-text", "replicas": 2},
                },
                "alternativeProviders": {
                    "vllm": {"enabled": False, "model": "meta-llama/Meta-Llama-3.1-70B-Instruct"},
                    "openai_compatible": {"enabled": False, "endpoint": "https://api.example.com/v1"},
                },
            },
            "janusgraph": {"enabled": True},
            "minio": {"enabled": True, "replicas": 4, "persistence": {"size": "1Ti"}},
            "opa": {"enabled": True},
            "grafana": {"enabled": True},
            "prometheus": {"enabled": True},
            "monitoring": {
                "opentelemetry": {"enabled": True},
                "dashboards": {"boss": True, "agents": True, "governance": True, "evidence": True},
            },
        }

    def _ns_yaml(self) -> str:
        return f'''{self.header_comment("#")}
apiVersion: v1
kind: Namespace
metadata:
  name: adam-governance
  labels:
    adam/plane: governance
    adam/company: {self.company_slug}
---
apiVersion: v1
kind: Namespace
metadata:
  name: adam-agents
  labels:
    adam/plane: execution
    adam/company: {self.company_slug}
---
apiVersion: v1
kind: Namespace
metadata:
  name: adam-data
  labels:
    adam/plane: data
    adam/company: {self.company_slug}
---
apiVersion: v1
kind: Namespace
metadata:
  name: adam-monitoring
  labels:
    adam/plane: observability
    adam/company: {self.company_slug}
'''

    def _core_engine_yaml(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM CORE Engine - Graph Database + Inference Engine
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: adam-core-engine
  namespace: adam-governance
  labels:
    app.kubernetes.io/name: adam-core-engine
    adam/plane: governance
    adam/component: core-engine
spec:
  serviceName: adam-core-engine
  replicas: {{{{ .Values.coreEngine.replicas }}}}
  selector:
    matchLabels:
      app.kubernetes.io/name: adam-core-engine
  template:
    metadata:
      labels:
        app.kubernetes.io/name: adam-core-engine
        adam/plane: governance
    spec:
      nodeSelector:
        adam/plane: governance
      containers:
        - name: core-engine
          image: "{{{{ .Values.global.imageRegistry }}}}/adam-core-engine:{{{{ .Values.global.imageTag }}}}"
          ports:
            - containerPort: 8182
              name: gremlin
            - containerPort: 8080
              name: http
          env:
            - name: ADAM_COMPANY
              value: "{{{{ .Values.global.company }}}}"
            - name: ADAM_GRAPH_BACKEND
              value: "{{{{ .Values.coreEngine.database }}}}"
          resources:
            requests:
              cpu: "{{{{ .Values.coreEngine.resources.requests.cpu }}}}"
              memory: "{{{{ .Values.coreEngine.resources.requests.memory }}}}"
            limits:
              cpu: "{{{{ .Values.coreEngine.resources.limits.cpu }}}}"
              memory: "{{{{ .Values.coreEngine.resources.limits.memory }}}}"
          volumeMounts:
            - name: core-data
              mountPath: /data
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 5
  volumeClaimTemplates:
    - metadata:
        name: core-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: "{{{{ .Values.coreEngine.persistence.storageClass }}}}"
        resources:
          requests:
            storage: "{{{{ .Values.coreEngine.persistence.size }}}}"
---
apiVersion: v1
kind: Service
metadata:
  name: adam-core-engine
  namespace: adam-governance
spec:
  selector:
    app.kubernetes.io/name: adam-core-engine
  ports:
    - port: 8182
      name: gremlin
    - port: 8080
      name: http
  clusterIP: None
'''

    def _boss_scoring_yaml(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM BOSS Scoring Engine
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adam-boss-engine
  namespace: adam-governance
  labels:
    app.kubernetes.io/name: adam-boss-engine
    adam/plane: governance
    adam/component: boss-scoring
spec:
  replicas: {{{{ .Values.bossScoring.replicas }}}}
  selector:
    matchLabels:
      app.kubernetes.io/name: adam-boss-engine
  template:
    metadata:
      labels:
        app.kubernetes.io/name: adam-boss-engine
        adam/plane: governance
    spec:
      nodeSelector:
        adam/plane: governance
      containers:
        - name: boss-engine
          image: "{{{{ .Values.global.imageRegistry }}}}/adam-boss-engine:{{{{ .Values.global.imageTag }}}}"
          ports:
            - containerPort: 8090
              name: http
          env:
            - name: BOSS_DIMENSIONS_CONFIG
              value: /config/boss-dimensions.json
          resources:
            requests:
              cpu: "{{{{ .Values.bossScoring.resources.requests.cpu }}}}"
              memory: "{{{{ .Values.bossScoring.resources.requests.memory }}}}"
            limits:
              cpu: "{{{{ .Values.bossScoring.resources.limits.cpu }}}}"
              memory: "{{{{ .Values.bossScoring.resources.limits.memory }}}}"
          volumeMounts:
            - name: boss-config
              mountPath: /config
      volumes:
        - name: boss-config
          configMap:
            name: adam-boss-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: adam-boss-config
  namespace: adam-governance
data:
  boss-dimensions.json: |
    {{{{ .Values.bossScoring.dimensions | toJson }}}}
  boss-thresholds.json: |
    {{{{ .Values.bossScoring.thresholds | toJson }}}}
'''

    def _agent_mesh_yaml(self) -> str:
        sections = []
        for class_key, class_data in AGENT_CLASSES.items():
            for agent in class_data["agents"]:
                sections.append(f'''---
# Agent: {agent["name"]}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {agent["id"]}
  namespace: adam-agents
  labels:
    app.kubernetes.io/name: {agent["id"]}
    adam/agent-class: {class_key}
    adam/plane: execution
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: {agent["id"]}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {agent["id"]}
        adam/agent-class: {class_key}
    spec:
      containers:
        - name: agent
          image: "{{{{ .Values.global.imageRegistry }}}}/adam-agent:{{{{ .Values.global.imageTag }}}}"
          env:
            - name: AGENT_ID
              value: "{agent["id"]}"
            - name: AGENT_NAME
              value: "{agent["name"]}"
            - name: AGENT_CLASS
              value: "{class_key}"
          resources:
            requests:
              cpu: "{agent["resources"]["vcpus"]}"
              memory: "{agent["resources"]["ram_gb"]}Gi"
            limits:
              cpu: "{agent["resources"]["vcpus"] * 2}"
              memory: "{agent["resources"]["ram_gb"] * 2}Gi"
''')
                # Append GPU limit onto the existing limits block for GPU agents.
                if agent["resources"]["gpu"]:
                    sections[-1] += f'''              nvidia.com/gpu: "1"
'''
        # Only include first 5 and last 2 to keep file manageable, with comment
        return f'''{self.header_comment("#")}
# ADAM Agent Mesh - {self.total_agents()} Agents across {len(AGENT_CLASSES)} classes
# This file contains deployment manifests for all ADAM agents.
# Each agent runs as an independent deployment with its own identity and resources.
{"".join(sections[:10])}

# ... ({len(sections) - 12} additional agent deployments) ...

{"".join(sections[-2:])}
'''

    def _flight_recorder_yaml(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Flight Recorder - Immutable evidence store
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: adam-flight-recorder
  namespace: adam-data
  labels:
    app.kubernetes.io/name: adam-flight-recorder
    adam/plane: data
    adam/component: flight-recorder
spec:
  serviceName: adam-flight-recorder
  replicas: {{{{ .Values.flightRecorder.replicas | default 3 }}}}
  selector:
    matchLabels:
      app.kubernetes.io/name: adam-flight-recorder
  template:
    metadata:
      labels:
        app.kubernetes.io/name: adam-flight-recorder
    spec:
      containers:
        - name: flight-recorder
          image: "{{{{ .Values.global.imageRegistry }}}}/adam-flight-recorder:{{{{ .Values.global.imageTag }}}}"
          ports:
            - containerPort: 8091
              name: http
          env:
            - name: STORAGE_BACKEND
              value: "minio"
            - name: HASH_CHAIN_ENABLED
              value: "true"
            - name: IMMUTABLE_MODE
              value: "true"
  volumeClaimTemplates:
    - metadata:
        name: evidence-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 500Gi
'''

    def _policy_engine_yaml(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Policy Engine - OPA/Gatekeeper for governance enforcement
apiVersion: v1
kind: ConfigMap
metadata:
  name: adam-rego-policies
  namespace: adam-governance
data:
  boss-routing.rego: |
    package adam.boss

    # BOSS routing policy - maps composite scores to escalation tiers
    default routing_tier = "soap"

    routing_tier = "ohshat" {{ input.composite_score > 75 }}
    routing_tier = "high" {{ input.composite_score > 50; input.composite_score <= 75 }}
    routing_tier = "elevated" {{ input.composite_score > 30; input.composite_score <= 50 }}
    routing_tier = "moderate" {{ input.composite_score > 10; input.composite_score <= 30 }}

    # Critical dimension override
    escalate_override {{
      some d
      input.dimension_scores[d] > 75
    }}

  intent-validation.rego: |
    package adam.intent

    # Intent Object validation policy
    default valid = false

    valid {{
      input.intent_id != ""
      input.source.role != ""
      count(input.desired_outcomes) > 0
      count(input.constraints) > 0
    }}

    # Check delegation authority
    authorized {{
      input.source.role == "director"
    }}

    authorized {{
      input.source.delegation_chain != null
      count(input.source.delegation_chain) > 0
    }}

  idempotency-check.rego: |
    package adam.idempotency

    # Non-idempotent action penalty
    default penalty = 0
    penalty = 15 {{ input.action.is_non_idempotent == true }}
'''

    def _monitoring_yaml(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Monitoring - OpenTelemetry Collector + ServiceMonitors
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adam-otel-collector
  namespace: adam-monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: adam-otel-collector
  template:
    metadata:
      labels:
        app: adam-otel-collector
    spec:
      containers:
        - name: otel-collector
          image: otel/opentelemetry-collector-contrib:0.92.0
          ports:
            - containerPort: 4317  # gRPC
            - containerPort: 4318  # HTTP
            - containerPort: 8888  # metrics
          volumeMounts:
            - name: otel-config
              mountPath: /etc/otel
      volumes:
        - name: otel-config
          configMap:
            name: adam-otel-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: adam-otel-config
  namespace: adam-monitoring
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    processors:
      batch:
        timeout: 5s
      attributes:
        actions:
          - key: adam.company
            value: "{self.company_name}"
            action: insert
    exporters:
      prometheus:
        endpoint: 0.0.0.0:8889
      logging:
        loglevel: info
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch, attributes]
          exporters: [logging]
        metrics:
          receivers: [otlp]
          processors: [batch]
          exporters: [prometheus]
'''

    def _rbac_yaml(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM RBAC - Least-privilege agent identities
apiVersion: v1
kind: ServiceAccount
metadata:
  name: adam-governance-sa
  namespace: adam-governance
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: adam-agent-mesh-sa
  namespace: adam-agents
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: adam-governance-role
  namespace: adam-governance
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: adam-governance-binding
  namespace: adam-governance
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: adam-governance-role
subjects:
  - kind: ServiceAccount
    name: adam-governance-sa
    namespace: adam-governance
'''

    def _network_policies_yaml(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Network Policies - Sovereignty isolation
# Governance namespace: no external ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: adam-governance-isolation
  namespace: adam-governance
spec:
  podSelector: {{}}
  policyTypes: ["Ingress", "Egress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              adam/plane: governance
        - namespaceSelector:
            matchLabels:
              adam/plane: execution
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              adam/plane: governance
        - namespaceSelector:
            matchLabels:
              adam/plane: data
---
# Agent namespace: can reach governance and data, not internet
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: adam-agents-isolation
  namespace: adam-agents
spec:
  podSelector: {{}}
  policyTypes: ["Ingress", "Egress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              adam/plane: governance
        - namespaceSelector:
            matchLabels:
              adam/plane: execution
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              adam/plane: governance
        - namespaceSelector:
            matchLabels:
              adam/plane: data
        - namespaceSelector:
            matchLabels:
              adam/plane: execution
'''

    def _kustomize_base(self) -> str:
        return f'''{self.header_comment("#")}
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: adam-governance

resources:
  - ../helm/adam-platform/templates/namespace.yaml
  - ../helm/adam-platform/templates/rbac.yaml
  - ../helm/adam-platform/templates/network-policies.yaml
  - ../helm/adam-platform/templates/core-engine.yaml
  - ../helm/adam-platform/templates/boss-scoring.yaml
  - ../helm/adam-platform/templates/flight-recorder.yaml
  - ../helm/adam-platform/templates/policy-engine.yaml
  - ../helm/adam-platform/templates/monitoring.yaml

commonLabels:
  adam/company: {self.company_slug}
'''

    def _k8s_config(self) -> Dict[str, Any]:
        return {
            "adam_deployment": {
                "platform": "kubernetes-opensource",
                "company": self.company_name,
                "version": "1.1",
                "generated": self.timestamp,
            },
            "governance_plane": {
                "core_engine": {"database": "janusgraph", "replicas": 3},
                "flight_recorder": {"storage": "minio", "immutable": True},
                "crypto_vault": {"service": "hashicorp-vault"},
                "policy_engine": {"engine": "opa-gatekeeper"},
            },
            "agent_mesh": {
                "total_agents": self.total_agents(),
                "agent_classes": {k: {"count": len(v["agents"]), "description": v["description"]} for k, v in AGENT_CLASSES.items()},
            },
            "llm": {
                "provider": "ollama",
                "models": {"reasoning": "llama3.1:70b", "execution": "llama3.1:8b"},
            },
            "boss_config": {"dimensions": self.get_boss_dimensions(), "thresholds": self.get_boss_thresholds()},
        }

    def _k8s_values(self) -> Dict[str, Any]:
        return self._helm_values()
