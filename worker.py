from rq import Worker, Queue, Connection
import redis
from app.core.settings import settings

listen = ['default']

# ---------- Redis Connection ----------
conn = redis.from_url(settings.REDIS_URL)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work(with_scheduler=True)