{{/*
Common labels for every ADAM resource.
*/}}
{{- define "adam.labels" -}}
app.kubernetes.io/managed-by: "adam-sovereignty-connector"
app.kubernetes.io/part-of: "adam"
helm.sh/chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
{{- end -}}

{{- define "adam.image" -}}
{{- if .global.imageRegistry -}}
{{ .global.imageRegistry }}/{{ .image }}
{{- else -}}
{{ .image }}
{{- end -}}
{{- end -}}
