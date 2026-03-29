import json
import time
from datetime import datetime, timezone

import pika
from prometheus_client import Counter, start_http_server
from sqlalchemy.orm import Session

from src.config import settings
from src.db import SessionLocal
from src.models import Release, ReleaseStep

from prometheus_client import Counter, Histogram, start_http_server

import uuid

import os
import subprocess
from pathlib import Path

QUEUE_NAME = "release_requested"

worker_heartbeat = Counter("idp_worker_heartbeat_total", "Worker heartbeat counter")
worker_processed = Counter("idp_worker_processed_total", "Processed release events")
worker_failed = Counter("idp_worker_failed_total", "Failed release events")

release_success_total = Counter(
    "idp_release_success_total",
    "Total successful releases",
    ["service", "environment"],
)

release_failed_total = Counter(
    "idp_release_failed_total",
    "Total failed releases",
    ["service", "environment"],
)

release_step_success_total = Counter(
    "idp_release_step_success_total",
    "Total successful release steps",
    ["service", "environment", "step_name"],
)

release_step_failed_total = Counter(
    "idp_release_step_failed_total",
    "Total failed release steps",
    ["service", "environment", "step_name"],
)

release_step_duration_seconds = Histogram(
    "idp_release_step_duration_seconds",
    "Duration of release steps in seconds",
    ["service", "environment", "step_name"],
)


def log_step(release_id: str, step: str, message: str) -> None:
    print(f"[worker] [{release_id}] [{step}] {message}")

def get_or_create_step(db: Session, release_id: str, step_name: str, step_order: int) -> ReleaseStep:
    step = (
        db.query(ReleaseStep)
        .filter(ReleaseStep.release_id == release_id, ReleaseStep.step_name == step_name)
        .first()
    )
    if step:
        return step

    step = ReleaseStep(
        id=str(uuid.uuid4()),
        release_id=release_id,
        step_name=step_name,
        status="PENDING",
        step_order=step_order,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def mark_step_in_progress(db: Session, release_id: str, step_name: str, step_order: int) -> ReleaseStep:
    step = get_or_create_step(db, release_id, step_name, step_order)
    step.status = "IN_PROGRESS"
    step.started_at = datetime.now(timezone.utc)
    step.error_message = None
    db.commit()
    db.refresh(step)
    return step


def mark_step_success(db: Session, release_id: str, step_name: str, step_order: int) -> None:
    step = get_or_create_step(db, release_id, step_name, step_order)
    step.status = "SUCCESS"
    step.finished_at = datetime.now(timezone.utc)
    db.commit()


def mark_step_failed(db: Session, release_id: str, step_name: str, step_order: int, error_message: str) -> None:
    step = get_or_create_step(db, release_id, step_name, step_order)
    step.status = "FAILED"
    step.finished_at = datetime.now(timezone.utc)
    step.error_message = error_message
    db.commit()


def run_validate(db: Session, release: Release) -> None:
    step = "VALIDATE"
    step_order = 1

    mark_step_in_progress(db, release.id, step, step_order)
    log_step(release.id, step, "started")

    started = time.perf_counter()
    try:
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

        mark_step_success(db, release.id, step, step_order)

        duration = time.perf_counter() - started
        release_step_duration_seconds.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).observe(duration)

        release_step_success_total.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).inc()

        log_step(release.id, step, "finished successfully")
    except Exception:
        duration = time.perf_counter() - started
        release_step_duration_seconds.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).observe(duration)

        release_step_failed_total.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).inc()

        raise


def run_deploy(db: Session, release: Release) -> None:
    step = "DEPLOY"
    step_order = 2

    mark_step_in_progress(db, release.id, step, step_order)
    log_step(release.id, step, "started")

    started = time.perf_counter()
    try:
        target_root = Path("/opt/release-targets")
        target_dir = target_root / release.service

        if not target_dir.exists():
            raise RuntimeError(f"Target stack directory does not exist: {target_dir}")

        compose_file = target_dir / release.target_compose_path
        if not compose_file.exists():
            raise RuntimeError(f"Compose file does not exist: {compose_file}")

        env_file = target_dir / "envs" / f"{release.environment}.env"
        if not env_file.exists():
            raise RuntimeError(f"Env file does not exist: {env_file}")

        project_name = f"{release.service}-{release.environment}"

        # 1. Check compose config
        config_cmd = [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(compose_file),
            "config",
        ]

        log_step(release.id, step, f"running config check: {' '.join(config_cmd)}")

        config_result = subprocess.run(
            config_cmd,
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if config_result.stdout:
            log_step(release.id, step, f"config stdout: {config_result.stdout.strip()}")

        if config_result.stderr:
            log_step(release.id, step, f"config stderr: {config_result.stderr.strip()}")

        if config_result.returncode != 0:
            raise RuntimeError(
                f"docker compose config failed with exit code {config_result.returncode}"
            )

        # 2. Pull step
        pull_cmd = [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-p",
            project_name,
            "-f",
            str(compose_file),
            "pull",
        ]

        log_step(release.id, step, f"running pull: {' '.join(pull_cmd)}")

        pull_result = subprocess.run(
            pull_cmd,
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if pull_result.stdout:
            log_step(release.id, step, f"pull stdout: {pull_result.stdout.strip()}")

        if pull_result.stderr:
            log_step(release.id, step, f"pull stderr: {pull_result.stderr.strip()}")

        if pull_result.returncode != 0:
            raise RuntimeError(
                f"docker compose pull failed with exit code {pull_result.returncode}"
            )

        # 3. Deploy
        cmd = [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
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
            cwd=target_dir,
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

        mark_step_success(db, release.id, step, step_order)

        duration = time.perf_counter() - started
        release_step_duration_seconds.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).observe(duration)

        release_step_success_total.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).inc()

        log_step(release.id, step, "finished successfully")

    except Exception as e:
        duration = time.perf_counter() - started
        release_step_duration_seconds.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).observe(duration)

        release_step_failed_total.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).inc()

        log_step(release.id, step, f"failed: {str(e)}")
        raise

