import time
from prometheus_client import start_http_server, Counter

worker_heartbeat = Counter("idp_worker_heartbeat_total", "Worker heartbeat counter")

def main():
    start_http_server(8001)
    print("Worker started. Metrics on :8001/metrics")

    while True:
        worker_heartbeat.inc()
        print("Worker heartbeat...")
        time.sleep(10)

if __name__ == "__main__":
    main()