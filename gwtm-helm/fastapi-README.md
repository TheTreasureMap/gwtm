{{- /* This file is for documentation only and should not be processed as a template */ -}}
# FastAPI Helm Templates

These templates are used to deploy the FastAPI backend service of the GWTM application.

## Templates

- `deployment.yaml`: Defines the Kubernetes Deployment for the FastAPI service.
- `service.yaml`: Defines the Kubernetes Service for the FastAPI service.
- `configmap.yaml`: Contains configuration data for the FastAPI service.

## Configuration

Configuration for the FastAPI service is defined in the `values.yaml` file under the `fastapi` key:

```yaml
fastapi:
  name: fastapi-backend
  replicas: 2
  image:
    repository: gwtm-fastapi
    tag: latest
    pullPolicy: IfNotPresent
  service:
    port: 8000
    targetPort: 8000
  readinessProbe:
    enabled: true
    path: /docs
    initialDelaySeconds: 10
    periodSeconds: 5
  livenessProbe:
    enabled: true
    path: /docs
    initialDelaySeconds: 30
    periodSeconds: 15
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 200m
      memory: 256Mi
```

## Ingress Configuration

The FastAPI service is exposed through the following routes in the Ingress:

- `/api/v1/*`: API endpoints
- `/docs`: Swagger UI documentation
- `/redoc`: ReDoc documentation
- `/openapi.json`: OpenAPI schema
- `/health`: Health check endpoint

## Environment Variables

The FastAPI service uses environment variables from the `secrets.yaml` template, which includes:

- Database credentials
- Mail configuration
- AWS/Azure credentials
- Other application-specific settings

## Usage

To deploy the FastAPI service, include these templates in your Helm installation:

```bash
helm install gwtm ./gwtm-helm
```

You can customize the deployment by overriding values:

```bash
helm install gwtm ./gwtm-helm --set fastapi.replicas=3 --set fastapi.image.tag=v1.0.0
```

## Health Checks

The FastAPI service includes readiness and liveness probes that check the `/docs` endpoint to verify that the service is running correctly.