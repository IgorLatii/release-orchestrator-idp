# Runbooks

## Overview

This document contains basic operational procedures for running, restarting, and troubleshooting the Release Orchestrator IDP.

It is intended for demo, maintenance, and incident handling.

---

## 1. Start the Platform

To start the platform locally or on the server:

```bash
docker compose up -d
```

To verify running containers:

```bash
docker ps
```

---

## 2. Stop the Platform

To stop all services:

```bash
docker compose down
```

---

## 3. Restart a Service

Restart a specific container:

```bash
docker restart <container_name>
```

Examples:

```bash
docker restart release-api
docker restart worker
docker restart rabbitmq
docker restart postgres
```

If using Docker Compose service names:

```bash
docker compose restart worker
docker compose restart release-api
```

---

## 4. Check Logs

To inspect service logs:

```bash
docker logs <container_name>
```

Follow logs in real time:

```bash
docker logs -f <container_name>
```

Examples:

```bash
docker logs -f worker
docker logs -f release-api
docker logs -f rabbitmq
```

---

## 5. Common Troubleshooting

### Problem: Release stays in PENDING

Possible causes:
- worker is not running
- RabbitMQ is unavailable
- event was not published

Checks:
```bash
docker ps
docker logs -f worker
docker logs -f rabbitmq
```

---

### Problem: Release becomes FAILED

Possible causes:
- invalid target path
- missing env file
- docker compose error
- smoke test failed

Checks:
```bash
docker logs -f worker
docker compose config
ls -la /opt/release-targets/<service>/
```

---

### Problem: API is not reachable

Checks:
```bash
docker ps
docker logs -f release-api
ss -lntp | grep 8000
curl http://localhost:8000/docs
```

---

### Problem: RabbitMQ communication issues

Checks:
```bash
docker logs -f rabbitmq
docker exec -it rabbitmq rabbitmqctl status
```

---

### Problem: PostgreSQL connection issues

Checks:
```bash
docker logs -f postgres
docker exec -it postgres psql -U <user> -d <database>
```

---

## 6. Deployment Troubleshooting

If deployment does not start or complete:

1. Check worker logs
2. Verify target directory exists
3. Verify env file exists
4. Verify compose file path is correct
5. Run compose manually for testing

Example:

```bash
docker compose   --env-file /opt/release-targets/<service>/envs/<env>.env   -p <service>-<environment>   -f /opt/release-targets/<service>/docker-compose.yml   up -d
```

---

## 7. API Verification

To test the API manually:

```bash
curl -X POST http://localhost:8000/releases \
  -H "Content-Type: application/json" \
  -d '{
    "service": "frontier-consult",
    "version": "latest",
    "environment": "dev"
  }'
```

Check Swagger:

```bash
http://localhost:8000/docs
```

---

## 8. Monitoring Verification

Prometheus and Grafana can be used to validate system activity.

### Check Grafana
```bash
http://<IDP_HOST>:3000
```

### What to verify
- step duration
- success/failure counters
- deployment activity

---

## 9. Useful Debug Commands

```bash
docker ps
docker compose ps
docker compose config
docker logs -f worker
docker logs -f release-api
docker logs -f rabbitmq
docker logs -f postgres
```

For network checks:

```bash
docker network ls
docker inspect <container_name>
```

---

## 10. Operational Notes

- API accepts release requests
- RabbitMQ transports deployment events
- Worker performs deployment logic
- PostgreSQL stores release history
- Monitoring stack provides visibility

---

## Key Idea

These runbooks provide a simple operational guide for:
- starting the platform
- restarting services
- checking logs
- troubleshooting deployment issues

They improve reproducibility and operational readiness of the project.
