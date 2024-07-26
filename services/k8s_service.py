import os
import logging
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_namespace():
    return os.getenv('K8S_NAMESPACE', 'default')

def load_k8s_config():
    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()

def create_k8s_resources(name: str) -> str:
    namespace = get_namespace()
    service_name = f"{name}-svc"
    ingress_name = f"{name}-ing"
    ingress_domain = os.getenv('INGRESS_DOMAIN', 'your-ingress-domain')

    # Validate environment variables
    if not ingress_domain:
        raise ValueError("Environment variable INGRESS_DOMAIN is not set")

    load_k8s_config()

    v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()

    # Define Service
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=service_name),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(port=80, target_port=80)]
        )
    )

    # Define Ingress
    ingress = client.V1Ingress(
        metadata=client.V1ObjectMeta(name=ingress_name),
        spec=client.V1IngressSpec(
            rules=[client.V1IngressRule(
                http=client.V1HTTPIngressRuleValue(
                    paths=[client.V1HTTPIngressPath(
                        path="/",
                        path_type="Prefix",
                        backend=client.V1IngressBackend(
                            service=client.V1IngressServiceBackend(
                                name=service_name,
                                port=client.V1ServiceBackendPort(number=80)
                            )
                        )
                    )]
                )
            )]
        )
    )

    try:
        logger.info("Creating Kubernetes Service and Ingress...")
        v1.create_namespaced_service(namespace=namespace, body=service)
        networking_v1.create_namespaced_ingress(namespace=namespace, body=ingress)
        logger.info("Service and Ingress created successfully.")
    except client.ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise Exception(f"Kubernetes API error: {e}")

    # Return the URL
    url = f"http://{ingress_domain}/{ingress_name}/"
    return url

def delete_k8s_resources(name: str):
    namespace = get_namespace()
    service_name = f"{name}-svc"
    ingress_name = f"{name}-ing"

    load_k8s_config()

    v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()

    try:
        logger.info("Deleting Kubernetes Service and Ingress...")
        networking_v1.delete_namespaced_ingress(name=ingress_name, namespace=namespace)
        v1.delete_namespaced_service(name=service_name, namespace=namespace)
        logger.info("Service and Ingress deleted successfully.")
    except client.ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise Exception(f"Kubernetes API error: {e}")