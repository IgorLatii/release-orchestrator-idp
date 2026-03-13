import json
import time
from datetime import datetime, timezone

import pika
from prometheus_client import Counter, start_http_server
from sqlalchemy.orm import Session

from src.config import settings
from src.db import SessionLocal
from src.models import Release

import os
import subprocess
from pathlib import Path

QUEUE_NAME = "release_requested"

worker_heartbeat = Counter("idp_worker_heartbeat_total", "Worker heartbeat counter")
worker_processed = Counter("idp_worker_processed_total", "Processed release events")
worker_failed = Counter("idp_worker_failed_total", "Failed release events")


def log_step(release_id: str, step: str, message: str) -> None:
    print(f"[worker] [{release_id}] [{step}] {message}")


def run_validate(release: Release) -> None:
    step = "VALIDATE"
    log_step(release.id, step, "started")

    if not release.service:
        raise RuntimeError("Release service is empty")
    if not release.version:
        raise RuntimeError("Release version is empty")
    if not release.environment:
        raise RuntimeError("Release environment is empty")
    if not release.target_repo:
        raise RuntimeError("Release target_repo is empty")
    if not release.target_ref:
        raise RuntimeError("Release target_ref is empty")
    if not release.target_compose_path:
        raise RuntimeError("Release target_compose_path is empty")

    if release.environment not in ("dev", "stage", "prod"):
        raise RuntimeError(f"Unsupported environment: {release.environment}")

    log_step(release.id, step, "finished successfully")


def run_deploy(release: Release) -> None:
    step = "DEPLOY"
    log_step(release.id, step, "started")

    target_root = Path("/opt/release-targets")
    target_dir = target_root / release.service

    if not target_dir.exists():
        raise RuntimeError(f"Target stack directory does not exist: {target_dir}")

    compose_file = target_dir / release.target_compose_path
    if not compose_file.exists():
        raise RuntimeError(f"Compose file does not exist: {compose_file}")

    project_name = f"{release.service}-{release.environment}"

    cmd = [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "up",
        "-d",
    ]

    log_step(release.id, step, f"running command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        log_step(release.id, step, f"stdout: {result.stdout.strip()}")

    if result.stderr:
        log_step(release.id, step, f"stderr: {result.stderr.strip()}")

    if result.returncode != 0:
        raise RuntimeError(f"docker compose failed with exit code {result.returncode}")

    log_step(release.id, step, "finished successfully")


def run_smoke_test(release: Release) -> None:
    step = "SMOKE_TEST"
    log_step(release.id, step, "started")

    if release.service == "demo-web":
        import urllib.request

        url = "http://172.30.81.172:8088"
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status != 200:
                raise RuntimeError(f"Smoke test failed, status={response.status}")

    else:
        time.sleep(1)

    log_step(release.id, step, "finished successfully")


def process_release_event(event: dict) -> None:
    release_id = event["release_id"]

    db: Session = SessionLocal()
    try:
        release = db.query(Release).filter(Release.id == release_id).first()
        if not release:
            raise RuntimeError(f"Release {release_id} not found")

        log_step(release.id, "PIPELINE", "setting status to IN_PROGRESS")
        release.status = "IN_PROGRESS"
        release.started_at = datetime.now(timezone.utc)
        db.commit()

        run_validate(release)
        run_deploy(release)
        run_smoke_test(release)

        release.status = "SUCCESS"
        release.finished_at = datetime.now(timezone.utc)
        db.commit()

        log_step(release.id, "PIPELINE", "completed with SUCCESS")
        worker_processed.inc()

    except Exception as exc:
        worker_failed.inc()

        release = db.query(Release).filter(Release.id == release_id).first()
        if release:
            release.status = "FAILED"
            release.error_message = str(exc)
            release.finished_at = datetime.now(timezone.utc)
            db.commit()

        log_step(release_id, "PIPELINE", f"failed: {exc}")
        raise
    finally:
        db.close()


def callback(ch, method, properties, body):
    event = json.loads(body.decode("utf-8"))
    print(f"[worker] Received event: {event}")

    try:
        process_release_event(event)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[worker] Processed release {event['release_id']}")
    except Exception as exc:
        print(f"[worker] Failed: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    start_http_server(8001)
    print("Worker started. Metrics on :8001/metrics")

    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(f"[worker] Waiting for messages in queue: {QUEUE_NAME}")
    channel.start_consuming()


if __name__ == "__main__":
    main()