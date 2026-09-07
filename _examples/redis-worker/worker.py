import json
import os
import signal
import threading
import redis

PENDING = "docs:jobs:pending"
PROCESSING = "docs:jobs:processing"

def run():
    stopping = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopping.set())
    client = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True, socket_connect_timeout=5)
    client.ping()
    # One worker only: recover work interrupted before acknowledgement.
    while client.rpoplpush(PROCESSING, PENDING) is not None:
        pass
    print("Queue worker ready", flush=True)
    while not stopping.is_set():
        try:
            raw = client.brpoplpush(PENDING, PROCESSING, timeout=5)
            if raw is None:
                continue
            job = json.loads(raw)
            key = "docs:result:" + job["id"]
            result = json.dumps({"id": job["id"], "result": job["value"].upper()})
            # SET and acknowledgement commit together. Repeated IDs are safe for this demo.
            with client.pipeline(transaction=True) as transaction:
                transaction.set(key, result)
                transaction.lrem(PROCESSING, 1, raw)
                transaction.execute()
            print("Processed " + job["id"], flush=True)
        except redis.RedisError:
            print("Redis request failed; retrying", flush=True)
            stopping.wait(5)
    client.close()
    print("Queue worker stopped", flush=True)

if __name__ == "__main__":
    run()
