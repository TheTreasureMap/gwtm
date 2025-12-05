# GWTM Deployment Workflow

This guide describes the GitOps workflow for deploying GWTM from development to production.

## Overview

GWTM uses a GitOps approach with two repositories:
- **gwtm repository** (this repo) - Application source code and Helm charts
- **gwtm-deploy repository** - ArgoCD Application manifests for each environment

```
Developer Workflow:
┌─────────────────────────────────────────────────────────────────────┐
│  1. Develop    2. Test      3. Merge     4. Deploy    5. Promote   │
│     Feature    Locally      to Master    to Dev       to Prod      │
└─────────────────────────────────────────────────────────────────────┘
   │              │            │            │            │
   ▼              ▼            ▼            ▼            ▼
 Branch      Skaffold       GitHub       ArgoCD       Git Tag
  Code         Dev           PR         Auto-Sync    + Manual Sync
```

## Prerequisites

Before following this workflow, you'll need:

1. **kubectl access to dev and prod clusters**
   - You need the kubeconfig files for the environments you'll deploy to
   - See [Getting Access in gwtm-deploy HOW_TO.md](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#2-getting-access-for-team-members) for obtaining kubeconfig files
   - See [Accessing Your Kubernetes Cluster](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#3-accessing-your-kubernetes-cluster) for setting up KUBECONFIG

2. **ArgoCD access**
   - **Recommended:** Use the ArgoCD web UI
   - Members of the TreasureMap GitHub organization can log in with their GitHub credentials
   - See [Accessing ArgoCD](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#5-accessing-argocd) for finding the ArgoCD URL
   - **Advanced:** ArgoCD CLI is available for power users
     - Install: [ArgoCD CLI installation guide](https://argo-cd.readthedocs.io/en/stable/cli_installation/)
     - Login instructions in [gwtm-deploy HOW_TO.md](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#5-accessing-argocd)


### Quick Setup: Setting KUBECONFIG

```bash
# For dev environment
export KUBECONFIG=/path/to/gwtm-deploy/dev/kubeconfig

# Verify connection
kubectl get nodes

# For prod environment (when promoting to production)
export KUBECONFIG=/path/to/gwtm-deploy/prod/kubeconfig

# Verify connection
kubectl get nodes
```

For detailed instructions on obtaining and managing kubeconfig files, see the [gwtm-deploy HOW_TO.md](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#3-accessing-your-kubernetes-cluster).

## Automated Image Building

This repository has GitHub Actions configured to automatically build and push Docker images:

**Triggers:**
- Any git tag matching `v*` (e.g., `v1.234`)
- Pushes to `master` branch (tagged as `:latest`)

**What Gets Built:**
```bash
# When you push tag v1.234, GitHub Actions builds and pushes:
ghcr.io/thetreasuremap/gwtm/flask-app:1.234
ghcr.io/thetreasuremap/gwtm/fastapi-backend:1.234
ghcr.io/thetreasuremap/gwtm/svelte-frontend:1.234

# Also tagged as:
ghcr.io/thetreasuremap/gwtm/flask-app:latest  (if from master)
```

**Location:** `.github/workflows/build-all.yml`

## Step-by-Step: Development to Production

### Phase 1: Development

```bash
# 1. Create feature branch
git checkout -b feature/my-new-feature

# 2. Make your changes
# Edit code in server/, frontend/, or src/

# 3. Test locally with Skaffold
cd gwtm-helm
skaffold dev
# This builds local images and deploys to your local K8s cluster
# Access at http://localhost:8000 (FastAPI), http://localhost:3000 (Frontend)

# 4. Run tests (assumes you have a virtualenv set up with dependencies installed)
cd ..
source venv/bin/activate
pytest tests/fastapi/ -v

# 5. Commit and push
git commit -am "Add my new feature"
git push origin feature/my-new-feature
```

### Phase 2: Merge to Master

```bash
# 6. Create Pull Request on GitHub
# - Review code changes
# - Run CI tests (if configured)
# - Get approval from team member

# 7. Merge PR to master
# - GitHub Actions automatically builds images tagged as :latest
# - Images pushed to ghcr.io/thetreasuremap/gwtm/*:latest
```

### Phase 3: Deploy to Dev Environment

```bash
# 8. ArgoCD automatically syncs dev from master branch
# Dev environment watches: master branch
# Images used: :latest tags

# View dev deployment:
# - Recommended: Open ArgoCD web UI and check gwtm-dev application status
# - CLI alternative: argocd app get gwtm-dev
# - Force sync if needed: Click "SYNC" button in UI or run: argocd app sync gwtm-dev

# Monitor deployment:
kubectl get pods -n gwtm-dev -w

# For more detailed monitoring commands, see:
# https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#6-monitoring-application-deployments

# 9. Test on dev cluster
# Access dev endpoints (check with your infrastructure team for IPs)
# Verify functionality works correctly
# Check logs for errors: kubectl logs -n gwtm-dev deployment/fastapi-backend

# For more logging commands, see:
# https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#7-viewing-logs-and-troubleshooting
```

### Phase 4: Create Release Tag

```bash
# 10. Once dev testing passes, create a release tag
git checkout master
git pull origin master

# Create annotated tag
git tag -a v1.234 -m "Release v1.234: Add new feature X"

# Push tag to GitHub
git push origin v1.234

# 11. GitHub Actions automatically triggered
# - Builds images for all three components (Flask, FastAPI, Frontend)
# - Tags images as: 1.234 (strips the 'v' prefix)
# - Pushes to: ghcr.io/thetreasuremap/gwtm/*:1.234
# - Takes ~5-10 minutes to complete

# Monitor build progress:
# - Go to GitHub repository -> Actions tab
# - Watch "Build and Push All Images" workflow
```

### Phase 5: Update Production Configuration

```bash
# 12. Update ArgoCD Application to point to new tag
cd /path/to/gwtm-deploy

# Edit the production application manifest
# Option A: Update targetRevision in Application manifest
vim dev/application.yaml  # or prod/application.yaml

# Find the line with targetRevision and update:
# FROM: targetRevision: v1.233
# TO:   targetRevision: v1.234

# Option B: Update image tags in values-prod.yaml
# (This approach is more explicit about which image versions are deployed)

# 13. Commit and push to gwtm-deploy repository
git add dev/application.yaml  # or prod/application.yaml
git commit -m "Deploy v1.234 to production"
git push origin master
```

### Phase 6: Deploy to Production

```bash
# 14. ArgoCD detects change in gwtm-deploy repository
# - Production requires MANUAL sync (for safety)
# - ArgoCD will show app as "OutOfSync"

# 15. Manually sync production
# Recommended: Use ArgoCD Web UI
# - Open ArgoCD UI (log in with your GitHub credentials)
# - Click on "gwtm-prod" application
# - Click "SYNC" button
# - Review changes in the confirmation dialog
# - Click "SYNCHRONIZE" to confirm

# Advanced: CLI alternative
# argocd app get gwtm-prod  # View status
# argocd app sync gwtm-prod  # Sync

# 16. Monitor production deployment
kubectl get pods -n gwtm-prod -w

# Watch for all pods to become Running:
# NAME                              READY   STATUS    RESTARTS   AGE
# fastapi-backend-xxx              1/1     Running   0          30s
# flask-backend-xxx                1/1     Running   0          30s
# frontend-xxx                     1/1     Running   0          30s

# Check application health:
# - In ArgoCD UI: Application should show green "Healthy" status
# - CLI alternative: argocd app wait gwtm-prod --health

# For detailed monitoring and troubleshooting commands, see:
# https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#6-monitoring-application-deployments
# https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#7-viewing-logs-and-troubleshooting

# 17. Verify production deployment
# - Access production endpoints
# - Run smoke tests
# - Monitor logs for errors
# - Check application metrics
```

## Rollback Procedure

If issues are discovered in production:

```bash
# Option 1: Rollback to previous version in gwtm-deploy
cd /path/to/gwtm-deploy
git revert HEAD  # Reverts the last commit
git push origin master
argocd app sync gwtm-prod

# Option 2: Update to specific previous version
vim prod/application.yaml
# Change: targetRevision: v1.233  (previous working version)
git commit -m "Rollback prod to v1.233"
git push origin master
argocd app sync gwtm-prod

# Option 3: Use ArgoCD's built-in rollback
argocd app rollback gwtm-prod <history-id>

# View deployment history to find history ID:
argocd app history gwtm-prod
```

## Environment Configuration

**Dev Environment:**
- **Watches:** `master` branch in gwtm repository
- **Image tags:** `:latest`
- **Sync:** Automatic (changes deploy immediately)
- **Purpose:** Integration testing, pre-production validation

**Prod Environment:**
- **Watches:** Specific git tags in gwtm repository (e.g., `v1.234`)
- **Image tags:** Specific versions (e.g., `:1.234`)
- **Sync:** Manual (requires explicit approval)
- **Purpose:** Production serving

## Best Practices

**DO:**
- Always test on dev before promoting to prod
- Use semantic versioning for tags (v1.2.3)
- Write descriptive commit messages and tag annotations
- Monitor deployments until all pods are healthy
- Keep a changelog of production releases
- Test rollback procedures periodically

**DON'T:**
- Don't deploy to prod without testing on dev first
- Don't skip version tags (they're your rollback points)
- Don't force-push tags (they should be immutable)
- Don't deploy on Friday afternoon (if you can avoid it!)
- Don't ignore health checks or warnings in ArgoCD

## Troubleshooting Deployments

### GitHub Actions build failed

```bash
# Check GitHub Actions logs
# Go to: github.com/TheTreasureMap/gwtm/actions
# Click on failed workflow
# Review build logs for errors
```

### ArgoCD shows "ImagePullBackOff"

```bash
# Verify image exists in registry
# Check if tag was pushed correctly:
# Go to: github.com/TheTreasureMap/gwtm/pkgs/container/gwtm%2Ffastapi-backend

# Check pod events:
kubectl describe pod <pod-name> -n gwtm-prod
```

## Additional Resources

- **Infrastructure Operations:** See [gwtm-deploy HOW_TO.md](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md) for:
  - Accessing Kubernetes clusters
  - [Monitoring deployments](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#6-monitoring-application-deployments)
  - [Viewing logs and troubleshooting](https://github.com/TheTreasureMap/gwtm-deploy/blob/master/HOW_TO.md#7-viewing-logs-and-troubleshooting)
  - Finding application endpoints and IPs
- **API Documentation:** http://localhost:8000/docs (when running locally)
