"""
Vercel Serverless Function Entry Point
=====================================

Alternative entry point optimized for Vercel's serverless architecture.

Author: Web Scraping Project
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import our main Flask app
    from flask_app import app
    
    # Configure for serverless
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
except Exception as e:
    # Fallback minimal app if import fails
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return jsonify({"error": str(e), "status": "import_failed"})

# This is what Vercel expects
if __name__ == '__main__':
    # Use a different port for testing to avoid conflicts
    app.run(host='127.0.0.1', port=8081) 