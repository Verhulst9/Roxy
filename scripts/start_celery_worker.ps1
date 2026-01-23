# Check if Redis is running (Optional basic check or just assume)
Write-Host "Starting Celery Worker..."

# Set Python Path to include current directory so 'tasks' module can be found
$env:PYTHONPATH = $PWD

# Run Celery Worker
# -A tasks.app: The application instance
# --loglevel=info: specific logging level
# -P solo: Pool implementation. 'solo' is recommended for Windows compatibility during dev. 
#          For production on Linux, remove '-P solo' or use 'prefork'.
# -Q high_priority,medium_priority,low_priority: Listen to all queues
python -m celery -A tasks.app worker --loglevel=info -P solo -Q high_priority,medium_priority,low_priority
