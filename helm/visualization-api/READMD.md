# Visualization API - Kubernetes Deployment Guide

This document describes how to deploy the Visualization API service on a Kubernetes cluster using Helm. 

## 1. Prerequisites

- You have access to a Kubernetes cluster (e.g., with kubectl and Helm 3 installed).
- You have a valid domain name (e.g., `viz.naavre.example.com`) pointing to your cluster's Ingress controller.
- You have set up a persistent volume provisioner (if you want data to survive pod restarts).

## 2. Configuration

Edit your `values.yaml` or create a custom `my-values.yaml` file. You MUST check the following settings:

```yaml
# Environment variables (required by the API)
env:
  K8S_NAMESPACE: "default"
  INGRESS_DOMAIN: "viz.naavre.example.com"
  STREAMLIT_URL: "http://viz.naavre.example.com"
  STREAMLIT_DATA_DIR: "/data/api/streamlit_visualizations"

# Ingress setup
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: viz.naavre.example.com
      paths:
        - path: /
          pathType: ImplementationSpecific

# PVC for data persistence
persistence:
  enabled: true
  size: 1Gi
  accessModes: [ "ReadWriteOnce" ]
  mountPath: /data/api/streamlit_visualizations

```

  Note:

If you want to change the data directory, update both env.STREAMLIT_DATA_DIR and persistence.mountPath.
The domain name must match your DNS and Ingress configuration.

## 3. Deploying with Helm
```bash
helm install visualization-api ./helm \
  -n default \
  --create-namespace \
  -f my-values.yaml
```

## 4. Upgrading and Rollback
To upgrade:

```bash
helm upgrade visualization-api ./helm -n default -f my-values.yaml
```

To rollback:

```bash
helm rollback visualization-api <REVISION> -n default
```

## 5. Verifying the Deployment
Check pods:
kubectl get pods -n default
Check ingress:
kubectl get ingress -n default
Visit:
http://viz.naavre.example.com in your browser
If you see errors, check logs with:

```bash
kubectl logs -l app.kubernetes.io/name=visualization-api -n default
```

## 6. Common Issues
Cannot access service from outside:
Check if INGRESS_DOMAIN and Ingress host match.
Verify DNS and Ingress controller setup.
Visualization data lost on restart:
Ensure persistence.enabled=true and PVC is bound.
Pod permission errors:
Ensure RBAC is enabled in values.yaml and your cluster allows creation of Service/Ingress.

## 7. For Developers
For local development, you may use a different helm-values.yaml for Minikube/dev setup.
Make sure to review and synchronize environment variables between production and development.
