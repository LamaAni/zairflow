{{- define "zairflow.kubernetes.worker" -}}
{{- $full_name := include "zairflow-helm.fullname" . }}
apiVersion: v1
kind: Pod
metadata:
  labels:
    zairflow.app: {{ include "zairflow-helm.fullname" . }}-worker
spec:
  {{- if .Values.serviceAccount.enabled }}
  serviceAccountName: {{ include "zairflow-helm.serviceAccountName" . }}
  {{- end}}
  restartPolicy: Never
  {{- include "zairflow-helm.node_selection_and_toleration" . | nindent 2 }}
  terminationGracePeriodSeconds: {{ default 10 .Values.worker.terminationGracePeriodSeconds }}
  containers:
    - name: airflow-worker
      image: {{ include "zairflow-helm.image" . }}
      imagePullPolicy: {{ .Values.worker.pullPolicy | default .Values.image.pullPolicy }}
      envFrom:
        - configMapRef:
            name: {{ $full_name }}-envs
        - configMapRef:
            name: {{ $full_name }}-kube-worker-envs
      env:
        - name: ZAIRFLOW_CONTAINER_TYPE
          value: 'worker'
        {{- tuple .Values.worker.envs | include "inject-yaml" | nindent 8 }}
      resources:
{{ tuple .Values.worker.resources | include "inject-yaml" | nindent 8 }}
{{ tuple .Values.worker.injectContainerYaml | include "inject-yaml" | nindent 6 }}
{{ tuple .Values.worker.containers | include "inject-yaml" | nindent 4 }}
{{ tuple .Values.worker.injectSpecYaml | include "inject-yaml" | nindent 2 }}
{{- end -}}