# k8s_service.py
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
        # initialize k8s client
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
        # generate resource names
        shorter_name = name[:50]
        return K8sResourceNames(
            service_name=f"viz-svc-{shorter_name}",
            ingress_name=f"viz-ing-{shorter_name}",
            namespace=self.namespace,
            original_name=name,
            label = label,
            base_url = base_url,
            needs_base_path = needs_base_path,
            target_port = target_port
        )

    async def _check_resources_exist(self, names: K8sResourceNames) -> Tuple[bool, bool]:
        # check if resources exist
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

    def _create_service_spec(self, names: K8sResourceNames) -> client.V1Service:
        # create service spec
        selector_labels = {
            "workflows.argoproj.io/workflow": names.original_name,
            "app": f"{names.label}"
        }

        return client.V1Service(
            metadata=client.V1ObjectMeta(name=names.service_name),
            spec=client.V1ServiceSpec(
                selector=selector_labels,
                # ports=[client.V1ServicePort(port=80, target_port=5173)]
                ports=[client.V1ServicePort(port=80, target_port=names.target_port)]
            )
        )

    def _create_ingress_spec(self, names: K8sResourceNames) -> client.V1Ingress:
        annotations = {}
        # Handle base path rewriting for nested applications
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
        
        # create ingress spec
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
                            # path=f"/{names.original_name}",
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

    async def create_resources(self, name: str, label: str, base_url: str, needs_base_path: bool, target_port: int) -> str:
        # create resources
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
                ingress_spec = self._create_ingress_spec(names)
                await asyncio.to_thread(
                    self.networking_v1.create_namespaced_ingress,
                    namespace=names.namespace, 
                    body=ingress_spec
                )
                logger.info(f"Ingress {names.ingress_name} created")

        except client.ApiException as e:
            logger.error(f"Failed to create resources: {e}")
            raise Exception(f"Kubernetes API error: {e}")

        return self._generate_url(names.original_name)

    async def delete_resources(self, name: str, label: str) -> None:
        # delete resources
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
        # generate url
        return f"http://{self.ingress_domain}/{name}/"