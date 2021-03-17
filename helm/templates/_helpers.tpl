{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "zairflow-helm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "zairflow-helm.fullname" -}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "zairflow-helm.namespace" -}}
{{- .Values.namespace | default .Release.Namespace -}}
{{- end -}}


{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "zairflow-helm.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "zairflow-helm.labels" -}}
helm.sh/chart: {{ include "zairflow-helm.chart" . }}
{{ include "zairflow-helm.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "zairflow-helm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "zairflow-helm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Tolerations and node selection
*/}}
{{- define "zairflow-helm.node_selection_and_toleration" -}}
{{- if .Values.tolerations }}
tolerations: 
{{ .Values.tolerations | toYaml | indent 2}}
{{- end }}
{{- if .Values.nodeSelector }}
nodeSelector:
{{ .Values.nodeSelector | toYaml | indent 2}}
{{- end }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "zairflow-helm.serviceAccountName" -}}
  {{- if .Values.serviceAccount.enabled -}}

    {{- if .Values.serviceAccount.name -}}
      {{- .Values.serviceAccount.name }}
    {{- else -}}
      {{- include "zairflow-helm.fullname" . }}-svc-account
    {{- end -}}

  {{- else -}}
    {{- default "default" .Values.serviceAccount.defaultServiceAccount }}
  {{- end -}}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "zairflow-helm.serviceAccountRoleName" -}}
{{- include "zairflow-helm.fullname" . }}-role
{{- end -}}

{{/*
Create image name
*/}}
{{- define "zairflow-helm.image" -}}
{{- .Values.image.repository }}:{{ .Values.image.tag }}
{{- end -}}

{{/*
Create image name
*/}}
{{- define "inject-yaml" -}}
  {{- $value := index . 0 }}
  {{- if $value }}
    {{- toYaml $value }}
  {{- else }}

  {{- end }}
{{- end -}}

{{/*
Configmap checksum
*/}}
{{- define "zairflow-helm.metadata_checksums" -}}
checksum/config: {{ include (print $.Template.BasePath "/envs.yaml") . | sha256sum }}
checksum/values: {{ .Values | toJson | sha256sum }}
{{- end -}}