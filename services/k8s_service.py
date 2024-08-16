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

def get_workflow_pods(workflow_id: str) -> List[client.V1Pod]:
    config.load_kube_config()  # 或者使用 config.load_incluster_config() 如果在集群内运行
    v1 = client.CoreV1Api()

    # 假设 Argo 使用 'workflows.argoproj.io/workflow' 标签来标识工作流
    label_selector = f"workflows.argoproj.io/workflow={workflow_id}"
    
    pods = v1.list_pod_for_all_namespaces(label_selector=label_selector)
    return pods.items

def find_visualization_pod(pods: List[client.V1Pod]) -> Optional[client.V1Pod]:
    for pod in pods:
        # 这里的筛选条件需要根据实际情况调整
        # 可能是通过检查 Pod 的名称、标签或注解来识别可视化节点
        if "visualization" in pod.metadata.name or pod.metadata.labels.get("node-type") == "visualization":
            return pod
    return None

def get_visualization_pod_name(workflow_id: str) -> Optional[str]:
    pods = get_workflow_pods(workflow_id)
    viz_pod = find_visualization_pod(pods)
    if viz_pod:
        return viz_pod.metadata.name
    return None

def create_k8s_resources(name: str) -> str:
    namespace = get_namespace()
    service_name = f"{name}-svc"
    ingress_name = f"{name}-ing"
    # ingress_domain设置
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

            # 要先确认标签
            selector={"app": name},
            ports=[client.V1ServicePort(port=80, target_port=80)]
        )
    )

    # Define Ingress
    ingress = client.V1Ingress(
        metadata=client.V1ObjectMeta(name=ingress_name),
        spec=client.V1IngressSpec(
            rules=[client.V1IngressRule(
                # host设置和path设置
                host=ingress_domain,
                http=client.V1HTTPIngressRuleValue(
                    paths=[client.V1HTTPIngressPath(
                        path=f"/{name}",
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

        # 获取并打印service和Ingress信息
        service_info = v1.read_namespaced_service(name=service_name, namespace=namespace)
        logger.info(f"Service: {service_info.metadata.name}, Cluster IP: {service_info.spec.cluster_ip}")

        ingress_info = networking_v1.read_namespaced_ingress(name=ingress_name, namespace=namespace)
        logger.info(f"Ingress: {ingress_info.metadata.name}, Host: {ingress_info.spec.rules[0].host}")

    except client.ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise Exception(f"Kubernetes API error: {e}")

    # URL构造注意一下
    url = f"http://{ingress_domain}/{name}/"
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
        if e.status == 404:
            logger.warning(f"Resource not found: {e}")        
        else: 
            logger.error(f"Kubernetes API error: {e}")
            raise Exception(f"Kubernetes API error: {e}")