def load_env_file(env_path: Path) -> dict:
    env_vars = {}

    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip()

    return env_vars

def run_smoke_test(db: Session, release: Release) -> None:
    step = "SMOKE_TEST"
    step_order = 3

    mark_step_in_progress(db, release.id, step, step_order)
    log_step(release.id, step, "started")

    started = time.perf_counter()
    try:
        if release.service == "demo-web":
            import urllib.request

            url = "http://172.30.81.172:8088"
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status != 200:
                    raise RuntimeError(f"Smoke test failed, status={response.status}")

        elif release.service == "frontier-consult":
            import requests

            target_root = Path("/opt/release-targets")
            target_dir = target_root / release.service
            env_file = target_dir / "envs" / f"{release.environment}.env"

            if not env_file.exists():
                raise RuntimeError(f"Env file not found for smoke test: {env_file}")

            env_vars = load_env_file(env_file)

            fastapi_port = env_vars.get("FASTAPI_PORT")
            django_port = env_vars.get("DJANGO_PORT")

            if not fastapi_port or not django_port:
                raise RuntimeError("FASTAPI_PORT or DJANGO_PORT is missing in env file")

            # Time to up for services
            time.sleep(10)

            fastapi_url = f"http://localhost:{fastapi_port}/docs"
            django_url = f"http://localhost:{django_port}/admin/"

            log_step(release.id, step, f"checking FastAPI: {fastapi_url}")
            r1 = requests.get(fastapi_url, timeout=10)
            if r1.status_code != 200:
                raise RuntimeError(
                    f"FastAPI smoke test failed: {fastapi_url} -> {r1.status_code}"
                )

            log_step(release.id, step, f"checking Django: {django_url}")
            r2 = requests.get(django_url, timeout=10, allow_redirects=False)
            if r2.status_code not in (200, 302):
                raise RuntimeError(
                    f"Django smoke test failed: {django_url} -> {r2.status_code}"
                )

        else:
            time.sleep(1)

        mark_step_success(db, release.id, step, step_order)

        duration = time.perf_counter() - started
        release_step_duration_seconds.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).observe(duration)

        release_step_success_total.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).inc()

        log_step(release.id, step, "finished successfully")

    except Exception as e:
        duration = time.perf_counter() - started
        release_step_duration_seconds.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).observe(duration)

        release_step_failed_total.labels(
            service=release.service,
            environment=release.environment,
            step_name=step,
        ).inc()

        log_step(release.id, step, f"failed: {str(e)}")
        raise


def process_release_event(event: dict) -> None:
    release_id = event["release_id"]

    db: Session = SessionLocal()
    current_step_name = None
    current_step_order = None

    try:
        release = db.query(Release).filter(Release.id == release_id).first()
        if not release:
            raise RuntimeError(f"Release {release_id} not found")

        log_step(release.id, "PIPELINE", "setting status to IN_PROGRESS")
        release.status = "IN_PROGRESS"
        release.started_at = datetime.now(timezone.utc)
        db.commit()

        current_step_name = "VALIDATE"
        current_step_order = 1
        run_validate(db, release)

        current_step_name = "DEPLOY"
        current_step_order = 2
        run_deploy(db, release)

        current_step_name = "SMOKE_TEST"
        current_step_order = 3
        run_smoke_test(db, release)

        release.status = "SUCCESS"
        release.finished_at = datetime.now(timezone.utc)
        db.commit()

        release_success_total.labels(
            service=release.service,
            environment=release.environment,
        ).inc()

        log_step(release.id, "PIPELINE", "completed with SUCCESS")
        worker_processed.inc()

    except Exception as exc:
        worker_failed.inc()

        if current_step_name is not None and current_step_order is not None:
            mark_step_failed(db, release_id, current_step_name, current_step_order, str(exc))

        release = db.query(Release).filter(Release.id == release_id).first()
        if release:
            release.status = "FAILED"
            release.error_message = str(exc)
            release.finished_at = datetime.now(timezone.utc)
            db.commit()

            if release:
                release_failed_total.labels(
                    service=release.service,
                    environment=release.environment,
                ).inc()

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