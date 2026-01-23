from celery import Celery
from .config import CeleryConfig

# Initialize Celery app
# The name 'tasks' corresponds to the package name
app = Celery("nakari_tasks")

# Load configuration from config object
app.config_from_object(CeleryConfig)

# Auto-discover tasks
# We manually specify the modules to ensure they are loaded when the worker starts
app.conf.imports = (
    'tasks.general',
    'tasks.interaction',
    'tasks.reflection',
)

if __name__ == "__main__":
    app.start()
