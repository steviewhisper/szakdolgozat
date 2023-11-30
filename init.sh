#!/bin/bash

# a cluster indítása
minikube start

# kimentsük az OS nevét
OS_TYPE=$(uname -s)
# kimentsük a processzor architektúráját
PROCESSOR_ARCH=$(uname -p)

HOSTNAME="minikube.local"

# ha arm az architektúra, akkor minikbue ip helyett a 127.0.0.1 ip-t kell resolvolni minikube.local hostként
if [ "$OS_TYPE" == "Darwin" ]; then
    if [ "$PROCESSOR_ARCH" == "arm" ]; then
        MINIKUBE_IP=127.0.0.1
    elif [ "$PROCESSOR_ARCH" == "x86_64" ]; then
        MINIKUBE_IP=$(minikube ip)
    else
        echo "Unsupported processor architecture: $PROCESSOR_ARCH"
        exit 1
    fi
    # ha a $MINIKUBE_IP var még nincs benne az /etc/hosts fájlba, akkor írjuk bele
    if [ -n "$MINIKUBE_IP" ] && ! grep -q "$HOSTNAME" /etc/hosts; then
        echo "$MINIKUBE_IP $HOSTNAME" | sudo tee -a /etc/hosts
        echo "Added $MINIKUBE_IP $HOSTNAME to /etc/hosts"
    else
        echo "Minikube IP is not available or $HOSTNAME is already in /etc/hosts"
    fi
else
    echo "Unsupported operating system: $OS_TYPE"
    exit 1
fi

# függvény, ami megvizsgálja, hogy az architektúra arm, vagy sem
is_arm64() {
    uname -m | grep -q "arm64"
}

# az 1 végpontot tartalmazó python alkalmazás docker képének létrehozása, majd megvizsgálása
(cd ./app && docker build -t service-to-be-scaled -f Dockerfile .)

if docker image list | grep -q service-to-be-scaled; then
    echo "Docker image 'service-to-be-scaled' built successfully."
else
    echo "Failed to build Docker image. Exiting..."
    exit 1
fi

# a docker kép elindítása konténerként
docker run -p 8080:8080 --name service-to-be-scaled -d service-to-be-scaled

# a docker konténer létezésének tesztelése
if docker ps | grep -q service-to-be-scaled; then
    echo "Docker container 'service-to-be-scaled' is running."
    sleep 5
    # a docker konténer végpontjának tesztelése
    curl -v http://127.0.0.1:8080/api/v1/index | json_pp
else
    echo "Failed to run Docker container. Exiting..."
    exit 1
fi

# a docker konténer eltávolítása
docker rm $(docker stop $(docker ps -a -q --filter ancestor=service-to-be-scaled --format="{{.ID}}"))

# belépés a docker hub-ra
docker login

# docker kép tagolása, majd feltöltése docker hubra
docker tag service-to-be-scaled krisz99/service-to-be-scaled:latest
docker push krisz99/service-to-be-scaled:latest

# kubernetes namespace létrehozása
kubectl create namespace predictive-scaler
kubectl create namespace predictive-scaler

# helm telepítése
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# ingress-nginx repository letöltése és ellenőrzése
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo list | grep ingress-nginx

# Ingress-Nginx vezérlő telepítése a névtérbe
helm install nginx-ingress ingress-nginx/ingress-nginx -f nginx-ingress/ingress-values.yaml --namespace predictive-scaler

# Ingress-Nginx pod ellenőrzése
kubectl get pods -n predictive-scaler | grep ingress

# ConfigMap létrehozása Minikube IP-vel
# minikube ip használata ha az architectura nem arm64, egyébként 127.0.0.1
if is_arm64; then
    kubectl apply -f k8/host-conf-arm.yaml
else
    kubectl apply -f k8/host-conf-default.yaml
fi

# ConfigMap ellenőrzése
kubectl get configmaps -n predictive-scaler minikube-ip -o yaml

# image pull secret alkalmazása privát repository miatt
kubectl apply -f k8/pull-secret.yaml

# service és deployment alkalmazása a clusteron
kubectl apply -f app/service.yaml
kubectl apply -f app/deployment.yaml

# ha az architektúra arm64, akkor minikube tunnel indítása egy másik háttérfolyamatban
if is_arm64; then
    echo $TUNNEL_PASSWORD | base64 -D | sudo -S minikube tunnel &> /dev/null &
    sleep 60
fi

# Ingress szabályok alkalmazása Nginx Ingresshez
kubectl apply -f nginx-ingress/ingress-class.yaml

# Várjuk meg amíg az Ingress controller ready statusban lesz
until kubectl get pods -n predictive-scaler | grep 'nginx-ingress-ingress-nginx-controller' | grep '1/1'; do
    sleep 5
done

# Alkalmazzuk az ingress beállításokat
kubectl delete -A ValidatingWebhookConfiguration ingress-nginx-admission
kubectl apply -f app/ingress.yaml

# megnézzük, hogy működik-e az endpoint, illetve, hogy az Ingress beállítás helyes-e
curl -v minikube.local/api/v1/index | json_pp

# grafana config beállítása
kubectl apply -f grafana/config.yaml
# grafana service létrehozása 
kubectl apply -f grafana/service.yaml
# grafana deployment létrehozása a helm chart helyett, ugyanis itt is problémák voltak a chartal a prometheus-stack miatt
kubectl apply -f grafana/deployment.yaml
# grafana ingress létrehozása, hogy elérhető legyen port forwarding nélkül a web UI LoadBalancer typeként (ez nagyon veszélyes így, portforwarding a nyerő, vagy RBAC, esetleg HTTPS, JWT token, vagy valamilyen hitelesítés) 
kubectl apply -f grafana/ingress.yaml

# prometheus community instalálása
helm install prometheus prometheus-community/prometheus --namespace predictive-scaler
# prometheus adapter telepítése a custom metric rule-val, amit szeretnénk felhasználni minda  HPA-hoz, mind pedig a saját scalerünkhez
helm install prometheus-adapter prometheus-community/prometheus-adapter --namespace predictive-scaler --values prometheus-adapter/values.yaml --set prometheus.url="http://prometheus-server",prometheus.port="80"

# ingress létrehozása, hogy elérjük a web UI-t
kubectl apply -f prometheus/ingress.yaml

# nézzük meg, hogy megvan e a méréshez szükséges adat
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/*/nginx_ingress_controller_per_second" | json_pp

# kubernetes_deployment_status_replicas (to monitor deployed pod replicas in grafana)