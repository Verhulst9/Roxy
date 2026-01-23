from .app import app
import time

@app.task(queue="high_priority")
def ping():
    """Basic health check task."""
    return "pong"

@app.task(queue="medium_priority")
def echo(message: str):
    """Echo the message back."""
    return f"Echo: {message}"
