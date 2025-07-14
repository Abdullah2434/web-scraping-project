"""
Main Flask Application Entry Point for Render Deployment
=======================================================

This is the main entry point for the Flask web scraping dashboard.
Configured for deployment on Render with automatic data collection.

Author: Web Scraping Project
"""

import os
import logging
import threading
import time
from flask import Flask

# Set up logging for production
if os.getenv('FLASK_ENV') == 'production':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
                else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    
    # Import the main Flask app
    from flask_app import app
    
    # Configure for Render deployment
    if os.getenv('RENDER') or os.getenv('FLASK_ENV') == 'production':
        logger.info("🚀 Configuring app for Render deployment...")
        
        # Configure for production
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Use environment port or default to 10000
        port = int(os.getenv('PORT', 10000))
        
        logger.info(f"✅ App configured for production on port {port}")
        
        # Start background scheduler for data collection
        def start_background_scheduler():
            """Start the automated data collection in background"""
            try:
                # Import scheduler functions
                from scheduler import start_scheduler
                logger.info("🔄 Starting automated data collection scheduler...")
                start_scheduler()
                logger.info("✅ Background scheduler started successfully")
            except Exception as e:
                logger.error(f"❌ Failed to start background scheduler: {e}")
        
        # Start scheduler in a separate thread
        scheduler_thread = threading.Thread(target=start_background_scheduler, daemon=True)
        scheduler_thread.start()
        
    else:
        logger.info("📱 Configuring app for local development...")
    
    return app

def main():
    """Main function for running the application"""
    app = create_app()
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 10000))
    
    if os.getenv('FLASK_ENV') == 'production':
        logger.info(f"🚀 Starting production server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.info(f"🔧 Starting development server on port {port}")
        app.run(host='127.0.0.1', port=port, debug=True)

if __name__ == '__main__':
    main() 