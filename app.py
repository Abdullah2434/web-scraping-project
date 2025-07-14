"""
Main Flask Application Entry Point for Production Deployment
==========================================================

WSGI application entry point optimized for Gunicorn deployment.
Configured for deployment on Render with automatic data collection.

Author: Web Scraping Project
"""

import os
import logging
import threading
import atexit
from flask import Flask

# Set up logging for production with safe encoding
if os.getenv('FLASK_ENV') == 'production':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application for WSGI"""
    
    # Import the main Flask app
    from flask_app import app
    
    # Configure for production deployment
    if os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER'):
        logger.info("Configuring app for production deployment with Gunicorn...")
        
        # Configure for production
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Get port from environment
        port = int(os.getenv('PORT', 10000))
        logger.info(f"App configured for production on port {port}")
        
        # Start background scheduler once per application (not per worker)
        def start_background_scheduler():
            """Start the automated data collection in background"""
            try:
                from scheduler import start_scheduler
                logger.info("Starting automated data collection scheduler...")
                start_scheduler()
                logger.info("Background scheduler started successfully")
                
                # Register cleanup handler
                def cleanup_scheduler():
                    try:
                        from scheduler import stop_scheduler
                        stop_scheduler()
                        logger.info("Scheduler stopped on application shutdown")
                    except Exception as e:
                        logger.error(f"Error stopping scheduler: {e}")
                
                atexit.register(cleanup_scheduler)
                
            except Exception as e:
                logger.error(f"Failed to start background scheduler: {e}")
        
        # Only start scheduler in the main worker process (avoid duplicates)
        if not hasattr(app, '_scheduler_started'):
            scheduler_thread = threading.Thread(target=start_background_scheduler, daemon=True)
            scheduler_thread.start()
            app._scheduler_started = True
        
    else:
        logger.info("Configuring app for local development...")
    
    return app

# Create the WSGI application instance
app = create_app()

# WSGI callable for Gunicorn
application = app

if __name__ == '__main__':
    # This should only be used for local development
    logger.warning("Running with Flask development server. Use Gunicorn for production!")
    port = int(os.getenv('PORT', 8080))
    app.run(host='127.0.0.1', port=port, debug=True) 