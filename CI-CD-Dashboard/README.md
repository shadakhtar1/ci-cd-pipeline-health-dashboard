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
4. Copy .env.example to .env and update the values.
5. Run the application with uvicorn.

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

## Notes
- The GitHub integration is intentionally isolated in the backend service layer.
- The application uses SQLite for local persistence.
- The integration supports pagination, rate-limit handling, retries, and structured logging.
