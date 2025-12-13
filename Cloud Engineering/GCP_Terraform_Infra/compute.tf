# Instance Template
resource "google_compute_instance_template" "web_template" {
  name        = "web-server-template"
  description = "This template is used to create web server instances."

  tags = ["web-server"]

  labels = {
    environment = "dev"
  }

  instance_description = "Web Server"
  machine_type         = "e2-micro"
  can_ip_forward       = false

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
  }

  # Create a new boot disk from an image
  disk {
    source_image = "debian-cloud/debian-11"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.public_subnet.id
    access_config {
      # Ephemeral IP
    }
  }

  metadata = {
    startup-script = <<-EOF
      #! /bin/bash
      apt-get update
      apt-get install -y nginx
      service nginx start
      echo "Hello from Terraform GCP!" > /var/www/html/index.html
    EOF
  }
}

# Managed Instance Group
resource "google_compute_instance_group_manager" "web_mig" {
  name = "web-mig"

  base_instance_name = "web"
  zone               = var.zone

  version {
    instance_template  = google_compute_instance_template.web_template.id
  }

  target_size  = 2
}
