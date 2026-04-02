# Architecture

## Overview

The system is built as a distributed, event-driven architecture.

It separates responsibilities between API, messaging, processing, and deployment layers.

---

## Components

### 1. Release API (FastAPI)

- Entry point for release requests
- Validates input
- Stores release data in PostgreSQL
- Publishes events to RabbitMQ

---

### 2. RabbitMQ

- Message broker
- Enables asynchronous communication
- Decouples API from worker

---

### 3. Worker Service

- Consumes events from RabbitMQ
- Executes deployment pipeline:
  - VALIDATE
  - DEPLOY
  - SMOKE_TEST
- Updates release status in database

---

### 4. PostgreSQL

- Stores:
  - releases
  - release_steps
- Provides persistence and history tracking

---

### 5. Monitoring (Prometheus + Grafana)

- Tracks:
  - step duration
  - success/failure metrics
- Provides basic analytics

---

### 6. Target Services

- Applications deployed by the IDP
- Managed via Docker Compose
- Example: frontier-consult

---

## Event-Driven Flow

1. Client or CI/CD sends request → API
2. API saves release → PostgreSQL
3. API publishes event → RabbitMQ
4. Worker consumes event
5. Worker executes:
   - validation
   - deployment
   - smoke test
6. Worker updates status in DB
7. Metrics are collected

---

## Deployment Architecture (Runtime)

All services run as Docker containers on a cloud VM.

### Containers:

- release-api
- worker
- rabbitmq
- postgres
- prometheus
- grafana
- deployed services

---

## Networking

- All containers are connected to a shared Docker network
- Communication via service names (Docker DNS):
  - rabbitmq
  - postgres
- Internal ports:
  - RabbitMQ → 5672
  - PostgreSQL → 5432
- External ports:
  - API → 8000
  - Grafana → 3000

---

## Design Principles

- Loose coupling via message broker
- Asynchronous processing
- Separation of concerns
- Observability (metrics + logs)
- Scalability (worker can be scaled horizontally)

---

## Why Event-Driven Architecture

- Non-blocking API
- Better scalability
- Clear separation between components
- Easier to extend (retry, DLQ, etc.)

---

## Key Idea

The system acts as a **deployment orchestrator platform**.

CI/CD pipelines do not deploy services directly — they trigger the IDP, which manages deployment asynchronously.
