#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# Update Ubuntu and install the core packages required for Docker and Git operations.
apt-get update
apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg lsb-release git

# Install Docker Engine and the Docker Compose plugin.
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start the Docker service so it runs on boot.
systemctl enable docker
systemctl start docker

# Add the admin user to the docker group so Docker commands can be run without sudo.
ADMIN_USERNAME="${ADMIN_USERNAME:-${SUDO_USER:-$(whoami)}}"
if [ "$ADMIN_USERNAME" != "root" ] && id "$ADMIN_USERNAME" >/dev/null 2>&1; then
  usermod -aG docker "$ADMIN_USERNAME"
  echo "Added $ADMIN_USERNAME to the docker group."
fi

# Clone the application repository if it is not already present.
REPO_PATH="/opt/ci-cd-pipeline-health-dashboard"
if [ ! -d "$REPO_PATH" ]; then
  git clone https://github.com/shadakhtar1/ci-cd-pipeline-health-dashboard.git "$REPO_PATH"
else
  echo "Repository already exists; skipping clone."
fi

# Change into the project directory and update it in place.
cd "$REPO_PATH"
git pull --ff-only || true

# Build and start the containers using Docker Compose.
echo "Starting Docker Compose services..."
docker compose up --build -d

# Wait until the backend container becomes healthy before printing success messages.
for i in $(seq 1 60); do
  backend_container_id="$(docker compose ps -q backend 2>/dev/null || true)"
  if [ -n "$backend_container_id" ]; then
    health_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$backend_container_id" 2>/dev/null || true)"
    if [ "$health_status" = "healthy" ]; then
      echo "Backend is healthy."
      break
    fi
  fi

  echo "Waiting for backend to become healthy..."
  sleep 10
  if [ "$i" -eq 60 ]; then
    echo "Timed out waiting for backend health. Continuing with deployment output."
  fi
done

# Print useful deployment messages.
echo "Deployment completed."
echo "Project directory: $REPO_PATH"
echo "Use 'docker compose ps' to inspect running containers."
