# Gunicorn configuration file
import multiprocessing

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Number of threads per worker
threads = 2

# Maximum requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Timeout for requests (in seconds)
timeout = 120

# Access log - writes to stdout by default
accesslog = '-'

# Error log - writes to stderr by default
errorlog = '-'

# Log level
loglevel = 'info'

# Preload the application before forking workers
preload_app = True

# Bind to this address and port
bind = '0.0.0.0:8000'