#!/bin/bash

# Web Scraping Dashboard Startup Script
# =====================================
# Optimized startup for Render.com deployment

echo "🚀 Starting Web Scraping Dashboard..."
echo "📊 Environment: ${FLASK_ENV:-production}"
echo "🔧 Port: ${PORT:-10000}"

# Ensure data directories exist
mkdir -p data
mkdir -p static/css static/js static/img
mkdir -p templates

# Start with Gunicorn
echo "🔥 Starting Gunicorn server..."
exec gunicorn --config gunicorn.conf.py app:application 