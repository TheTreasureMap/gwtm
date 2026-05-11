# GW Treasure Map 
Website environment

## Quick Start

**For the modern FastAPI backend (recommended):**
The FastAPI application requires database and cache services. Use Skaffold for the complete development environment:
```bash
cd gwtm-helm
skaffold dev    # Starts full stack including FastAPI, database, and cache
```
FastAPI will be available at http://localhost:8000 with API docs at http://localhost:8000/docs

See the [FastAPI README](server/README.md) for detailed setup instructions and testing.

### Configuration
Configuration is handled via environmental variables. At a minimum, the following env vars must be
present:

    DB_PWD
    MAIL_PASSWORD
    RECAPTCHA_PUBLIC_KEY
    RECAPTCHA_PRIVATE_KEY
    ZENODO_ACCESS_KEY
    REDIS_URL

    # Storage backend (choose one: s3, abfs, or swift)
    STORAGE_BUCKET_SOURCE      # "s3", "abfs", or "swift"

    # AWS S3 credentials (if using s3)
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY

    # Azure credentials (if using abfs)
    AZURE_ACCOUNT_NAME
    AZURE_ACCOUNT_KEY

    # OpenStack Swift credentials (if using swift)
    OS_AUTH_URL
    OS_STORAGE_URL
    OS_USERNAME
    OS_PASSWORD
    OS_CONTAINER_NAME

For FastAPI configuration and detailed storage setup, see [server/README.md](server/README.md).

Env vars can be set by using export:

```bash
export MAIL_PASSWORD=ASecretPassword
export RECAPTCHA_PUBLIC_KEY=ASecretPassword2
```
Or by using a utility like [direnv](https://direnv.net).

### Running the application and dependencies via Docker

#### Using Skaffold with Kubernetes for Development

For a more complete development environment with Kubernetes, you can use Skaffold with the Helm chart:

1. Prerequisites:
   - Install [Skaffold](https://skaffold.dev/docs/install/)
   - Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
   - Have a Kubernetes cluster running (Minikube, Docker Desktop Kubernetes, etc.)

2. Navigate to the Helm chart directory:
```bash
cd gwtm-helm
```

3. Start the development environment:
```bash
skaffold dev
```
   This will:
   - Build the Docker image
   - Deploy the application to your Kubernetes cluster
   - Set up port-forwarding (frontend: localhost:3000, fastapi: localhost:8000)
   - Display logs in real-time
   - Automatically redeploy when files change

4. To restore sample data to the database:
```bash
cd gwtm-helm
./restore-db /path/to/your/dump.sql
```
   This script copies the SQL dump to the database pod and executes it directly.

5. Access the application:
   - Frontend dashboard: http://localhost:3000
   - FastAPI docs: http://localhost:8000/docs

6. When finished, stop Skaffold with Ctrl+C or run:
```bash
skaffold delete
```

This Kubernetes setup includes:
- PostgreSQL database with PostGIS
- Redis cache
- FastAPI backend
- Svelte frontend dashboard

## Deployment

### Environments

| Environment | URL | Deployment |
|-------------|-----|------------|
| Dev | https://dev.treasuremap.space | Auto-deploys on every push to `master` via ArgoCD Image Updater |
| Prod | https://treasuremap.space | Deploys on deliberate version tag — see release process below |

### Release process (prod)

1. **Tag the release** in this repo:
   ```bash
   git tag v1.0.x && git push origin v1.0.x
   ```
   CI will build and push images tagged `1.0.x` to GHCR.

2. **Update `gwtm-deploy`** — in `argocd-config/app-gwtm-prod.yaml`, update these three values to the new version:
   ```yaml
   targetRevision: v1.0.x
   # under parameters:
   - name: fastapi.image.tag
     value: "1.0.x"
   - name: frontend.image.tag
     value: "1.0.x"
   ```
   Commit and push. ArgoCD auto-syncs and deploys prod with immutable image tags.

### Running tests

Tests can be run from the root directory using pytest. First create a virtual environment and install the requirements:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt
pip install pytest
```

Then run the tests:
```
pytest
```
