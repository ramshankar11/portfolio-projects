# GKE Microservices Project

This project provisions a **Google Kubernetes Engine (GKE)** cluster using Terraform and deploys a sample scalable web application.

## Components
1. **gke_cluster.tf**: Terraform code to create a zonal GKE cluster with a managed node pool.
2. **deployment.yaml**: Kubernetes manifest defining a Deployment (3 replicas) and a LoadBalancer Service.

## Deployment Steps

### 1. Provision Cluster
```bash
terraform init
terraform apply -var="project_id=YOUR-PROJECT-ID"
# Confirm with 'yes'
```

### 2. Connect to Cluster
```bash
gcloud container clusters get-credentials portfolio-gke-cluster --region us-central1
```

### 3. Deploy Application
```bash
kubectl apply -f deployment.yaml
```

### 4. Verify
```bash
kubectl get pods
kubectl get services
# Wait for EXTERNAL-IP on the service to access the app
```

## Key Skills
- **Infrastructure as Code**: Managing Clouds resources.
- **Container Orchestration**: Pods, Services, ReplicaSets.
- **Cloud Native**: Using managed k8s services instead of raw VMs.
