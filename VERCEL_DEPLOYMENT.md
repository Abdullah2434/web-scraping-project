# Vercel Deployment Guide

## 🚀 Quick Vercel Deployment

### 1. Deploy to Vercel

```bash
# Install Vercel CLI (if you don't have it)
npm i -g vercel

# Deploy from your project directory
vercel

# Follow the prompts:
# - Link to existing project? No
# - Project name: web-scraping-dashboard
# - Directory: ./
# - Override settings? No
```

### 2. Set Environment Variables

In Vercel dashboard, add these environment variables:

```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=WebScrapingDashboard/1.0
YOUTUBE_API_KEY=your_youtube_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
```

## ⚠️ Vercel Limitations & Solutions

### Background Processes Not Supported
**Issue:** Vercel is serverless - no background schedulers
**Solution:** Use external cron services

### 🔄 External Scheduling Options

#### Option 1: GitHub Actions (Recommended)
Create `.github/workflows/data-collection.yml`:

```yaml
name: Automated Data Collection
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch: # Manual trigger

jobs:
  collect-data:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Data Collection
        run: |
          curl -X POST "https://your-app.vercel.app/api/collect" \
            -H "Content-Type: application/json" \
            -d '{"keywords":["AI","technology","python"],"sources":["google","reddit","youtube","twitter"]}'
```

#### Option 2: Vercel Cron (Pro Plan)
Add to `vercel.json`:
```json
{
  "crons": [
    {
      "path": "/api/collect",
      "schedule": "0 * * * *"
    }
  ]
}
```

#### Option 3: External Cron Services
- **cron-job.org** (free)
- **EasyCron.com** 
- **Cronitor.io**

Set to call: `https://your-app.vercel.app/trigger-collection`

## 🧪 Test Your Deployment

After deployment, test these URLs:

1. **Main Dashboard:** `https://your-app.vercel.app`
2. **Health Check:** `https://your-app.vercel.app/health`
3. **Manual Trigger:** `https://your-app.vercel.app/trigger-collection`
4. **API Test:** `https://your-app.vercel.app/api/stats`

## 💡 Vercel Benefits

✅ **Free HTTPS** - Automatic SSL certificates
✅ **Global CDN** - Fast worldwide access
✅ **Auto-scaling** - Handles traffic spikes
✅ **Git Integration** - Auto-deploy on push
✅ **Zero downtime** - Never sleeps (unlike Render free)

## 🚧 Data Storage Note

Vercel has **ephemeral storage** - files don't persist between deployments.

**Solutions:**
- Data collection works for real-time viewing
- Consider external database for persistence (MongoDB Atlas, PlanetScale)
- Or accept that data is temporary (refreshed each collection)

## 🔧 Troubleshooting

### Import Errors
- Check that all dependencies are in `requirements.txt`
- Vercel build logs will show specific issues

### Timeout Errors
- Vercel free plan: 10-second function timeout
- Optimize or upgrade to Pro for 60 seconds

### Missing Data
- Remember: no persistent storage
- Each visit triggers fresh data collection
- Use external cron for regular updates

## 🎉 Success!

Your dashboard should now be live on Vercel! The URL will be something like:
`https://web-scraping-dashboard-username.vercel.app`

**What works:**
- Full dashboard interface
- Manual data collection
- Real-time API endpoints
- Chart visualizations

**What needs external setup:**
- Automated hourly collection (use GitHub Actions)
- Data persistence (use external database if needed) 