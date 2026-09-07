import json
import os
import sys
import time
import redis
from worker import PENDING

client = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
action, job_id = sys.argv[1:3]
if action == "enqueue":
    client.lpush(PENDING, json.dumps({"id": job_id, "value": "hello"}))
    print(json.dumps({"queued": job_id}))
elif action == "result":
    for attempt in range(30):
        result = client.get("docs:result:" + job_id)
        if result:
            print(result)
            break
        time.sleep(1)
    else:
        raise SystemExit("No result after 30 seconds")
else:
    raise SystemExit("Use enqueue or result")
client.close()
