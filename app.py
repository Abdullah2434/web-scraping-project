"""
Flask Application Entry Point for Vercel Deployment
==================================================

Serverless-compatible entry point for Vercel deployment.
Background processes disabled - use external cron for scheduling.

Author: Web Scraping Project
"""

import os
import logging
from flask import Flask

# Set up logging for Vercel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application for Vercel"""
    
    # Import the main Flask app
    from flask_app import app
    
    # Configure for Vercel serverless deployment
    logger.info("Configuring app for Vercel serverless deployment...")
    
    # Configure for production
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    # Disable background scheduler for serverless
    # (Use external cron services like GitHub Actions or Vercel Cron)
    logger.info("Serverless mode: Background scheduler disabled")
    logger.info("Use external cron service for automated data collection")
    
    return app

# Create the app instance for Vercel
app = create_app()

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, lambda *args: None)

# For local development
if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting development server on port {port}")
    app.run(host='127.0.0.1', port=port, debug=True) 