# Requirement Analysis Document

## 1. Problem Statement
The CI/CD Pipeline Health Dashboard is needed to provide a centralized view of GitHub Actions or Jenkins pipeline runs. Teams need a reliable way to monitor the health of builds, investigate failures quickly, review recent commits, and receive alerts when a pipeline fails.

## 2. Objectives
- Collect pipeline execution data from GitHub Actions API.
- Store build history in a structured database.
- Expose dashboard metrics such as success rate, failure rate, average build time, and recent builds.
- Provide build logs and failure context.
- Send email alerts for failed pipelines.
- Deliver the solution as a containerized web application.

## 3. Functional Requirements
### Data Collection
- Retrieve workflow run information from GitHub Actions API.
- Capture the following fields for each build:
  - build number
  - pipeline name
  - workflow name
  - status
  - duration
  - branch
  - commit ID
  - commit message
  - author
  - started time
  - completed time
  - logs

### Dashboard
- Provide summary cards for key metrics.
- Display recent builds and build history.
- Show logs for a specific build.
- Display pipeline status and overall health.

### Alerts
- Send email notifications when a pipeline execution fails.
- Include pipeline name, build number, branch, duration, failure status, and logs link.

### API
- Expose REST endpoints for dashboard summaries, builds, build detail, logs, refresh, and health.

## 4. Non-functional Requirements
- Use Python 3.12, FastAPI, SQLAlchemy, SQLite, React, Bootstrap, and Docker.
- Follow clean architecture, SOLID principles, and PEP8.
- Use environment variables for configuration and secrets.
- Handle API failures gracefully.
- Provide logging and structured error handling.
- Support containerized deployment with Docker Compose.

## 5. Stakeholders
- DevOps engineers
- Software developers
- Engineering managers
- Support and operations teams

## 6. Assumptions
- GitHub Actions is the primary CI source.
- A GitHub personal access token is available through environment configuration.
- The application will run in a local development environment first, then in Docker.
- Email SMTP credentials will be configured via environment variables.

## 7. Risks
- GitHub API rate limits may affect data refresh frequency.
- Network issues may cause incomplete data retrieval.
- SMTP configuration errors could block alert delivery.
- Incomplete workflow metadata may reduce data quality.

## 8. Technology Choices
- Backend: FastAPI, SQLAlchemy, Pydantic, SQLite, Requests
- Frontend: React, Axios, Bootstrap, Chart.js, React Router
- Deployment: Docker and Docker Compose
- Source control: GitHub

## 9. API Analysis
The backend will expose the following API routes:
- GET /api/dashboard
- GET /api/builds
- GET /api/builds/{id}
- GET /api/builds/{id}/logs
- POST /api/refresh
- GET /health

These endpoints should return well-structured JSON and clear error responses.

## 10. Database Analysis
A normalized SQLite schema will include a primary Builds table with the required fields. Additional tables may be introduced later for repositories, workflows, or alert preferences if the scope expands.

## 11. UI Analysis
The frontend will include:
- summary cards for key metrics
- pie and bar charts for build status trends
- a recent builds table
- a logs viewer for selected builds
- responsive layout for desktop and mobile screens
