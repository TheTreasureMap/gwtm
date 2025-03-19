# Gravitational Wave Treasure Map (GWTM) Helm Chart

This repository contains Helm charts for deploying the Gravitational Wave Treasure Map application in Kubernetes environments.

## Overview

The GWTM Helm chart manages the following components:

- **Backend**: Flask application
- **Frontend**: Nginx web server
- **Database**: PostgreSQL with PostGIS extension
- **Cache**: Redis

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2+
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [Skaffold](https://skaffold.dev/docs/install/) (for local development)
- [kubeseal](https://github.com/bitnami-labs/sealed-secrets#installation) (for production deployment)

## Local Development

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/gwtm.git
cd gwtm
```

2. **Install dependencies**

Make sure you have Docker, Kubernetes (or minikube), Helm, and Skaffold installed.

3. **Configure local environment**

Review and update the `values-dev.yaml` file with appropriate settings for your development environment. The default values should work for most local setups.

### Running the Application Locally

Skaffold is configured to build the application container and deploy it to your local Kubernetes cluster:

```bash
cd gwtm-helm
skaffold dev
```

This command will:
- Build the Docker image from the parent directory
- Deploy the application to Kubernetes using Helm
- Forward local ports to the deployed services
- Watch for file changes and automatically rebuild/redeploy

### Accessing the Application

Once deployed, you can access:

- The frontend dashboard at http://localhost:8081
- The backend API directly at http://localhost:8080

### Database Operations

To restore a database dump to your local development environment:

```bash
./restore-db /path/to/your/dump.sql
```

## Production Deployment

For production environments, you should:
- Use proper secrets management
- Configure appropriate resource limits
- Enable persistence for the database and cache
- Set up TLS and ingress properly

### Using Sealed Secrets for Production

For production, we recommend using [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) to securely manage sensitive information.

1. **Install the Sealed Secrets controller in your cluster**

```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets
```

2. **Create a secrets file (DO NOT commit this to version control)**

Create a file called `secrets.yaml` (add to .gitignore):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gwtm-secrets
  namespace: gwtm
type: Opaque
data:
  db-user: base64_encoded_value
  db-password: base64_encoded_value
  db-name: base64_encoded_value
  mail-password: base64_encoded_value
  recaptcha-public-key: base64_encoded_value
  recaptcha-private-key: base64_encoded_value
  aws-access-key-id: base64_encoded_value
  aws-secret-access-key: base64_encoded_value
  zenodo-access-key: base64_encoded_value
```

You can encode values to base64 using:
```bash
echo -n "your-value" | base64
```

3. **Seal the secrets**

```bash
kubeseal --format yaml < secrets.yaml > sealed-secrets.yaml
```

4. **Apply the sealed secrets to your cluster**

```bash
kubectl apply -f sealed-secrets.yaml
```

5. **Deploy with production values**

```bash
helm install gwtm ./gwtm-helm -f values-prod.yaml --namespace gwtm --create-namespace
```

Or using Skaffold:

```bash
skaffold run -f skaffold-prod.yaml
```

### Production Configuration

Edit the `values-prod.yaml` file to:

1. Set `global.useGeneratedSecrets: false` to use your sealed secrets
2. Configure appropriate resources for your environment
3. Set up proper persistence settings
4. Configure your ingress host and TLS settings

Example updates to `values-prod.yaml`:

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  host: gwtm.yourdomain.com
  tls: true
  tlsSecretName: gwtm-tls-cert

database:
  persistence:
    enabled: true
    size: 50Gi
    storageClass: managed-premium

cache:
  persistence:
    enabled: true
    size: 10Gi
```

## Configuration Reference

The following tables list the configurable parameters of the GWTM chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Kubernetes namespace to deploy into | `gwtm` |
| `global.environment` | Environment name (development/production) | `development` |
| `global.createNamespace` | Whether to create the namespace | `true` |
| `global.useGeneratedSecrets` | Whether to generate secrets | `true` |

### Backend Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.replicas` | Number of backend replicas | `2` |
| `backend.image.repository` | Backend image repository | `gwtm` |
| `backend.image.tag` | Backend image tag | `latest` |
| `backend.resources` | Backend resource requests/limits | See values.yaml |

### Additional Components

See `values.yaml` for detailed configuration options for the database, cache, and frontend components.

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check that the database pod is running and the service is accessible
   ```bash
   kubectl get pods -n gwtm
   kubectl logs -n gwtm <postgres-pod-name>
   ```

2. **Backend startup failure**: Check the logs for the flask-backend pod
   ```bash
   kubectl logs -n gwtm <backend-pod-name>
   ```

3. **Persistence issues**: If using persistence, ensure that the storage class exists and is working properly
   ```bash
   kubectl get sc
   kubectl describe pvc -n gwtm
   ```
