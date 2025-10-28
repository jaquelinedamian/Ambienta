# Gunicorn configuration file for Ambienta
# Save as gunicorn_config.py

# Worker configuration
workers = 2  # Reduced number of workers
threads = 4  # Number of threads per worker
worker_class = 'gthread'  # Thread-based worker
worker_connections = 1000

# Timeouts
timeout = 120  # Increased timeout for ML operations
graceful_timeout = 30
keepalive = 5

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Server socket
bind = '0.0.0.0:$PORT'
backlog = 2048

# SSL configuration
keyfile = None
certfile = None

# Process naming
proc_name = 'ambienta_gunicorn'

# Server hooks
def on_starting(server):
    server.log.info('Starting Ambienta server with optimized settings')