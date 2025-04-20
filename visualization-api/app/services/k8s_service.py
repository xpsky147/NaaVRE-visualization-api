from dataclasses import dataclass
from typing import Optional, Tuple
import os
import logging
import asyncio
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class K8sResourceNames:
    service_name: str
    ingress_name: str
    namespace: str
    original_name: str
    label: str
    base_url: str
    needs_base_path: bool
    target_port: int

class K8sResourceManager:
    def __init__(self):
        # Set namespace and ingress domain from environment variables
        self.namespace = os.getenv('K8S_NAMESPACE', 'default')
        self.ingress_domain = os.getenv('INGRESS_DOMAIN')
        if not self.ingress_domain:
            raise ValueError("Environment variable INGRESS_DOMAIN is not set")
        
        try:
            config.load_kube_config()
        except ConfigException:
            config.load_incluster_config()
        self.core_v1 = client.CoreV1Api()
        self.networking_v1 = client.NetworkingV1Api()

    def _generate_resource_names(self, name: str, label: str, base_url: str, needs_base_path: bool, target_port: int) -> K8sResourceNames:
        shorter_name = name[:50]
        return K8sResourceNames(
            service_name=f"viz-svc-{shorter_name}",
            ingress_name=f"viz-ing-{shorter_name}",
            namespace=self.namespace,
            original_name=name,
            label=label,
            base_url=base_url,
            needs_base_path=needs_base_path,
            target_port=target_port
        )

    async def _check_resources_exist(self, names: K8sResourceNames) -> Tuple[bool, bool]:
        service_exists = False
        ingress_exists = False

        try:
            await asyncio.to_thread(
                self.core_v1.read_namespaced_service,
                name=names.service_name, 
                namespace=names.namespace
            )
            service_exists = True
            logger.info(f"Service {names.service_name} already exists")
        except client.ApiException as e:
            if e.status != 404:
                raise Exception(f"Kubernetes API error: {e}")

        try:
            await asyncio.to_thread(
                self.networking_v1.read_namespaced_ingress,
                name=names.ingress_name, 
                namespace=names.namespace
            )
            ingress_exists = True
            logger.info(f"Ingress {names.ingress_name} already exists")
        except client.ApiException as e:
            if e.status != 404:
                raise Exception(f"Kubernetes API error: {e}")

        return service_exists, ingress_exists

    def detect_visualization_type(self, container_image: str, target_port: int) -> str:
        """Detect visualization type based on container image and target port."""
        image_lower = container_image.lower() if container_image else ""
        if any(term in image_lower for term in ["jupyter", "notebook"]):
            return "jupyter"
        elif "shiny" in image_lower or target_port == 3838:
            return "rshiny"
        elif "rstudio" in image_lower or target_port == 8787:
            return "rstudio"
        elif "voila" in image_lower:
            return "voila"
        elif "streamlit" in image_lower or target_port == 8501:
            return "streamlit"
        port_type_map = {
            8888: "jupyter",
            3838: "rshiny",
            8787: "rstudio",
            8501: "streamlit"
        }
        if target_port in port_type_map:
            return port_type_map[target_port]
        return "generic-web"

    def _create_service_spec(self, names: K8sResourceNames) -> client.V1Service:
        selector_labels = {
            "workflows.argoproj.io/workflow": names.original_name,
            "app": f"{names.label}"
        }
        return client.V1Service(
            metadata=client.V1ObjectMeta(name=names.service_name),
            spec=client.V1ServiceSpec(
                selector=selector_labels,
                ports=[client.V1ServicePort(port=80, target_port=names.target_port)]
            )
        )

    VIZ_TYPE_CONFIGS = {
        "jupyter": {
            "annotations": {
                "nginx.ingress.kubernetes.io/websocket-services": "#{service_name}#",
                "nginx.ingress.kubernetes.io/proxy-read-timeout": "3600",
                "nginx.ingress.kubernetes.io/proxy-send-timeout": "3600"
            }
        },  
        "rshiny": {
            "annotations": {
                "nginx.ingress.kubernetes.io/proxy-read-timeout": "600",
                "nginx.ingress.kubernetes.io/proxy-body-size": "5m"
            }
        },
        "rstudio": {
            "annotations": {
                "nginx.ingress.kubernetes.io/proxy-read-timeout": "600",
                "nginx.ingress.kubernetes.io/proxy-body-size": "10m"
            }
        },
        "generic-web": {
            "annotations": {}
        }
    }

    def _create_ingress_spec(self, names: K8sResourceNames, viz_type: str = "generic-web") -> client.V1Ingress:
        viz_config = self.VIZ_TYPE_CONFIGS.get(viz_type, self.VIZ_TYPE_CONFIGS["generic-web"])
        annotations = viz_config.get("annotations", {}).copy()
        for key, value in annotations.items():
            if isinstance(value, str) and "#{service_name}#" in value:
                annotations[key] = value.replace("#{service_name}#", names.service_name)
        if viz_type == "jupyter":
            if names.needs_base_path:
                annotations.update({
                    "nginx.ingress.kubernetes.io/rewrite-target": f"/{names.original_name}/$2"
                })
            else:
                annotations.update({
                    "nginx.ingress.kubernetes.io/rewrite-target": "/$2"
                })
        else:
            if names.needs_base_path:
                annotations.update({
                    "nginx.ingress.kubernetes.io/rewrite-target": f"/{names.base_url}/$2",
                    "nginx.ingress.kubernetes.io/proxy-redirect-from": f"/{names.base_url}/",
                    "nginx.ingress.kubernetes.io/proxy-redirect-to": f"/{names.original_name}/"
                })
            else:
                annotations.update({
                    "nginx.ingress.kubernetes.io/rewrite-target": "/$2"
                })
        return client.V1Ingress(
            metadata=client.V1ObjectMeta(
                name=names.ingress_name,
                annotations=annotations
            ),
            spec=client.V1IngressSpec(
                ingress_class_name="nginx",
                rules=[client.V1IngressRule(
                    host=self.ingress_domain,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path=f"/{names.original_name}(/|$)(.*)",
                            path_type="Prefix",
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    name=names.service_name,
                                    port=client.V1ServiceBackendPort(number=80)
                                )
                            )
                        )]
                    )
                )]
            )
        )

    async def create_resources(self, name: str, label: str, base_url: str, 
                            needs_base_path: bool, target_port: int, 
                            viz_type: str = "generic-web") -> str:
        names = self._generate_resource_names(name, label, base_url, needs_base_path, target_port)
        service_exists, ingress_exists = await self._check_resources_exist(names)

        if service_exists and ingress_exists:
            logger.info("All resources already exist")
            return self._generate_url(names.original_name)

        try:
            if not service_exists:
                service_spec = self._create_service_spec(names)
                await asyncio.to_thread(
                    self.core_v1.create_namespaced_service,
                    namespace=names.namespace, 
                    body=service_spec
                )
                logger.info(f"Service {names.service_name} created")

            if not ingress_exists:
                ingress_spec = self._create_ingress_spec(names, viz_type)
                await asyncio.to_thread(
                    self.networking_v1.create_namespaced_ingress,
                    namespace=names.namespace, 
                    body=ingress_spec
                )
                logger.info(f"Ingress {names.ingress_name} created for {viz_type} visualization")                

        except client.ApiException as e:
            logger.error(f"Failed to create resources: {e}")
            raise Exception(f"Kubernetes API error: {e}")

        return self._generate_url(names.original_name)

    async def delete_resources(self, name: str, label: str) -> None:
        names = self._generate_resource_names(
            name, 
            label, 
            base_url="",
            needs_base_path=False,
            target_port=5173
        )

        try:
            await asyncio.to_thread(
                self.networking_v1.delete_namespaced_ingress,
                name=names.ingress_name, 
                namespace=names.namespace
            )
            logger.info(f"Ingress {names.ingress_name} deleted")
        except client.ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete ingress: {e}")

        try:
            await asyncio.to_thread(
                self.core_v1.delete_namespaced_service,
                name=names.service_name, 
                namespace=names.namespace
            )
            logger.info(f"Service {names.service_name} deleted")
        except client.ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete service: {e}")

    def _generate_url(self, name: str) -> str:
        return f"http://{self.ingress_domain}/{name}/"