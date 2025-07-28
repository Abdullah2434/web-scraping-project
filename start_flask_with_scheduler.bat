@echo off
echo 🚀 Starting Flask App with Auto-Scheduler
echo.
echo This will start the Flask dashboard AND the automated Upwork scraper
echo The scraper will run every 2 hours automatically
echo.
echo 🌐 Dashboard: http://localhost:8080
echo 📋 Keywords: keywords.txt file
echo ⏰ Interval: 2 hours
echo.
echo Press Ctrl+C to stop everything
echo.
python flask_app.py
pause 