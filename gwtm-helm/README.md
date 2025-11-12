# Gravitational Wave Treasure Map (GWTM) Helm Chart

This repository contains Helm charts for deploying the Gravitational Wave Treasure Map application in Kubernetes environments.

## Overview

The GWTM Helm chart manages the following components:

- **Flask Backend** (`flask-backend`): Legacy Python [Flask](https://flask.palletsprojects.com/) application (Python 3.9+, Flask 2.1.1) on port 8080
- **FastAPI Backend** (`fastapi-backend`): Modern high-performance API service with auto-documentation on port 8000 ([FastAPI docs](https://fastapi.tiangolo.com/))
- **Svelte Frontend** (`frontend`): TypeScript/[SvelteKit](https://kit.svelte.dev/) dashboard with modern reactive UI on port 3000 ([Svelte docs](https://svelte.dev/))
- **PostgreSQL Database** (`postgres`): [PostgreSQL](https://www.postgresql.org/docs/) 14+ with [PostGIS](https://postgis.net/) 3.x extension for geospatial data on port 5432
- **Event Listeners** (optional): LIGO and IceCube gravitational wave event listeners

## Deployed Resources

When you run `skaffold dev`, the following Kubernetes resources are created in the `gwtm` namespace:

### Deployments
- `flask-backend` - 1 replica (configurable)
- `fastapi-backend` - 1 replica (configurable)
- `frontend` - 1 replica (configurable)
- `postgres` - 1 replica (stateful)
- `ligo-listener` - 1 replica (if enabled)
- `icecube-listener` - 1 replica (if enabled)

### Services
- `flask-backend` - ClusterIP on port 8080
- `fastapi-backend` - ClusterIP on port 8000
- `frontend` - ClusterIP on port 3000
- `postgres` - ClusterIP on port 5432

### ConfigMaps & Secrets
- `gwtm-secrets` - Credentials and API keys
- `postgres-init-scripts` - Database initialization SQL

### Persistent Volumes (optional)
- `postgres-data` - Database storage (if persistence enabled)

### Port Forwards (automatic with `skaffold dev`)
- `localhost:8080` → `flask-backend:8080`
- `localhost:8000` → `fastapi-backend:8000`
- `localhost:3000` → `frontend:3000`

### Build Artifacts

Skaffold builds the following Docker images:

1. **gwtm** - Flask backend from main Dockerfile
2. **gwtm-fastapi** - FastAPI backend from `server/Dockerfile`
3. **gwtm-frontend** - Svelte frontend from `frontend/Dockerfile`

File sync is configured for hot-reloading without rebuilds:
- FastAPI: Python files sync to container, uvicorn auto-reloads
- Frontend: Source files sync to container, Vite HMR handles updates
- Flask: No sync configured (requires rebuild)

## Quick Reference

**Start the full stack:**
```bash
cd gwtm-helm && skaffold dev
```

**Monitor deployment:**
```bash
kubectl get pods -n gwtm --watch
```

**View logs:**
```bash
kubectl logs -n gwtm deployment/frontend -f          # Frontend
kubectl logs -n gwtm deployment/fastapi-backend -f   # FastAPI
kubectl logs -n gwtm deployment/flask-backend -f     # Flask
```

**Access services:**
- Frontend: http://localhost:3000
- FastAPI Docs: http://localhost:8000/docs
- Flask API: http://localhost:8080/api/v0/

**Database operations:**
```bash
./restore-db path/to/dump.sql                                          # Restore DB (auto-strips incompatible \restrict commands)
kubectl exec -it -n gwtm deployment/postgres -- psql -U treasuremap    # Connect to DB
```

**Troubleshooting:**
```bash
kubectl get all -n gwtm                     # Check all resources
kubectl describe pod <pod-name> -n gwtm     # Detailed pod info
skaffold delete && skaffold dev             # Clean restart
```

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

- **Svelte Frontend**: http://localhost:3000 - Modern reactive UI dashboard
- **Flask Backend API**: http://localhost:8080 - Legacy REST API
- **FastAPI Backend**: http://localhost:8000 - Modern API with docs at http://localhost:8000/docs

### Database Operations

To restore a database dump to your local development environment:

```bash
./restore-db /path/to/your/dump.sql
```

The restore script automatically strips out `\restrict` commands that are added by newer pg_dump versions (v16+) but not supported by the PostgreSQL v14 server in the cluster.

To dump a copy of the production database:

```bash
# Exclude all Flask profiler tables (large and irrelevant for testing)
# --no-owner: Don't set ownership (avoids privilege issues)
# --no-privileges: Don't dump access privileges (avoids ACL issues)
# --clean: Add DROP commands before CREATE
# --if-exists: Use IF EXISTS with DROP commands
# Note: \restrict commands from pg_dump v16+ are automatically stripped during restore
pg_dump -h treasuremap.host.org -U treasuremap -d treasuremap \
  --exclude-table='public.flask*' \
  --no-owner --no-privileges --clean --if-exists \
  -f ./dump_latest.sql

# For data-only dumps (requires tables to already exist)
pg_dump -h treasuremap.host.org -U treasuremap -d treasuremap \
  --exclude-table-data='public.flask*' \
  --no-owner --no-privileges \
  -a -f ./dump_latest.sql
```

## Monitoring and Debugging

### Checking Deployment Status

View all resources in the GWTM namespace:

```bash
# Get all pods and their status
kubectl get pods -n gwtm

# Get all services
kubectl get services -n gwtm

# Get all deployments with replica counts
kubectl get deployments -n gwtm

# Get detailed status of all resources
kubectl get all -n gwtm
```

### Watching Deployment Progress

Monitor pods as they start up:

```bash
# Watch all pods in real-time
kubectl get pods -n gwtm --watch

# Watch with wide output (shows node assignment)
kubectl get pods -n gwtm -o wide --watch

# Describe a specific pod for detailed events
kubectl describe pod <pod-name> -n gwtm
```

### Viewing Logs

**View logs from specific components:**

```bash
# Frontend (Svelte) logs
kubectl logs -n gwtm deployment/frontend -f

# FastAPI backend logs (recommended for new development)
kubectl logs -n gwtm deployment/fastapi-backend -f

# Flask backend logs (legacy)
kubectl logs -n gwtm deployment/flask-backend -f

# PostgreSQL logs
kubectl logs -n gwtm deployment/postgres -f
```

**View logs from a specific pod:**

```bash
# Get pod names
kubectl get pods -n gwtm

# View logs from a specific pod
kubectl logs -n gwtm <pod-name> -f

# View previous container logs (if pod crashed)
kubectl logs -n gwtm <pod-name> --previous
```

**View logs from all replicas of a deployment:**

```bash
# All frontend pods
kubectl logs -n gwtm -l app=frontend --all-containers=true -f

# All FastAPI backend pods
kubectl logs -n gwtm -l app=fastapi-backend --all-containers=true -f
```

**Filter and search logs:**

```bash
# Search for errors in FastAPI logs
kubectl logs -n gwtm deployment/fastapi-backend | grep -i error

# View last 100 lines
kubectl logs -n gwtm deployment/frontend --tail=100

# Logs since specific time
kubectl logs -n gwtm deployment/fastapi-backend --since=10m
```

### Checking Resource Usage

```bash
# View resource usage for all pods
kubectl top pods -n gwtm

# View resource usage for nodes
kubectl top nodes

# Describe pod to see resource limits and requests
kubectl describe pod <pod-name> -n gwtm | grep -A 5 "Limits\|Requests"
```

### Interactive Debugging

**Execute commands inside containers:**

```bash
# Open shell in FastAPI backend
kubectl exec -it -n gwtm deployment/fastapi-backend -- /bin/bash

# Open shell in frontend container
kubectl exec -it -n gwtm deployment/frontend -- /bin/sh

# Open psql in database
kubectl exec -it -n gwtm deployment/postgres -- psql -U treasuremap -d treasuremap
```

**Port forwarding for direct access:**

```bash
# Forward database port for local access
kubectl port-forward -n gwtm service/postgres 5432:5432

# Access from local machine
psql -h localhost -U treasuremap -d treasuremap
```

### Event Listener Monitoring (if enabled)

```bash
# LIGO listener logs
kubectl logs -n gwtm deployment/ligo-listener -f

# IceCube listener logs
kubectl logs -n gwtm deployment/icecube-listener -f

# Check listener configuration
kubectl get configmap -n gwtm
kubectl describe configmap <listener-configmap-name> -n gwtm
```

### Troubleshooting Skaffold

```bash
# Verbose output for debugging build/deploy issues
skaffold dev -v debug

# Skip tests during build
skaffold dev --skip-tests

# Clean up and restart
skaffold delete
skaffold dev

# Build without deploying
skaffold build

# Deploy without building
skaffold deploy
```

### Restarting Components

```bash
# Restart a specific deployment (triggers rolling restart)
kubectl rollout restart deployment/frontend -n gwtm
kubectl rollout restart deployment/fastapi-backend -n gwtm
kubectl rollout restart deployment/flask-backend -n gwtm

# Check rollout status
kubectl rollout status deployment/frontend -n gwtm

# View rollout history
kubectl rollout history deployment/frontend -n gwtm
```

### Checking Persistent Volumes

```bash
# View persistent volume claims
kubectl get pvc -n gwtm

# Describe PVC to see binding status
kubectl describe pvc postgres-data -n gwtm

# View persistent volumes
kubectl get pv
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
  zenodo-access-key: base64_encoded_value

  # Storage credentials (choose based on STORAGE_BUCKET_SOURCE)
  # For S3:
  aws-access-key-id: base64_encoded_value
  aws-secret-access-key: base64_encoded_value

  # For Azure Blob Storage:
  azure-account-name: base64_encoded_value
  azure-account-key: base64_encoded_value

  # For Swift/OpenStack:
  swift-username: base64_encoded_value
  swift-password: base64_encoded_value
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

#### 1. Database Connection Errors

Check database pod status and logs:
```bash
# Verify postgres pod is running
kubectl get pods -n gwtm | grep postgres

# Check database logs for connection issues
kubectl logs -n gwtm deployment/postgres

# Test database connectivity from within cluster
kubectl exec -it -n gwtm deployment/fastapi-backend -- nc -zv postgres 5432

# Verify database service exists
kubectl get service postgres -n gwtm
```

#### 2. Backend Startup Failures

**FastAPI Backend:**
```bash
# Check FastAPI logs for startup errors
kubectl logs -n gwtm deployment/fastapi-backend --tail=100

# Verify environment variables
kubectl exec -n gwtm deployment/fastapi-backend -- env | grep -E 'DB_'

# Check pod events
kubectl describe pod -n gwtm -l app=fastapi-backend
```

**Flask Backend:**
```bash
# Check Flask logs
kubectl logs -n gwtm deployment/flask-backend --tail=100

# Verify migrations ran successfully
kubectl logs -n gwtm deployment/flask-backend | grep -i migration
```

#### 3. Frontend Issues

```bash
# Check Svelte frontend logs
kubectl logs -n gwtm deployment/frontend --tail=100

# Verify frontend can reach backends
kubectl exec -it -n gwtm deployment/frontend -- wget -O- http://fastapi-backend:8000/health
kubectl exec -it -n gwtm deployment/frontend -- wget -O- http://flask-backend:8080/api/v0/

# Check environment variables
kubectl exec -n gwtm deployment/frontend -- env | grep PUBLIC_API
```

#### 4. Port Forwarding Issues

```bash
# Kill existing port forwards
pkill -f "port-forward.*gwtm"

# Restart skaffold
skaffold delete
skaffold dev

# Manually set up port forwards
kubectl port-forward -n gwtm service/frontend 3000:3000 &
kubectl port-forward -n gwtm service/fastapi-backend 8000:8000 &
kubectl port-forward -n gwtm service/flask-backend 8080:8080 &
```

#### 5. Image Pull/Build Issues

```bash
# Check image pull status
kubectl describe pod -n gwtm <pod-name> | grep -A 10 Events

# Rebuild images with verbose output
skaffold build -v debug

# Check if images exist locally
docker images | grep gwtm

# Force rebuild
skaffold delete
skaffold dev --cache-artifacts=false
```

#### 6. Persistence Issues

If using persistence, ensure storage classes are configured:
```bash
# List storage classes
kubectl get sc

# Check PVC status
kubectl get pvc -n gwtm

# Describe PVC for detailed status
kubectl describe pvc postgres-data -n gwtm

# Check PV binding
kubectl get pv | grep gwtm
```

#### 7. Resource Constraints

```bash
# Check if pods are being OOMKilled or CPU throttled
kubectl describe pod -n gwtm <pod-name> | grep -A 5 "Last State"

# View resource usage
kubectl top pods -n gwtm

# Temporarily increase resources in values-dev.yaml if needed
```

#### 8. Secret Issues

```bash
# Verify secrets exist
kubectl get secrets -n gwtm

# Check secret contents (base64 encoded)
kubectl get secret gwtm-secrets -n gwtm -o yaml

# Decode specific secret value
kubectl get secret gwtm-secrets -n gwtm -o jsonpath='{.data.db-password}' | base64 -d
```

#### 9. Networking Issues Between Services

```bash
# Test connectivity between services
kubectl exec -it -n gwtm deployment/fastapi-backend -- nc -zv postgres 5432
kubectl exec -it -n gwtm deployment/frontend -- nc -zv fastapi-backend 8000

# Check service endpoints
kubectl get endpoints -n gwtm

# Verify DNS resolution
kubectl exec -it -n gwtm deployment/frontend -- nslookup fastapi-backend
```

#### 10. Complete Reset

If all else fails, clean up and redeploy:
```bash
# Delete everything
skaffold delete

# Delete namespace (optional, removes all data)
kubectl delete namespace gwtm

# Redeploy
cd gwtm-helm
skaffold dev
```

### Getting More Help

For additional debugging:
```bash
# Dump all cluster state for GWTM namespace
kubectl get all,configmaps,secrets,pvc,pv -n gwtm -o wide > gwtm-cluster-state.txt

# Export pod logs for all components
kubectl logs -n gwtm deployment/frontend > frontend-logs.txt
kubectl logs -n gwtm deployment/fastapi-backend > fastapi-logs.txt
kubectl logs -n gwtm deployment/flask-backend > flask-logs.txt
kubectl logs -n gwtm deployment/postgres > postgres-logs.txt
```
