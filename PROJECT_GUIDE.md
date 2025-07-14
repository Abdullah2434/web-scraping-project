# Web Scraping Dashboard - Complete Project Guide

## 📊 Project Overview

A comprehensive Flask-based web dashboard for analyzing keyword trends across multiple social media platforms and search engines. The system collects, analyzes, and visualizes trending keyword data from:

- **Google Trends** - Search interest over time
- **Reddit** - Posts, comments, and engagement metrics  
- **YouTube** - Video statistics and engagement data
- **Twitter** - Tweet data and social interactions

### 🌟 Key Features

- **Real-time Data Collection** - Automated hourly data gathering
- **Dynamic Keyword Management** - User-controlled keyword sets
- **Interactive Dashboard** - Modern web interface with charts
- **Trending Analysis** - AI-powered keyword trend detection
- **API Endpoints** - Full REST API for data access
- **Cloud Deployment Ready** - Optimized for Render.com deployment

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- API credentials for data sources

### 1. Local Setup

```bash
# Clone the project
git clone <your-repo-url>
cd web-scraping-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Reddit API (Required)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=YourAppName/1.0

# YouTube API (Required)
YOUTUBE_API_KEY=your_youtube_api_key

# Twitter API (Optional - has fallback)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Google Trends (No API key needed)
# Twitter Nitter (No API key needed - uses web scraping)
```

### 3. Get API Credentials

#### Reddit API Setup
1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Copy Client ID and Client Secret

#### YouTube API Setup  
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Copy the API key

#### Twitter API Setup (Optional)
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app
3. Generate API keys and tokens
4. Copy all credentials

### 4. Run the Application

```bash
# Start the Flask dashboard
python flask_app.py

# Access the dashboard
# Open: http://localhost:8080
```

---

## 🎯 Application Features

### Dashboard Overview
- **Real-time Statistics** - Live data counts and metrics
- **Trending Keywords** - AI-analyzed trending topics
- **Data Source Status** - Health indicators for all sources
- **Recent Activity** - Latest posts and videos

### Data Collection
- **Manual Triggers** - Instant data collection on-demand
- **Automated Scheduling** - Hourly background collection
- **Keyword Management** - Dynamic keyword configuration
- **Source Selection** - Enable/disable specific data sources

### Analytics & Visualization
- **Keyword Frequency Charts** - Cross-platform comparison
- **Google Trends Timeline** - Interest over time graphs
- **Engagement Metrics** - Reddit/YouTube interaction data
- **Trending Analysis** - AI-powered trend detection

### Settings & Configuration
- **Keyword Management** - Add, remove, validate keywords
- **Scheduler Settings** - Configure collection intervals
- **Source Configuration** - Enable/disable data sources
- **Real-time Monitoring** - Live collection logs

---

## 🔧 API Documentation

### Core Data Endpoints

#### Get All Data
```http
GET /api/data
```
Returns complete dataset from all sources.

#### Get Summary Statistics
```http
GET /api/stats
```
Returns dashboard summary metrics.

#### Source-Specific Data
```http
GET /api/reddit          # Reddit posts data
GET /api/youtube         # YouTube videos data  
GET /api/twitter         # Twitter posts data
GET /api/google-trends   # Google Trends data
GET /api/trending        # Trending analysis results
```

### Data Collection

#### Trigger Manual Collection
```http
POST /api/collect
Content-Type: application/json

{
  "keywords": ["AI", "technology", "python"],
  "sources": ["google", "reddit", "youtube", "twitter"]
}
```

#### Real-time Collection Logs
```http
GET /api/logs
```
Server-Sent Events stream for live collection progress.

### Keyword Management

#### Get Current Keywords
```http
GET /api/keywords
```

#### Set Keywords
```http
POST /api/keywords
Content-Type: application/json

{
  "keywords": ["AI", "machine learning", "data science"]
}
```

#### Add Single Keyword
```http
POST /api/keywords/add
Content-Type: application/json

{
  "keyword": "blockchain"
}
```

#### Remove Keyword
```http
POST /api/keywords/remove
Content-Type: application/json

{
  "keyword": "old_keyword"
}
```

#### Reset to Defaults
```http
POST /api/keywords/reset
```

### Scheduler Management

#### Get Scheduler Status
```http
GET /api/scheduler/status
```

#### Update Scheduler Settings
```http
POST /api/scheduler/settings
Content-Type: application/json

{
  "enabled": true,
  "interval_minutes": 60,
  "sources": ["google", "reddit", "youtube"]
}
```

#### Trigger Immediate Collection
```http
POST /api/scheduler/trigger
```

### Chart Data

#### Keyword Frequency Chart
```http
GET /api/charts/keyword-frequency
```

#### Google Trends Chart
```http
GET /api/charts/google-trends
```

#### Reddit Engagement Chart
```http
GET /api/charts/reddit-engagement
```

#### YouTube Engagement Chart
```http
GET /api/charts/youtube-engagement
```

---

