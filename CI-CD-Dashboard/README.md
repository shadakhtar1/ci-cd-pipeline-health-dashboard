# CI/CD Pipeline Health Dashboard

## Overview
This repository contains a backend-first CI/CD pipeline health dashboard built with FastAPI, SQLAlchemy, SQLite, and React. The current backend foundation includes configuration, logging, database persistence, REST APIs, metrics, email alerts, and GitHub Actions integration.

## GitHub Actions Configuration
To enable GitHub Actions ingestion, set the following values in the backend environment file:

- GITHUB_TOKEN: personal access token with repository read permissions
- GITHUB_OWNER: GitHub repository owner or organization
- GITHUB_REPO: GitHub repository name

### Personal Access Token Setup
1. Open GitHub and navigate to Settings > Developer settings > Personal access tokens.
2. Create a token with repository read access.
3. Store the token in the backend .env file as GITHUB_TOKEN.

Example:

```env
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_OWNER=octocat
GITHUB_REPO=hello-world
```

### API Usage
- Use the refresh endpoint to ingest workflow runs from GitHub Actions:
  - POST /api/refresh
- The response includes inserted, updated, and skipped counts.

## Backend Setup
1. Change into the backend directory.
2. Create and activate a virtual environment.
3. Install dependencies from requirements.txt.
4. Copy .env.example to .env and update the values as needed.
5. Run the application with uvicorn.

Docker Compose expects the backend environment file at backend/.env. A local default file is included for development, but you should still review the values before using GitHub or SMTP features.

## Metrics Engine
The dashboard metrics endpoint exposes the following values via GET /api/dashboard:

- success rate
- failure rate
- average build duration
- last build status
- total builds
- successful builds
- failed builds
- running builds
- last refresh time

The calculations are centralized in the reusable metrics service and use the Build table as the source of truth.

## Email Alerts
The backend can send HTML email alerts for failed builds using SMTP configuration from the backend environment file.

### SMTP Configuration
Add the following values to the backend .env file:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=noreply@example.com
TO_EMAIL=team@example.com
SMTP_RECIPIENTS=ops@example.com,devops@example.com
EMAIL_ALERTS_ENABLED=true
```

### Behavior
- Email alerts are sent automatically for newly detected failed workflow runs during the GitHub refresh flow.
- The message includes workflow name, repository, branch, status, started time, and GitHub Actions run URL.
- Temporary SMTP failures are retried automatically before the process logs a warning and continues.
- If email delivery fails, the refresh flow still completes without crashing.

### Usage
Trigger a refresh at POST /api/refresh. Any newly failed build will trigger an alert if SMTP is configured correctly.

## Docker Deployment
Build and start the full stack with Docker Compose:

```bash
docker compose up --build -d
```

This starts:
- Backend API on http://localhost:8000
- Frontend UI on http://localhost:3000

The compose stack uses:
- a named network for service-to-service communication
- a named volume for SQLite persistence
- restart policies for resilience
- health checks for both services

## Azure VM Deployment
The infrastructure in the infra directory provisions an Ubuntu VM and runs the bootstrap script automatically during provisioning. The script will:

1. Install Docker and Docker Compose.
2. Add azureuser to the Docker group.
3. Clone the repository into /opt/ci-cd-pipeline-health-dashboard/CI-CD-Dashboard.
4. Set ownership of the repository to azureuser.
5. Create backend/.env from backend/.env.example if it does not already exist.
6. Start the stack with docker compose up --build -d.

## Prerequisites
- An Azure subscription.
- Azure CLI logged in with an active account.
- Terraform installed locally.
- An SSH public key for the VM.

## Azure Login
```bash
az login
```

## Terraform Workflow
From the infra directory:

```bash
terraform init
terraform plan
terraform apply
```

## SSH Access
Once the VM is provisioned, connect with:

```bash
ssh azureuser@<public-ip>
```

## Deployment Flow
After terraform apply completes, the following should happen automatically:
- Azure infrastructure is provisioned.
- The VM is created.
- Docker and Docker Compose are installed.
- The repository is cloned and configured.
- backend/.env is created from the example file if needed.
- Docker images are built and the stack starts.
- Backend health is verified before the deployment script exits.

## Troubleshooting
- If the backend does not start, verify that backend/.env exists and contains the expected values.
- Check container status with:

```bash
docker compose ps
```

- Review logs with:

```bash
docker compose logs backend
```

- Verify the VM security rules allow inbound traffic on ports 22, 80, 443, 3000, and 8000.
- Review the provisioning log at /var/log/deployment.log on the VM.

## Destroy
To remove all Azure resources:

```bash
terraform destroy
```

## Notes
- The GitHub integration is intentionally isolated in the backend service layer.
- The application uses SQLite for local persistence.
- The integration supports pagination, rate-limit handling, retries, and structured logging.
