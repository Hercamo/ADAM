{{/* Standard chart helpers. */}}

{{- define "boss-engine.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "boss-engine.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "boss-engine.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "boss-engine.labels" -}}
helm.sh/chart: {{ include "boss-engine.chart" . }}
{{ include "boss-engine.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: adam
{{- end -}}

{{- define "boss-engine.selectorLabels" -}}
app.kubernetes.io/name: {{ include "boss-engine.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: api
{{- end -}}

{{- define "boss-engine.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "boss-engine.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "boss-engine.secretName" -}}
{{- if .Values.auth.existingSecret -}}
{{- .Values.auth.existingSecret -}}
{{- else -}}
{{- printf "%s-secrets" (include "boss-engine.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "boss-engine.neo4jSecretName" -}}
{{- if .Values.external.neo4j.existingSecret -}}
{{- .Values.external.neo4j.existingSecret -}}
{{- else -}}
{{- printf "%s-neo4j" (include "boss-engine.fullname" .) -}}
{{- end -}}
{{- end -}}
