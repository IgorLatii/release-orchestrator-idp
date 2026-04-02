# End-to-End Demo

## Overview

This document describes the main end-to-end scenario of the system.

It demonstrates how a release is triggered, processed asynchronously, and deployed using the IDP.

---

## Goal

Show a complete flow:

CI/CD → API → RabbitMQ → Worker → Deployment → Result

---

## Step-by-Step Flow

### Step 1 — Trigger Release (CI/CD or Manual)

A release is triggered via API:

curl -X POST http://<IDP_HOST>:8000/releases \
  -H "Content-Type: application/json" \
  -d '{
    "service": "frontier-consult",
    "version": "latest",
    "environment": "dev"
  }'

Expected result:
- Release created
- Status = PENDING

---

### Step 2 — Event Published

The API:
- saves release in PostgreSQL
- publishes event to RabbitMQ

---

### Step 3 — Worker Consumes Event

Worker:
- receives event from RabbitMQ
- updates status → IN_PROGRESS

---

### Step 4 — Deployment Execution

Worker executes:

1. VALIDATE
   - checks configuration
   - verifies target directory

2. DEPLOY
   - runs docker compose
   - starts containers

3. SMOKE_TEST
   - checks service availability (HTTP 200)

---

### Step 5 — Status Update

After execution:
- SUCCESS → if all steps pass
- FAILED → if any step fails

---

### Step 6 — Verify Deployment

Check running containers:

docker ps

Check service endpoint:

curl http://<SERVICE_HOST>

---

### Step 7 — Check Release via API

GET /releases/{id}

Expected:
- status = SUCCESS

---

### Step 8 — Check Metrics

Open Grafana:

http://<IDP_HOST>:3000

Metrics:
- step duration
- success/failure count

---

## What This Demo Shows

- Event-driven processing
- Message broker usage (RabbitMQ)
- Asynchronous workflow
- Automated deployment
- Observability (metrics + logs)

---

## Demo Tips (for Presentation)

For a fast demo:

1. Trigger release
2. Show worker logs
3. Show docker ps
4. Show API status

If time is limited:
- skip metrics
- focus on deployment result

---

## Key Idea

The system demonstrates a full event-driven deployment pipeline:

Request → Event → Processing → Deployment → Result

This satisfies the main requirement of an end-to-end asynchronous workflow.
