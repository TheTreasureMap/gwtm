# ArgoCD Configuration

This directory contains GitOps-managed ArgoCD configuration, including cluster connections.

## Files

- **`cluster-gwtm-dev.yaml`** - Dev cluster connection with insecure TLS (self-signed cert)
- **`argocd-config-app.yaml`** - ArgoCD Application to manage these configs

## Setup

### One-time setup (bootstrap)

Apply the ArgoCD Application to the ArgoCD cluster:

```bash
kubectl apply -f argocd-config/argocd-config-app.yaml \
  --kubeconfig=/path/to/argocd/kubeconfig \
  --insecure-skip-tls-verify
```

Then sync:
```bash
argocd app sync argocd-config
```

### How it works

Once the Application is created:
1. ArgoCD watches this directory in the gwtm repo
2. Any changes to cluster configurations are automatically synced
3. The cluster connection can't be manually misconfigured
4. All changes are version controlled

## Adding new clusters

To add a new cluster connection:

1. Create a new Secret YAML file: `cluster-<name>.yaml`
2. Follow the same format as `cluster-gwtm-dev.yaml`
3. Commit and push to the svelte branch
4. ArgoCD will automatically sync the new cluster

## TODO

- [ ] Replace self-signed certificates with proper TLS (Let's Encrypt)
- [ ] Remove `insecure: true` flag once proper certs are in place
