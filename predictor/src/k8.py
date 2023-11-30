from kubernetes import client, config

class K8ClientWrapper:
    
    def __init__(self):
        pass
    
    def get_current_pod_count(self, deployment_name):
        try:
            config.load_kube_config()
            api_instance = client.CoreV1Api()

            pod_list = api_instance.list_namespaced_pod(namespace="predictive-scaler")

            deployment_pods = [
                pod for pod in pod_list.items if pod.metadata.labels.get("app") == deployment_name
            ]

            current_pod_count = len(deployment_pods)
            print(f"Jelenlegi telepítések száma a következő telepítéshez: {deployment_name}: {current_pod_count}")
            return current_pod_count

        except Exception as e:
            print(f"Error: {e}")
            return None
        
    def create_scaled_deployments(self, api_instance, existing_deployment, replicas):
        existing_deployment_name = existing_deployment.metadata.name
        existing_deployment_namespace = existing_deployment.metadata.namespace

        existing_deployment.spec.replicas = replicas

        for i in range(replicas):
            new_deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=f"{existing_deployment_name}-scaled-{i}"),
                spec=existing_deployment.spec,
            )

            try:
                api_instance.create_namespaced_deployment(
                    namespace=existing_deployment_namespace, body=new_deployment
                )
                print(f"Telepítés: {new_deployment.metadata.name} sikeres létrehozva.")
            except client.rest.ApiException as e:
                print(f"Hiba a telepítésnél: {e}")

    def scale_up(self, deployment_name, replicas):
        try:
            config.load_kube_config()
            api_instance = client.AppsV1Api()
            existing_deployment = api_instance.read_namespaced_deployment(
                name=deployment_name, namespace="predictive-scaler"
            )

            self.create_scaled_deployments(api_instance, existing_deployment, replicas)

        except Exception as e:
            print(f"Hiba: {e}")

    def scale_down(self, deployment_name, replicas):
        try:
            config.load_kube_config()
            api_instance = client.AppsV1Api()
            existing_deployment = api_instance.read_namespaced_deployment(
                name=deployment_name, namespace="predictive-scaler"
            )

            existing_deployment.spec.replicas = replicas

            try:
                api_instance.replace_namespaced_deployment(
                    name=deployment_name,
                    namespace="predictive-scaler",
                    body=existing_deployment
                )
                print(f"Telepítés  {deployment_name} leskálázva {replicas} replikára.")
            except client.rest.ApiException as e:
                print(f"Hiba a telepítés leskálázásánál: {e}")

        except Exception as e:
            print(f"Hiba: {e}")

k8_client = K8ClientWrapper()
