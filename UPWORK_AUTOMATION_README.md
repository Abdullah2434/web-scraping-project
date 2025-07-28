# Upwork Job Automation System

## 🎯 Overview

This system automatically collects Upwork jobs every 2 hours and adds them to Google Sheets with the following features:

- **⏰ 2-Hour Intervals**: Runs every 2 hours automatically
- **📋 Unique Jobs Only**: Prevents duplicate jobs using hash tracking
- **📅 Daily Sheets**: Creates new sheets daily with date/month titles
- **🔗 Google Sheets Integration**: Automatically adds jobs to your spreadsheet
- **🤖 100% Automated**: No manual intervention required

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Sheets

Run the setup script:

```bash
python setup_google_sheets.py
```

Follow the instructions to:
1. Create Google Cloud Project
2. Enable Google Sheets API
3. Create Service Account
4. Download credentials
5. Share your Google Sheet

### 3. Configure Keywords

Edit `data/user_keywords.json` or use the dashboard to set your search keywords:

```json
{
  "keywords": ["python", "web development", "data science"],
  "max_keywords": 5,
  "created_at": "2025-01-15T10:00:00",
  "last_updated": "2025-01-15T10:00:00"
}
```

### 4. Test the System

```bash
python test_upwork_scheduler.py
```

### 5. Start the Scheduler

```bash
python upwork_scheduler.py
```

## 📋 System Components

### 1. Upwork Scheduler (`upwork_scheduler.py`)
- Runs every 2 hours (7200 seconds)
- Collects jobs using enhanced Upwork scraper
- Automatically adds unique jobs to Google Sheets
- Creates daily sheets with date/month titles
- Prevents duplicates using hash tracking

### 2. Google Sheets Integration (`google_sheets_integration.py`)
- Connects to your Google Sheet
- Creates daily sheets automatically
- Adds unique jobs with comprehensive data
- Formats headers and data properly
- Tracks unique jobs to prevent duplicates

### 3. Enhanced Upwork Scraper (`fetch_upwork_data_enhanced.py`)
- Collects comprehensive job data
- Handles private jobs and filtering
- Extracts detailed job information
- Supports multiple keywords and filters

## 📊 Google Sheets Structure

Each daily sheet contains these columns:

| Column | Description |
|--------|-------------|
| Job ID | Unique job identifier |
| Title | Job title |
| Budget | Budget information |
| Job Type | Hourly/Fixed |
| Experience Level | Entry/Intermediate/Expert |
| Posted Time | When job was posted |
| Proposals | Number of proposals |
| Client Location | Client's location |
| Client Rating | Client's rating |
| Payment Verified | Payment verification status |
| Skills | Required skills |
| Description | Job description (truncated) |
| Keywords | Search keywords used |
| Collection Date | When job was collected |
| Job URL | Direct link to job |

## ⚙️ Configuration

### Scheduler Settings

Edit `data/upwork_scheduler_status.json`:

```json
{
  "enabled": true,
  "interval_minutes": 120,
  "max_jobs_per_keyword": 15,
  "skip_private_jobs": true
}
```

### Upwork Filters

The system uses these default filters:

```python
upwork_filters = {
    'time_range': 'today',
    'hourly_filter': '',
    'budget_range': 'any',
    'job_type': 'any',
    'experience_level': 'any',
    'payment_status': 'both',
    'sort_by': 'recency'
}
```

## 📈 Monitoring

### Check Scheduler Status

```bash
python test_upwork_scheduler.py
```

### View Logs

Check `scraping.log` for detailed information:

```bash
tail -f scraping.log
```

### Google Sheets Summary

The system provides a summary of:
- Total jobs collected
- Jobs added to sheets
- Duplicate jobs skipped
- Daily sheet statistics

## 🔧 Troubleshooting

### Common Issues

1. **Google Sheets Connection Failed**
   - Check credentials file exists
   - Verify service account has access
   - Ensure Google Sheets API is enabled

2. **No Jobs Collected**
   - Check keywords are configured
   - Verify internet connection
   - Check Upwork is accessible

3. **Duplicate Jobs**
   - System automatically prevents duplicates
   - Uses hash-based tracking
   - Check unique jobs cache

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📅 Daily Sheet Creation

The system automatically creates daily sheets with names like:
- `January_15_2025`
- `January_16_2025`
- etc.

Each sheet includes:
- Formatted headers
- Comprehensive job data
- Automatic date tracking

## 🔄 Automation Flow

1. **Every 2 Hours**:
   - Scheduler triggers collection
   - Scrapes Upwork for jobs
   - Filters unique jobs
   - Adds to Google Sheets
   - Updates statistics

2. **Daily**:
   - Creates new sheet with date
   - Continues adding jobs
   - Maintains unique tracking

3. **Continuous**:
   - Runs 24/7
   - Handles errors gracefully
   - Logs all activities

## 📊 Statistics Tracking

The system tracks:
- Total jobs collected
- Jobs added to sheets
- Duplicate jobs skipped
- Collection success rate
- Error counts and messages

## 🛡️ Error Handling

- **Network Errors**: Automatic retry
- **API Limits**: Rate limiting
- **Duplicate Jobs**: Hash-based prevention
- **Sheet Creation**: Automatic fallback
- **Data Validation**: Comprehensive checks

## 📋 File Structure

```
web-scraping-project/
├── upwork_scheduler.py           # Main scheduler
├── google_sheets_integration.py  # Sheets integration
├── fetch_upwork_data_enhanced.py # Enhanced scraper
├── setup_google_sheets.py        # Setup script
├── test_upwork_scheduler.py      # Test script
├── data/
│   ├── upwork_scheduler_status.json
│   ├── unique_jobs_cache.json
│   └── user_keywords.json
└── google_sheets_credentials.json # Your credentials
```

## 🎯 Success Metrics

- **Jobs Collected**: 50-100+ per day
- **Unique Jobs**: 90%+ unique rate
- **Success Rate**: 95%+ collection success
- **Sheet Creation**: 100% daily sheets
- **Uptime**: 24/7 automated operation

## 🚀 Production Deployment

For 24/7 operation, consider:
- Cloud deployment (AWS, Google Cloud)
- Database for persistent storage
- Monitoring and alerting
- Backup and recovery

## 📞 Support

For issues or questions:
1. Check the logs in `scraping.log`
2. Run `python test_upwork_scheduler.py`
3. Verify Google Sheets credentials
4. Check internet connectivity

## 🎉 Success!

Once configured, your system will:
- ✅ Collect jobs every 2 hours
- ✅ Add unique jobs to Google Sheets
- ✅ Create daily sheets automatically
- ✅ Prevent duplicate jobs
- ✅ Run 100% automated

Your Google Sheet will be populated with fresh Upwork jobs every 2 hours, organized by date, with no duplicates! 