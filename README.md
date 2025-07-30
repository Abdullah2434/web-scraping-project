# Web Scraping Project: Keyword Trend Analysis

A beginner-friendly Python project that scrapes trending data based on keywords from Google Trends and Reddit, then visualizes the results in a Streamlit dashboard.

## 🎯 Features

- **Google Trends Integration**: Fetch trending searches and related queries
- **Reddit Data Collection**: Get top posts and discussions for keywords
- **Data Cleaning**: Remove duplicates, normalize text, and process data
- **JSON File Storage**: Store data in lightweight JSON files
- **Interactive Dashboard**: Streamlit app with charts and search functionality

## 📁 Project Structure

```
web-scraping-project/
├── requirements.txt          # Python dependencies
├── config.py                # Configuration settings
├── fetch_google_data.py     # Google Trends data collection
├── fetch_reddit_data.py     # Reddit data collection
├── clean_data.py            # Data cleaning and processing
├── app.py                   # Streamlit dashboard
└── README.md                # This file
```

## 🚀 Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Reddit API Setup (Required for Reddit data)

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Fill in the form:
   - **Name**: Your app name (e.g., "Keyword Scraper")
   - **App type**: Select "script"
   - **Description**: Optional description
   - **About URL**: Leave blank or add your website
   - **Redirect URI**: Use `http://localhost:5000`
4. Click "Create app"
5. Note down the **Client ID** (under the app name) and **Client Secret**

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=keyword_scraper_bot_1.0
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

### 4. Run the Application

#### Collect Data
```bash
# Fetch Google Trends data
python fetch_google_data.py

# Fetch Reddit data
python fetch_reddit_data.py

# Clean and process data
python clean_data.py
```

#### Launch Dashboard
```bash
streamlit run app.py
```

## 📊 Usage

1. **Data Collection**: Run the fetch scripts with your keywords
2. **Dashboard**: Open the Streamlit app and explore:
   - Enter new keywords to search
   - View keyword frequency charts
   - Browse related queries from Google Trends
   - See Reddit post titles and discussions

## 🔧 Configuration

Edit `config.py` to customize:
- Keywords to search
- API rate limits
- Data collection parameters
- File storage paths

## 📚 Learning Resources

- [Python Web Scraping Tutorial](https://realpython.com/beautiful-soup-web-scraper-python/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pandas Data Cleaning](https://pandas.pydata.org/docs/user_guide/index.html)
- [MongoDB Python Tutorial](https://pymongo.readthedocs.io/en/stable/tutorial.html)

## ⚠️ Important Notes

- **Rate Limiting**: Be respectful with API calls to avoid being blocked
- **Reddit API**: Requires free registration and API credentials
- **Data Privacy**: Follow platform terms of service
- **Error Handling**: Check logs if data collection fails

## 🐛 Troubleshooting

### Common Issues

1. **Reddit API Errors**: Check your `.env` file credentials
2. **Missing Data**: Run data collection scripts before dashboard
3. **Streamlit Errors**: Check all dependencies are installed

### Getting Help

- Check error messages in terminal
- Verify all dependencies are installed: `pip list`
- Review configuration in `config.py`
- Ensure `data/` directory exists for JSON files

## 🎓 Next Steps

Once you're comfortable with the basics:
- Add more data sources (Twitter, YouTube, News APIs)
- Implement real-time data updates
- Add user authentication
- Deploy to cloud platforms
- Create automated data collection schedules

Happy scraping! 🚀 