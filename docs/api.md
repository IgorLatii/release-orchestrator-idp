# API Documentation

## Overview

The Release Orchestrator exposes a REST API used to trigger and monitor deployments.

The API is implemented using FastAPI and provides automatic Swagger/OpenAPI documentation.

---

## Base URL

http://<IDP_HOST>:8000

---

## Authentication

For demo purposes, the API can be used without authentication or with a simple token-based mechanism (depending on configuration).

---

## Endpoints

---

### 1. Create Release

Trigger a new deployment.

Endpoint:  
POST /releases

Request Body:

{
  "service": "frontier-consult",
  "version": "1.0.0",
  "environment": "dev",
  "target": {
    "repo": "local",
    "ref": "main",
    "composePath": "docker-compose.yml"
  }
}

Description:
- Registers a new release
- Publishes an event to RabbitMQ
- Triggers asynchronous deployment

Response:

{
  "id": 1,
  "status": "PENDING"
}

---

### 2. Get Release by ID

Retrieve release details and status.

Endpoint:  
GET /releases/{id}

Response:

{
  "id": 1,
  "service": "frontier-consult",
  "version": "1.0.0",
  "environment": "dev",
  "status": "SUCCESS",
  "created_at": "2026-01-01T12:00:00"
}

---

### 3. List Releases

Get all releases.

Endpoint:  
GET /releases

Response:

[
  {
    "id": 1,
    "service": "frontier-consult",
    "status": "SUCCESS"
  },
  {
    "id": 2,
    "service": "frontier-consult",
    "status": "FAILED"
  }
]

---

### 4. Get Release Steps

Retrieve execution steps for a release.

Endpoint:  
GET /releases/{id}/steps

Response:

[
  {
    "step": "VALIDATE",
    "status": "SUCCESS"
  },
  {
    "step": "DEPLOY",
    "status": "SUCCESS"
  },
  {
    "step": "SMOKE_TEST",
    "status": "SUCCESS"
  }
]

---

## Release Lifecycle

Each release goes through the following states:

- PENDING – created, waiting for processing  
- IN_PROGRESS – being processed by worker  
- SUCCESS – deployment completed successfully  
- FAILED – error occurred during deployment  

---

## How API Works Internally

1. Client sends request to /releases  
2. API validates input  
3. Saves release in PostgreSQL  
4. Sends event to RabbitMQ  
5. Worker processes the event  
6. Updates status in database  

---

## Swagger Documentation

Interactive API documentation is available at:

http://<IDP_HOST>:8000/docs

This allows:
- testing endpoints  
- viewing request/response models  
- validating API behavior  

---

## Example (CI/CD Integration)

curl -X POST http://<IDP_HOST>:8000/releases \
  -H "Content-Type: application/json" \
  -d '{
    "service": "frontier-consult",
    "version": "latest",
    "environment": "dev"
  }'

---
