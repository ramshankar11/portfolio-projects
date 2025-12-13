# GCP 3-Tier Infrastructure with Terraform

This project uses **Infrastructure as Code (IaC)** to provision a scalable 3-Tier architecture on Google Cloud Platform.

## Architecture
- **VPC Network**: Custom `portfolio-vpc`.
- **Subnets**: Public (Web) and Private (DB) separation.
- **Compute Engine**: 
  - Managed Instance Group (MIG) for high availability.
  - Autoscaling web servers running Nginx.
  - Startup script to verify deployment.
- **Database**: 
  - Cloud SQL (MySQL) instance in private network.
- **Security**: Firewall rules allowing HTTP only to web tier.

## Prerequisites
- Terraform installed
- A GCP Project with Billing enabled
- Google Cloud SDK (`gcloud`) authenticated

## How to Deploy
1. **Initialize Terraform**:
   ```bash
   terraform init
   ```

2. **Plan (Preview Changes)**:
   ```bash
   terraform plan -var="project_id=YOUR_PROJECT_ID" -var="db_password=YOUR_DB_PASSWORD"
   ```

3. **Apply (Create Infrastructure)**:
   ```bash
   terraform apply -var="project_id=YOUR_PROJECT_ID" -var="db_password=YOUR_DB_PASSWORD"
   ```

4. **Clean Up**:
   ```bash
   terraform destroy -var="project_id=YOUR_PROJECT_ID" -var="db_password=YOUR_DB_PASSWORD"
   ```

## Key Concepts
- **Modular Networking**: Defining custom VPCs instead of using default.
- **Immutable Infrastructure**: Using Instance Templates.
- **High Availability**: Using Instance Groups instead of single VMs.
- **Secure Database**: Private IP only for database access.
