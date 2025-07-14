"""
Gunicorn Configuration for Web Scraping Dashboard
===============================================

Optimized settings for production deployment on Render.com
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
backlog = 2048

# Worker processes
workers = min(4, multiprocessing.cpu_count() * 2 + 1)  # Cap at 4 workers for memory efficiency
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Increased timeout for data collection operations
keepalive = 60

# Memory management
max_requests = 1000
max_requests_jitter = 50
preload_app = True  # Load application code before forking workers

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "web-scraping-dashboard"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Application
wsgi_module = "app:application"

# Development vs Production
if os.getenv('FLASK_ENV') == 'development':
    reload = True
    workers = 1
    loglevel = "debug"
else:
    reload = False
    
print(f"🚀 Gunicorn starting with {workers} workers on {bind}")
print(f"📊 Worker class: {worker_class}, Timeout: {timeout}s")
print(f"🔧 Environment: {os.getenv('FLASK_ENV', 'production')}") 