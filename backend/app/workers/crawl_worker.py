from rq import SimpleWorker

from app.queue.crawl_queue import crawl_queue


if __name__ == "__main__":
    worker = SimpleWorker(
        [crawl_queue],
    )

    worker.work()