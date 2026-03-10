from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Release Orchestrator IDP API")

health_counter = Counter("idp_api_health_requests_total", "Total health requests")

@app.get("/health")
def health():
    health_counter.inc()
    return {"status": "ok", "service": "idp-api"}

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)