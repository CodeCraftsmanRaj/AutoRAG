{{- define "rag-chart.name" -}}
rag-chart
{{- end -}}

{{- define "rag-chart.fullname" -}}
{{- printf "%s" .Release.Name -}}
{{- end -}}
