{{/* Return the name of the secret to use for global app credentials */}}
{{- define "gwtm.secretName" -}}
{{- if .Values.global.useGeneratedSecrets }}{{ .Release.Name }}-secrets{{ else }}{{ .Values.global.existingSecret }}{{ end }}
{{- end }}

{{/* DB env vars for main containers */}}
{{- define "gwtm.dbEnv" -}}
- name: DB_USER
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: db-user
- name: DB_PWD
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: db-password
- name: DB_NAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: db-name
- name: DB_HOST
  value: {{ .Values.database.name }}
- name: DB_PORT
  value: "{{ .Values.database.service.port }}"
{{- end }}

{{/* DB env vars for init containers (includes PGPASSWORD) */}}
{{- define "gwtm.dbInitEnv" -}}
{{- include "gwtm.dbEnv" . }}
- name: PGPASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: db-password
{{- end }}

{{/* Cloud storage env vars (S3, Azure, Swift) from global secrets */}}
{{- define "gwtm.storageEnv" -}}
- name: STORAGE_BUCKET_SOURCE
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: STORAGE_BUCKET_SOURCE
- name: AWS_ACCESS_KEY_ID
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: aws-access-key-id
- name: AWS_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: aws-secret-access-key
- name: AWS_DEFAULT_REGION
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: AWS_DEFAULT_REGION
- name: AWS_BUCKET
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: AWS_BUCKET
- name: AZURE_ACCOUNT_NAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: AZURE_ACCOUNT_NAME
- name: AZURE_ACCOUNT_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: AZURE_ACCOUNT_KEY
- name: OS_AUTH_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_AUTH_URL
- name: OS_STORAGE_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_STORAGE_URL
- name: OS_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_USERNAME
- name: OS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_PASSWORD
- name: OS_CONTAINER_NAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_CONTAINER_NAME
- name: OS_PROJECT_NAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_PROJECT_NAME
- name: OS_USER_DOMAIN_NAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_USER_DOMAIN_NAME
- name: OS_PROJECT_DOMAIN_NAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: OS_PROJECT_DOMAIN_NAME
{{- end }}

{{/* App secret env vars: mail, recaptcha, zenodo */}}
{{- define "gwtm.appSecretEnv" -}}
- name: JWT_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: jwt-secret-key
- name: MAIL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: mail-password
- name: RECAPTCHA_PUBLIC_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: recaptcha-public-key
- name: RECAPTCHA_PRIVATE_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: recaptcha-private-key
- name: ZENODO_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.secretName" . }}
      key: zenodo-access-key
{{- end }}

{{/* Shared env vars for listener deployments (ligo + icecube) */}}
{{- define "gwtm.listenerEnv" -}}
# Kafka Configuration
- name: KAFKA_CLIENT_ID
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.fullname" . }}-listener-secrets
      key: kafka-client-id
- name: KAFKA_CLIENT_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.fullname" . }}-listener-secrets
      key: kafka-client-secret
# GWTM API Configuration
- name: API_BASE
  value: {{ printf "http://%s:%d%s" .Values.listeners.api.host (int .Values.listeners.api.port) .Values.listeners.api.path | quote }}
- name: API_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.fullname" . }}-listener-secrets
      key: api-token
# Storage Configuration
- name: STORAGE_BUCKET_SOURCE
  value: {{ .Values.listeners.storage.type | quote }}
{{- if eq .Values.listeners.storage.type "s3" }}
- name: AWS_ACCESS_KEY_ID
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.fullname" . }}-listener-secrets
      key: aws-access-key-id
- name: AWS_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.fullname" . }}-listener-secrets
      key: aws-secret-access-key
- name: AWS_DEFAULT_REGION
  value: {{ .Values.listeners.storage.s3.region | quote }}
- name: AWS_BUCKET
  value: {{ .Values.listeners.storage.s3.bucket | quote }}
{{- end }}
{{- if eq .Values.listeners.storage.type "swift" }}
- name: OS_AUTH_URL
  value: {{ .Values.listeners.storage.swift.authUrl | quote }}
- name: OS_STORAGE_URL
  value: {{ .Values.listeners.storage.swift.storageUrl | quote }}
- name: OS_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.fullname" . }}-listener-secrets
      key: swift-username
- name: OS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "gwtm.fullname" . }}-listener-secrets
      key: swift-password
- name: OS_PROJECT_NAME
  value: {{ .Values.listeners.storage.swift.projectName | default "" | quote }}
- name: OS_USER_DOMAIN_NAME
  value: {{ .Values.listeners.storage.swift.userDomainName | default "Default" | quote }}
- name: OS_PROJECT_DOMAIN_NAME
  value: {{ .Values.listeners.storage.swift.projectDomainName | default "Default" | quote }}
- name: OS_CONTAINER_NAME
  value: {{ .Values.listeners.storage.swift.containerName | default "gwtreasuremap" | quote }}
{{- end }}
# Observing Run
- name: OBSERVING_RUN
  value: {{ .Values.listeners.observingRun | default "O4" | quote }}
# Listener behavior controls
- name: DRY_RUN
  value: {{ .Values.listeners.dryRun | default "false" | quote }}
- name: WRITE_TO_STORAGE
  value: {{ .Values.listeners.writeToStorage | default "true" | quote }}
- name: VERBOSE
  value: {{ .Values.listeners.verbose | default "true" | quote }}
# Logging configuration
- name: LOG_FORMAT
  value: {{ .Values.listeners.logging.format | default "json" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.listeners.logging.level | default "INFO" | quote }}
{{- if .Values.listeners.kafka.offsetReset }}
- name: KAFKA_OFFSET_RESET
  value: {{ .Values.listeners.kafka.offsetReset | quote }}
{{- end }}
{{- if .Values.listeners.kafka.groupId }}
- name: KAFKA_GROUP_ID
  value: {{ .Values.listeners.kafka.groupId | quote }}
{{- end }}
{{- if .Values.listeners.galaxyCatalogConfig }}
- name: PATH_TO_GALAXY_CATALOG_CONFIG
  value: {{ .Values.listeners.galaxyCatalogConfig | quote }}
{{- end }}
{{- end }}

{{/* Generate basic labels */}}
{{- define "gwtm.labels" -}}
app.kubernetes.io/name: {{ include "gwtm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Generate name */}}
{{- define "gwtm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Generate fullname */}}
{{- define "gwtm.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}
