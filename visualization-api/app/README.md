# API Deployment Guide

A modular, cloud-native platform for scientific computing, workflow orchestration, and interactive data visualization.

## Project Structure

- **visualization-api/**  
  Backend API for managing visualizations and provisioning URLs.

- **nodes/**  
  Scientific computation and visualization node scripts.

- **workflow/**  
  Argo Workflow YAMLs for end-to-end pipelines.

- **helm/**  
  Helm charts for Kubernetes deployment.

See each folder’s `README.md` for detailed usage, parameters, and customization.

---

## Prerequisites

1. A Kubernetes cluster (Minikube/Kind or cloud provider)  
2. `kubectl` and `helm` installed and configured  
3. NGINX Ingress Controller deployed  
4. A TLS certificate for `naavre-dev.minikube.test`, stored as a Secret (e.g. `naavre-dev-tls`)  
5. Local hosts file mapping (for local testing): 127.0.0.1 naavre-dev.minikube.test

---

## 1. Clone the Repository

```bash
git clone https://github.com/xpsky147/NaaVRE-visualization-api.git
cd NaaVRE-visualization-api
```

## 2. Configure Helm Chart (helm/visualization-api/values.yaml)
### What to set
- INGRESS_DOMAIN: The Host domain that the Ingress Controller listens on to expose API & Visualizations URLs to the public.
- STREAMLIT_URL: The Streamlit Service Base URL that the API returns to the user. 
    - If your Streamlit UI is also intended to be accessed through the same domain name, fill in https://naavre-dev.minikube.test. 
    - If a different domain name or path is created, change it to the corresponding address.

```yaml
env:
  INGRESS_DOMAIN: "naavre-dev.minikube.test"
  STREAMLIT_URL: "https://naavre-dev.minikube.test"
```

- Ingress TLS
```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  hosts:
    - host: naavre-dev.minikube.test
      paths:
        - path: /api
          pathType: Prefix
  tls:
    - hosts:
        - naavre-dev.minikube.test
      secretName: naavre-dev-tls
```
STREAMLIT_URL must use https://….

secretName must match the TLS Secret in the same namespace.

## 3. Configure Streamlit Deployment (nodes/streamlit/streamlit-deployment-simple.yaml)
Edit nodes/streamlit/streamlit-deployment-simple.yaml:
```yaml
# Within the Deployment spec:
env:
  - name: API_BASE_URL
    value: "https://naavre-dev.minikube.test/api"

# Add TLS to the Ingress:
kind: Ingress
metadata:
  name: streamlit-viz-ingress
  annotations:
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - naavre-dev.minikube.test
      secretName: naavre-dev-tls
  rules:
    - host: naavre-dev.minikube.test
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: streamlit-viz
                port:
                  number: 80
```

## 4. Deploy Visualization-API
```bash
helm install viz-test helm/visualization-api \
  --values helm/visualization-api/values.yaml
```

## 5. Deploy Streamlit Service
```bash
kubectl apply -f nodes/streamlit/streamlit-deployment-simple.yaml
```
## 7. Verify Installation
- API Health:
```bash
curl -k https://naavre-dev.minikube.test/api/healthz
```
You should see something like:
```json
{ "status": "healthy", "timestamp": "2025-04-28T..." }
```

- Streamlit UI
Open in your browser: https://naavre-dev.minikube.test/

- Dynamic Visualization Nodes
Run an Argo Workflow and use the returned URL, e.g.:
https://naavre-dev.minikube.test/<workflow-name>/

## Notes & Cleanup
- TLS
    - For local testing, use mkcert to generate and trust certificates.
    - In production, use cert-manager + Let’s Encrypt or your CA of choice.
- Internal Traffic
    - All intra-cluster communication (Workflow → API → Streamlit) uses HTTP.
    - Only external client ↔ Ingress uses HTTPS.
- Cleanup
```bash
helm uninstall viz-test
kubectl delete -f nodes/streamlit/streamlit-deployment-simple.yaml