import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "27723")
CELERY_BROKER_DB = int(os.environ.get("CELERY_BROKER_DB", 0))
CELERY_BACKEND_DB = int(os.environ.get("CELERY_BACKEND_DB", 1))


celery_app = Celery(
    "agentiq_tasks",
    # Redis broker URL
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/{CELERY_BROKER_DB}",
    # Redis backend URL (optional)
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/{CELERY_BACKEND_DB}",
    broker_connection_retry_on_startup=True,
)

# Ensure unique queue name
celery_app.conf.task_default_queue = 'agentiq_tasks_queue'

# Optional: Prefix task results with a namespace
celery_app.conf.redis_backend_health_check_interval = 30
celery_app.conf.result_backend_transport_options = {
    'prefix': 'agentiq_tasks_results:',
    'visibility_timeout': 3600
}


# Function to import tasks after app initialization
def register_tasks():
    import src.tasks


register_tasks()