## ☁️ Cloud Deployment (Render.com)

### Deployment Options

#### Option 1: Manual Setup (Recommended)

1. **Prepare Repository**
   ```bash
   # Ensure all files are committed
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create Render Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure deployment settings:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `./start.sh`
     - **Environment**: `Python 3`

3. **Set Environment Variables**
   
   In Render dashboard, add these environment variables:

   ```env
   # Production Configuration
   FLASK_ENV=production
   SECRET_KEY=your-production-secret-key-here
   PORT=10000

   # Reddit API (Required)
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=YourAppName/1.0

   # YouTube API (Required)
   YOUTUBE_API_KEY=your_youtube_api_key

   # Twitter API (Optional)
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Access your live dashboard!

#### Option 2: Infrastructure as Code

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: web-scraping-dashboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PORT
        value: 10000
      - key: SECRET_KEY
        generateValue: true
      # Add your API keys here
      - key: REDDIT_CLIENT_ID
        sync: false
      - key: REDDIT_CLIENT_SECRET
        sync: false
      - key: YOUTUBE_API_KEY
        sync: false
```

Deploy with:
```bash
# Render CLI deployment
render services create --file render.yaml
```

#### Option 3: Direct Gunicorn Commands

For advanced users or other hosting platforms:

```bash
# Install dependencies
pip install -r requirements.txt

# Start with Gunicorn (production)
gunicorn --config gunicorn.conf.py app:application

# Or start manually with custom settings
gunicorn --bind 0.0.0.0:10000 --workers 4 --timeout 120 app:application
```

### Production Features

#### Gunicorn WSGI Server
The production deployment uses Gunicorn for optimal performance:
- **Multiple Workers**: Automatically scales based on CPU cores
- **Robust Handling**: Handles high traffic and concurrent requests
- **Memory Management**: Automatic worker recycling to prevent memory leaks
- **Production Logging**: Comprehensive access and error logging
- **120s Timeout**: Extended timeout for data collection operations

#### Built-in Scheduler
The production deployment includes an automatic background scheduler that:
- Runs hourly data collection automatically
- Handles Render's ephemeral storage (files don't persist)
- Logs results instead of file storage for monitoring
- Provides health check endpoint at `/health`

#### Manual Trigger Endpoint
```http
GET /trigger-collection
```
Triggers immediate data collection for testing.

#### Environment Detection
The app automatically detects production vs local environment and adapts behavior:
- **Local**: File-based storage, debug mode
- **Production**: Logging-based monitoring, optimized threading

### Render Free Tier Considerations

- **Service Sleep**: Free services sleep after 15 minutes of inactivity
- **Build Time**: 10 minutes maximum build time
- **Ephemeral Storage**: Files don't persist between deploys
- **Monthly Hours**: 750 hours per month limit

### Upgrade Options

For 24/7 reliability, consider:
- **Render Paid Plans**: Starting at $7/month for always-on services
- **External Cron Services**: GitHub Actions, cron-job.org
- **Database Integration**: PostgreSQL for persistent storage

---

## 🗂️ Project Structure

```
web-scraping-project/
├── app.py                      # Production entry point
├── flask_app.py               # Main Flask application
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── PROJECT_GUIDE.md          # This comprehensive guide
│
├── data/                      # Data storage
│   ├── cleaned_data.json     # Processed data
│   ├── raw_google_data.json  # Google Trends raw data
│   ├── raw_reddit_data.json  # Reddit raw data
│   ├── raw_youtube_data.json # YouTube raw data
│   └── raw_twitter_data.json # Twitter raw data
│
├── templates/                 # HTML templates
│   ├── base.html             # Base template
│   ├── dashboard.html        # Main dashboard
│   ├── data_source.html      # Data source pages
│   ├── settings.html         # Settings page
│   ├── trending_analysis.html # Trending analysis
│   └── error.html            # Error pages
│
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   ├── js/
│   │   └── app.js            # Frontend JavaScript
│   └── img/                  # Images
│
├── Data Collection Modules
├── fetch_google_data.py       # Google Trends collector
├── fetch_reddit_data.py       # Reddit data collector
├── fetch_youtube_data.py      # YouTube data collector
├── fetch_twitter_data.py      # Twitter data collector
├── fetch_twitter_nitter.py    # Nitter fallback collector
│
├── Processing & Analysis
├── clean_data.py             # Data cleaning pipeline
├── trending_analysis.py      # AI trending analysis
│
├── Core Management
├── keyword_manager.py        # Dynamic keyword management
├── scheduler.py              # Automated scheduling system
│
└── utils/                    # Utility functions
```

---

## ⚙️ Configuration Guide

### Keyword Management

The system supports dynamic keyword management with validation:

```python
# Default keywords (fallback)
DEFAULT_KEYWORDS = [
    "artificial intelligence",
    "machine learning", 
    "data science",
    "python programming",
    "web development"
]

