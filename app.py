"""
Main Flask Application Entry Point for Render Deployment
=======================================================

This is the main entry point for the Flask web scraping dashboard.
Configured for deployment on Render with automatic data collection.

Author: Web Scraping Project
"""

import os
import logging
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
        
        # Import and setup Render scheduler
        from render_scheduler_solution import setup_render_deployment
        setup_render_deployment(app)
        
        # Configure for production
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Use environment port or default to 10000
        port = int(os.getenv('PORT', 10000))
        
        logger.info(f"✅ App configured for production on port {port}")
    
        else:
        logger.info("📱 Configuring app for local development...")
        port = 8080
    
    return app, port

def main():
    """Main entry point"""
    try:
        app, port = create_app()
        
        # Start the application
        if os.getenv('FLASK_ENV') == 'production':
            # Production on Render
            logger.info(f"🌐 Starting production server on port {port}")
            app.run(host='0.0.0.0', port=port, debug=False)
        else:
            # Local development
            logger.info(f"🔧 Starting development server on port {port}")
            app.run(host='127.0.0.1', port=port, debug=True)
            
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise

if __name__ == '__main__':
    main() 