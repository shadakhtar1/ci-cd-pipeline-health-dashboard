#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

exec > >(tee /var/log/deployment.log)
exec 2>&1

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*"
}

log "Starting CI/CD Dashboard deployment"

# Update Ubuntu and install the core packages required for Docker and Git operations.
apt-get update
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

# Wait until the Docker daemon is ready before executing Docker commands.
until docker info >/dev/null 2>&1
 do
  log "Waiting for Docker daemon to become ready..."
  sleep 2
done

# Add the admin user to the docker group so Docker commands can be run without sudo.
ADMIN_USERNAME="${ADMIN_USERNAME:-}"
if [ -z "$ADMIN_USERNAME" ]; then
  ADMIN_USERNAME="$(getent passwd 1000 | cut -d: -f1 || true)"
fi
if [ -z "$ADMIN_USERNAME" ] && [ -d /home ]; then
  ADMIN_USERNAME="$(ls /home | head -n1 2>/dev/null || true)"
fi
if [ -z "$ADMIN_USERNAME" ]; then
  ADMIN_USERNAME="root"
fi

if [ "$ADMIN_USERNAME" != "root" ] && id "$ADMIN_USERNAME" >/dev/null 2>&1; then
  usermod -aG docker "$ADMIN_USERNAME"
  log "Added $ADMIN_USERNAME to the docker group."
fi

# Clone the application repository if it is not already present.
REPO_ROOT="/opt/ci-cd-pipeline-health-dashboard"
REPO_PATH="$REPO_ROOT/CI-CD-Dashboard"
if [ ! -d "$REPO_PATH/.git" ]; then
  rm -rf "$REPO_PATH"
  git clone https://github.com/shadakhtar1/ci-cd-pipeline-health-dashboard.git "$REPO_PATH"
  log "Cloned repository into $REPO_PATH"
else
  log "Repository already exists; syncing repository"
  git -C "$REPO_PATH" fetch origin --prune || {
    log "Git fetch failed"
    exit 1
  }
  if ! git -C "$REPO_PATH" reset --hard origin/main >/dev/null 2>&1; then
    if ! git -C "$REPO_PATH" reset --hard origin/master >/dev/null 2>&1; then
      log "Failed to reset repository to origin/main or origin/master"
      exit 1
    fi
  fi
fi

# Ensure the cloned repository is owned by the deployment user.
if [ "$ADMIN_USERNAME" != "root" ] && id "$ADMIN_USERNAME" >/dev/null 2>&1; then
  chown -R "$ADMIN_USERNAME:$ADMIN_USERNAME" "$REPO_ROOT"
  log "Set ownership of the repository to $ADMIN_USERNAME"
fi

# Change into the project directory and update it in place.
cd "$REPO_PATH"

# Ensure the backend environment file exists before Docker Compose starts.
if [ ! -f backend/.env ] && [ -f backend/.env.example ]; then
  cp backend/.env.example backend/.env
  log "Created backend/.env from backend/.env.example"
elif [ ! -f backend/.env ]; then
  log "backend/.env is missing and backend/.env.example is unavailable"
  exit 1
fi

# Build and start the containers using Docker Compose.
log "Starting Docker Compose services"
if ! docker compose up --build -d; then
  log "Docker Compose failed; printing logs"
  docker compose logs --tail=200 || true
  exit 1
fi

# Wait until the backend health endpoint responds successfully.
log "Waiting for backend health endpoint"
HEALTH_URL="http://127.0.0.1:8000/api/health"
for attempt in $(seq 1 600); do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    log "Backend health check passed"
    break
  fi

  sleep 1
  if [ "$attempt" -eq 600 ]; then
    log "Backend health check timed out after 10 minutes"
    docker compose ps || true
    docker compose logs --tail=200 || true
    exit 1
  fi
done

log "Deployment completed successfully"
log "Frontend: http://<VM_PUBLIC_IP>:3000"
log "Backend: http://<VM_PUBLIC_IP>:8000"
