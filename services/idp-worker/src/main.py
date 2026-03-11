import json
import time
from datetime import datetime, timezone

import pika
from prometheus_client import Counter, start_http_server
from sqlalchemy.orm import Session

from src.config import settings
from src.db import SessionLocal
from src.models import Release

QUEUE_NAME = "release_requested"

worker_heartbeat = Counter("idp_worker_heartbeat_total", "Worker heartbeat counter")
worker_processed = Counter("idp_worker_processed_total", "Processed release events")
worker_failed = Counter("idp_worker_failed_total", "Failed release events")


def process_release_event(event: dict) -> None:
    release_id = event["release_id"]

    db: Session = SessionLocal()
    try:
        release = db.query(Release).filter(Release.id == release_id).first()
        if not release:
            raise RuntimeError(f"Release {release_id} not found")

        release.status = "IN_PROGRESS"
        release.started_at = datetime.now(timezone.utc)
        db.commit()

        # Пока fake processing
        time.sleep(3)

        release.status = "SUCCESS"
        release.finished_at = datetime.now(timezone.utc)
        db.commit()

        worker_processed.inc()

    except Exception as exc:
        worker_failed.inc()

        release = db.query(Release).filter(Release.id == release_id).first()
        if release:
            release.status = "FAILED"
            release.error_message = str(exc)
            release.finished_at = datetime.now(timezone.utc)
            db.commit()

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