# Keywords are stored in: data/user_keywords.json
# Auto-validated for:
# - Length (2-50 characters)
# - Special characters
# - Duplicates
# - Empty values
```

### Data Collection Settings

```python
# Collection intervals
SCHEDULER_CONFIG = {
    'default_interval': 60,      # minutes
    'min_interval': 5,           # minimum allowed
    'max_interval': 1440,        # maximum (24 hours)
    'sources': ['google', 'reddit', 'youtube', 'twitter']
}

# Data source timeouts
COLLECTION_TIMEOUTS = {
    'youtube': 60,    # seconds
    'reddit': 30,     # seconds  
    'google': 30,     # seconds
    'twitter': 30     # seconds
}
```

### Dashboard Configuration

```python
DASHBOARD_CONFIG = {
    'refresh_interval': 30,      # seconds
    'max_trending_display': 15,  # keywords
    'chart_colors': {
        'primary': '#007bff',
        'success': '#28a745', 
        'warning': '#ffc107',
        'danger': '#dc3545'
    }
}
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Missing dependencies
pip install -r requirements.txt

# Virtual environment not activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

#### 2. API Rate Limits
- **Reddit**: 60 requests per minute
- **YouTube**: 10,000 units per day (quota)
- **Twitter**: Varies by endpoint
- **Google Trends**: No official limits (but can be rate limited)

#### 3. Empty Data Results
- Check API credentials in `.env`
- Verify internet connection
- Check service status (Reddit, YouTube, etc.)
- Review logs for specific error messages

#### 4. Scheduler Not Working
```python
# Check scheduler status
GET /api/scheduler/status

# Restart scheduler
POST /api/scheduler/settings
{
  "enabled": false
}
# Then enable again
```

#### 5. Memory Issues on Render
- Optimize data collection batch sizes
- Consider upgrading to paid Render plan
- Implement data pagination for large datasets

### Debug Mode

Enable detailed logging:

```bash
# Set environment variable
export FLASK_ENV=development

# Or in .env file
FLASK_ENV=development
```

### Log Analysis

Check application logs:
- **Local**: `scraping.log` file
- **Render**: Dashboard logs section
- **Real-time**: Connect to `/api/logs` endpoint

---

## 🔐 Security Considerations

### API Key Security
- Never commit API keys to version control
- Use environment variables for all credentials
- Rotate API keys regularly
- Monitor API usage for unusual activity

### Production Security
```python
# Use strong secret keys
SECRET_KEY = os.urandom(24).hex()

# Enable HTTPS in production
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
```

### Rate Limiting
Implement rate limiting for production:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

---

## 📈 Performance Optimization

### Data Collection
- **Parallel Processing**: Multiple sources collected simultaneously
- **Timeout Protection**: Prevents hanging requests
- **Error Handling**: Graceful degradation when sources fail
- **Caching**: Minimize duplicate API calls

### Frontend Performance
- **Chart Optimization**: Efficient data visualization
- **Real-time Updates**: Server-Sent Events for live data
- **Lazy Loading**: Load data as needed
- **Cache Control**: Prevent stale data display

### Database Optimization (Future)
Consider adding PostgreSQL for:
- Persistent data storage
- Historical trend analysis
- Advanced querying capabilities
- Better concurrent access

---

## 🚧 Future Enhancements

### Planned Features
- **Historical Analysis**: Long-term trend tracking
- **Custom Alerts**: Keyword spike notifications  
- **Export Features**: CSV/JSON data export
- **User Accounts**: Multi-user support
- **Advanced Filtering**: Time-based data filtering
- **Mobile App**: React Native companion app

### Integration Ideas
- **Slack/Discord Bots**: Trend notifications
- **Email Reports**: Daily/weekly summaries
- **Webhook Support**: External system integration
- **GraphQL API**: More flexible data querying

---

## 📞 Support & Contributing

### Getting Help
1. Check this guide for common solutions
2. Review application logs for error details
3. Check API service status pages
4. Search existing GitHub issues

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
python -m pytest

# Format code
black .

# Lint code
flake8 .
```

---

## 📄 License & Credits

### Dependencies
- **Flask**: Web framework
- **Pandas**: Data processing
- **Requests**: HTTP requests
- **BeautifulSoup**: Web scraping
- **APScheduler**: Job scheduling
- **Chart.js**: Data visualization

### API Services
- **Google Trends**: pytrends library
- **Reddit API**: PRAW (Python Reddit API Wrapper)
- **YouTube API**: Google API Client
- **Twitter API**: Official Twitter API v2
- **Nitter**: Alternative Twitter interface

---

## 🎉 Conclusion

This web scraping dashboard provides a comprehensive solution for monitoring keyword trends across multiple platforms. With features ranging from automated data collection to real-time visualization, it's designed to scale from local development to cloud production.

The modular architecture allows for easy extension and customization, while the robust error handling ensures reliable operation even when external services are unavailable.

**Happy trending! 📊🚀**

---

*Last updated: [Current Date]*
*Version: 2.0*
*Contact: [Your Contact Information]* 