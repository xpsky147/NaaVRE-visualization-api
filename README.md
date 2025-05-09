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
6. All resources below must be created in the same namespace (e.g. visualization).

---

## 1. Clone the Repository

```bash
git clone https://github.com/xpsky147/NaaVRE-visualization-api.git
cd NaaVRE-visualization-api
```

## 2. Create TLS Secret
Assuming you have fullchain.pem and privkey.pem:

```bash
kubectl -n visualization create secret tls naavre-dev-tls \
  --cert=fullchain.pem --key=privkey.pem
```

## 2. Configure Helm Chart (helm/visualization-api/values.yaml)
### What to set
- INGRESS_DOMAIN: The Host domain that the Ingress Controller listens on to expose API & Visualizations URLs to the public.
- STREAMLIT_URL: The Streamlit Service Base URL that the API returns to the user. 
    - If your Streamlit UI is also intended to be accessed through the same domain name, fill in https://naavre-dev.minikube.test. 
    - If a different domain name or path is created, change it to the corresponding address.

```yaml
env:
  INGRESS_DOMAIN: "staging.demo.naavre.net"
  STREAMLIT_URL: "https://staging.demo.naavre.net/visualization-api"
```

- Ingress TLS: secretName must match the TLS Secret in the same namespace.
```yaml
ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: "/$1"
  hosts:
    - host: staging.demo.naavre.net
      paths:
        - path: /visualization-api/(.*)
          pathType: ImplementationSpecific
  tls:
    - hosts:
        - staging.demo.naavre.net
```


## 3. Configure Streamlit Deployment (nodes/streamlit/streamlit-deployment-simple.yaml)
Edit nodes/streamlit/streamlit-deployment-simple.yaml:
```yaml
# Within the Deployment spec:
env:
  - name: API_BASE_URL
    value: "https://staging.demo.naavre.net/visualization-api"
```

```yaml
# Add TLS to the Ingress:
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: streamlit-viz-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - staging.demo.naavre.net
  rules:
    - host: staging.demo.naavre.net
      http:
        paths:
          - path: /visualization-api(/|$)(.*)
            pathType: ImplementationSpecific
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
curl -k https://staging.demo.naavre.net/visualization-api/healthz
```
You should see something like:
```json
{ "status": "healthy", "timestamp": "2025-04-28T..." }
```

- Streamlit UI
Open in your browser: https://staging.demo.naavre.net/

- Dynamic Visualization Nodes
Run an Argo Workflow and use the returned URL, e.g.:
https://staging.demo.naavre.net/…?id=<viz_id>

## Notes & Cleanup
- TLS Termination

The TLS cert you created is terminated at the NGINX Ingress Controller: external clients talk HTTPS to Ingress, which decrypts and forwards plain HTTP to your services. As long as your cert and DNS are correct, all https://naavre-dev.minikube.test/... URLs (API or Streamlit) will work.
- Internal Traffic
    - All intra-cluster communication (Workflow → API → Streamlit) uses HTTP.
    - Only external client ↔ Ingress uses HTTPS.
- Cleanup
```bash
helm uninstall viz-test
kubectl delete -f nodes/streamlit/streamlit-deployment-simple.yaml
```

---
### TLS Certificates & Ingress -– How It Works

When you `create secret tls naavre-dev-tls…` and reference it in **each** Ingress:

```yaml
spec:
  tls:
    - hosts: ["naavre-dev.minikube.test"]
      secretName: naavre-dev-tls
```

- Ingress Controller (NGINX) will terminate TLS: it presents your cert to the client.
- The client (browser or curl https://…) negotiates via HTTPS.
- After decryption, NGINX proxies the request via HTTP to your Service/Pod.
Result: external HTTPS access to both your API and Streamlit apps with a single certificate.

