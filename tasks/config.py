import os

class CeleryConfig:
    # Broker and Backend
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    # Task serialization
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]

    # Timezone
    timezone = "Asia/Shanghai"  # Or UTC, depending on preference. Using Asia/Shanghai for likely user context based on Chinese readme.
    enable_utc = True

    # Task Routing (Queues)
    task_default_queue = "medium_priority"
    task_queues = {
        "high_priority": {"exchange": "high_priority", "routing_key": "high.#"},
        "medium_priority": {"exchange": "medium_priority", "routing_key": "medium.#"},
        "low_priority": {"exchange": "low_priority", "routing_key": "low.#"},
    }
    
    # Task routing implementation
    # When defining tasks, we can specify queue='high_priority'

    # Optimization
    broker_transport_options = {'visibility_timeout': 3600}  # 1 hour
    worker_concurrency = os.getenv("CELERY_WORKER_CONCURRENCY", 4)
    worker_prefetch_multiplier = 1  # For long running tasks preventing starvation
