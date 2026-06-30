from rq import Worker

from app.workers.queue import get_redis_connection, settings


def main() -> None:
    worker = Worker(
        [settings.ingestion_queue_name],
        connection=get_redis_connection(),
    )
    worker.work()


if __name__ == "__main__":
    main()
