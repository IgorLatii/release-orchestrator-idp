# Release Orchestrator IDP

## Overview

Release Orchestrator IDP is a mini Internal Developer Platform designed to automate service deployment using an event-driven architecture.

Instead of deploying services directly from CI/CD, the pipeline delegates deployment to the IDP, which orchestrates the process asynchronously.

---

## Key Idea

CI/CD builds and pushes the application → IDP handles the deployment.

This approach provides:
- better control over releases
- decoupling between build and deploy
- observability of the deployment process

---

## Architecture Overview

The system is composed of multiple distributed services:

- **Release API (FastAPI)** – entry point for release requests
- **RabbitMQ** – message broker for async communication
- **Worker (Python)** – processes release events
- **PostgreSQL** – stores releases and steps
- **Prometheus + Grafana** – monitoring and metrics
- **Target services** – deployed via Docker Compose

---

## Event-Driven Flow

1. CI/CD triggers a release via API
2. Release is saved in PostgreSQL
3. Event is published to RabbitMQ
4. Worker consumes the event
5. Worker executes:
   - VALIDATE
   - DEPLOY (docker compose)
   - SMOKE_TEST
6. Status is updated in DB
7. Metrics are collected

---

## Deployment Architecture (Runtime)

The system is deployed on a cloud VM (Azure) using Docker Compose.

### Running containers:
- release-api
- worker
- rabbitmq
- postgres
- prometheus
- grafana
- deployed services (e.g. frontier-consult)

### Networking:
- internal Docker network
- communication via service names:
  - rabbitmq
  - postgres
- minimal exposed ports:
  - API → 8000
  - Grafana → 3000

---

## CI/CD Pipeline

Each service uses GitHub Actions.

### CI Stage:
- install dependencies
- build application
- run tests

### CD Stage:
- build Docker image
- push to GHCR
- trigger deployment via IDP

Example:

```bash
curl -X POST http://<IDP_HOST>:8000/releases \
  -H "Content-Type: application/json" \
  -d '{
    "service": "frontier-consult",
    "version": "latest",
    "environment": "dev"
  }'
```

## Deployment Logic

The deployment is executed by the Worker:

```
docker compose \
  --env-file /opt/release-targets/<service>/envs/<env>.env \
  -p <service>-<environment> \
  -f /opt/release-targets/<service>/docker-compose.yml \
  up -d
```

### The IDP acts as a deployment orchestrator, not just an API.

### Automation Scripts
#### bootstrap_vm.sh

Used to prepare the server:

- installs Docker and Docker Compose
- creates deploy user
- prepares directories:
  - /opt/release-orchestrator-idp
  - /opt/release-targets

Purpose:

- reproducible environment setup
- minimal manual configuration

#### deploy.ps1

Used from local machine:

- copies project files via SCP
- connects via SSH
- runs deployment commands

Purpose:

- simplifies deployment
- avoids manual SSH work 

### How to Run Locally
```
docker compose up -d
```
## Technologies
- FastAPI (Python)
- RabbitMQ
- PostgreSQL
- Docker & Docker Compose
- Prometheus & Grafana
- GitHub Actions (CI/CD)

## Key Features
- Event-driven deployment
- Asynchronous processing
- CI/CD integration
- Cloud deployment
- Monitoring and metrics
- Deployment automation
