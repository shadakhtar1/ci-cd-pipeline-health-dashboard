# Kubernetes Manifests for Minikube

This folder contains the Kubernetes resources required to deploy the CI/CD Dashboard locally on Minikube.

## Prerequisites
- `minikube` installed
- `kubectl` installed
- Docker installed locally

## Build images
From the repository root:

```bash
docker build -t ci-cd-backend:latest ./backend

docker build -t ci-cd-frontend:latest ./frontend
```

If Minikube uses a separate Docker daemon, load the images:

```bash
minikube image load ci-cd-backend:latest
minikube image load ci-cd-frontend:latest
```

## Deploy
```bash
kubectl apply -f namespace.yaml
kubectl apply -f storage/pvc.yaml
kubectl apply -f backend/configmap.yaml
kubectl apply -f backend/deployment.yaml
kubectl apply -f backend/service.yaml
kubectl apply -f frontend/deployment.yaml
kubectl apply -f frontend/service.yaml
kubectl apply -f frontend/ingress.yaml
```

## Verify
```bash
kubectl get pods -n ci-cd-dashboard
kubectl get svc -n ci-cd-dashboard
kubectl get ingress -n ci-cd-dashboard
```

## Access
Add the host to your OS hosts file:

```bash
echo "$(minikube ip) ci-cd-dashboard.local" | sudo tee -a /etc/hosts
```

Then open:

```bash
http://ci-cd-dashboard.local
```

Backend health:

```bash
curl http://ci-cd-dashboard.local/api/health
```

## Cleanup
```bash
kubectl delete namespace ci-cd-dashboard
minikube stop
```
