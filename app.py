"""
Streamlit Dashboard for Keyword Trends Analysis
==============================================

This is the main dashboard for visualizing scraped data from Google Trends and Reddit.
Features:
1. Interactive keyword search
2. Data visualization with charts
3. Reddit posts display
4. Google Trends analysis
5. Real-time data collection

Author: Web Scraping Project
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

# Local imports
from config import (
    DASHBOARD_CONFIG,
    CHART_COLORS,
    DATA_PATHS,
    DEFAULT_KEYWORDS
)

# Import data collection modules
try:
    from fetch_google_data import collect_all_google_data, save_google_data
    from fetch_reddit_data import collect_all_reddit_data, save_reddit_data
    from clean_data import DataCleaner, save_cleaned_data
    from save_to_db import MongoDBManager, load_cleaned_data
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure all required modules are in the same directory")

# Configure Streamlit page
st.set_page_config(
    page_title=DASHBOARD_CONFIG['page_title'],
    page_icon=DASHBOARD_CONFIG['page_icon'],
    layout="wide",  # type: ignore
    initial_sidebar_state="expanded"  # type: ignore
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .keyword-tag {
        background-color: #e1f5fe;
        color: #01579b;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
    }
    .data-source-tag {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load cleaned data with caching"""
    try:
        data = load_cleaned_data()
        if data:
            return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
    return None


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_database_summary():
    """Get database summary with caching"""
    try:
        db_manager = MongoDBManager()
        if db_manager.connect():
            summary = db_manager.get_data_summary()
            db_manager.close_connection()
            return summary
    except Exception as e:
        st.warning(f"Could not connect to database: {e}")
    return None


def create_keyword_frequency_chart(data: Dict[str, Any]) -> Optional[go.Figure]:
    """Create keyword frequency chart"""
    try:
        if 'keyword_analysis' not in data:
            return None
        
        keyword_analysis = data['keyword_analysis']
        keywords = []
        reddit_counts = []
        google_counts = []
        
        for keyword, stats in keyword_analysis.items():
            keywords.append(keyword)
            reddit_counts.append(stats.get('reddit_posts_count', 0))
            google_counts.append(stats.get('google_related_queries_count', 0))
        
        # Create grouped bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Reddit Posts',
            x=keywords,
            y=reddit_counts,
            marker_color=CHART_COLORS[0],
            text=reddit_counts,
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='Google Related Queries',
            x=keywords,
            y=google_counts,
            marker_color=CHART_COLORS[1],
            text=google_counts,
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Keyword Frequency Across Data Sources',
            xaxis_title='Keywords',
            yaxis_title='Count',
            barmode='group',
            height=500,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating keyword frequency chart: {e}")
        return None


def create_reddit_engagement_chart(data: Dict[str, Any]) -> Optional[go.Figure]:
    """Create Reddit engagement chart"""
    try:
        reddit_data = data.get('reddit_data', {})
        posts = reddit_data.get('posts', [])
        
        if not posts:
            return None
        
        # Create DataFrame for analysis
        df = pd.DataFrame(posts)
        
        # Group by keyword and calculate average scores
        keyword_scores = df.groupby('search_keyword').agg({
            'score': ['mean', 'sum', 'count'],
            'num_comments': ['mean', 'sum'],
            'upvote_ratio': 'mean'
        }).round(2)
        
        # Flatten column names
        keyword_scores.columns = ['_'.join(col).strip() for col in keyword_scores.columns]
        keyword_scores = keyword_scores.reset_index()
        
        # Create subplot with multiple metrics
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Average Score', 'Total Posts', 'Average Comments', 'Average Upvote Ratio'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Average Score
        fig.add_trace(
            go.Bar(x=keyword_scores['search_keyword'], 
                   y=keyword_scores['score_mean'],
                   name='Avg Score',
                   marker_color=CHART_COLORS[0]),
            row=1, col=1
        )
        
        # Total Posts
        fig.add_trace(
            go.Bar(x=keyword_scores['search_keyword'], 
                   y=keyword_scores['score_count'],
                   name='Total Posts',
                   marker_color=CHART_COLORS[1]),
            row=1, col=2
        )
        
        # Average Comments
        fig.add_trace(
            go.Bar(x=keyword_scores['search_keyword'], 
                   y=keyword_scores['num_comments_mean'],
                   name='Avg Comments',
                   marker_color=CHART_COLORS[2]),
            row=2, col=1
        )
        
        # Average Upvote Ratio
        fig.add_trace(
            go.Bar(x=keyword_scores['search_keyword'], 
                   y=keyword_scores['upvote_ratio_mean'],
                   name='Avg Upvote Ratio',
                   marker_color=CHART_COLORS[3]),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="Reddit Engagement Metrics by Keyword",
            height=600,
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating Reddit engagement chart: {e}")
        return None


def create_subreddit_distribution_chart(data: Dict[str, Any]) -> Optional[go.Figure]:
    """Create subreddit distribution pie chart"""
    try:
        reddit_data = data.get('reddit_data', {})
        posts = reddit_data.get('posts', [])
        
        if not posts:
            return None
        
        # Count posts by subreddit
        df = pd.DataFrame(posts)
        subreddit_counts = df['subreddit'].value_counts().head(10)  # Top 10 subreddits
        
        fig = go.Figure(data=[go.Pie(
            labels=subreddit_counts.index,
            values=subreddit_counts.values,
            hole=0.4,
            marker_colors=CHART_COLORS[:len(subreddit_counts)]
        )])
        
        fig.update_layout(
            title="Top Subreddits Distribution",
            height=500,
            annotations=[dict(text='Subreddits', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating subreddit distribution chart: {e}")
        return None


def create_google_trends_chart(data: Dict[str, Any]) -> Optional[go.Figure]:
    """Create Google Trends interest over time chart"""
    try:
        google_data = data.get('google_trends_data', {})
        interest_data = google_data.get('interest_data', [])
        
        if not interest_data:
            return None
        
        # Convert to DataFrame for easier manipulation
        df_data = []
        for entry in interest_data:
            date = entry.get('date')
            values = entry.get('values', {})
            for keyword, value in values.items():
                if value > 0:  # Only include non-zero values
                    df_data.append({
                        'date': pd.to_datetime(date),
                        'keyword': keyword,
                        'value': value
                    })
        
        if not df_data:
            return None
        
        df = pd.DataFrame(df_data)
        
        # Create line chart
        fig = px.line(
            df, 
            x='date', 
            y='value', 
            color='keyword',
            title='Google Trends - Interest Over Time',
            labels={'value': 'Search Interest (0-100)', 'date': 'Date'},
            color_discrete_sequence=CHART_COLORS
        )
        
        fig.update_layout(
            height=500,
            xaxis_title='Date',
            yaxis_title='Search Interest',
            legend_title='Keywords',
            hovermode='x unified'
        )
        
        # Update traces for better styling
        fig.update_traces(line=dict(width=3), marker=dict(size=6))
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating Google Trends chart: {e}")
        return None


def display_reddit_posts(data: Dict[str, Any], keyword_filter: Optional[str] = None, limit: int = 10):
    """Display Reddit posts in a formatted way"""
    try:
        reddit_data = data.get('reddit_data', {})
        posts = reddit_data.get('posts', [])
        
        if not posts:
            st.info("No Reddit posts available")
            return
        
        # Filter by keyword if specified
        if keyword_filter and keyword_filter != "All":
            posts = [p for p in posts if p.get('search_keyword') == keyword_filter]
        
        # Sort by score (highest first)
        posts = sorted(posts, key=lambda x: x.get('score', 0), reverse=True)[:limit]
        
        st.subheader(f"📱 Reddit Posts {f'for {keyword_filter}' if keyword_filter and keyword_filter != 'All' else ''}")
        
        for i, post in enumerate(posts, 1):
            with st.expander(f"#{i} - {post.get('title', 'No title')[:100]}..."):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Title:** {post.get('title', 'N/A')}")
                    if post.get('content'):
                        st.markdown(f"**Content:** {post.get('content')[:300]}...")
                    st.markdown(f"**Author:** {post.get('author', 'N/A')}")
                    st.markdown(f"**Subreddit:** r/{post.get('subreddit', 'N/A')}")
                
                with col2:
                    st.metric("Score", post.get('score', 0))
                    st.metric("Comments", post.get('num_comments', 0))
                
                with col3:
                    st.metric("Upvote Ratio", f"{post.get('upvote_ratio', 0):.2f}")
                    if post.get('permalink'):
                        st.markdown(f"[View on Reddit]({post.get('permalink')})")
                
                # Display keywords
                keywords = post.get('extracted_keywords', [])
                if keywords:
                    st.markdown("**Keywords:** " + " ".join([
                        f'<span class="keyword-tag">{kw}</span>' for kw in keywords[:10]
                    ]), unsafe_allow_html=True)
                
                st.markdown(f"**Search Keyword:** {post.get('search_keyword', 'N/A')}")
                st.markdown(f"**Created:** {post.get('created_date', 'N/A')}")
                
    except Exception as e:
        st.error(f"Error displaying Reddit posts: {e}")


def display_google_trends_data(data: Dict[str, Any], keyword_filter: Optional[str] = None):
    """Display Google Trends related queries and interest data"""
    try:
        google_data = data.get('google_trends_data', {})
        
        # Display Interest Over Time Chart
        st.subheader("📈 Google Trends - Interest Over Time")
        trends_chart = create_google_trends_chart(data)
        if trends_chart:
            st.plotly_chart(trends_chart, use_container_width=True, key="detailed_google_trends_chart")
        else:
            st.info("No Google Trends interest data available for chart")
        
        # Display Related Queries
        related_queries = google_data.get('related_queries', [])
        
        if not related_queries:
            st.info("No Google Trends related queries available")
            return
        
        # Filter by keyword if specified
        if keyword_filter and keyword_filter != "All":
            related_queries = [q for q in related_queries if q.get('keyword') == keyword_filter]
        
        if not related_queries:
            st.info(f"No related queries available for {keyword_filter}")
            return
        
        st.subheader(f"🔍 Google Trends Related Queries {f'for {keyword_filter}' if keyword_filter and keyword_filter != 'All' else ''}")
        
        # Group by keyword
        by_keyword = {}
        for query in related_queries:
            keyword = query.get('keyword', 'Unknown')
            if keyword not in by_keyword:
                by_keyword[keyword] = {'top': [], 'rising': []}
            
            query_type = query.get('type', 'top')
            by_keyword[keyword][query_type].append(query)
        
        for keyword, queries in by_keyword.items():
            with st.expander(f"🔑 {keyword}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔥 Top Queries**")
                    top_queries = sorted(queries['top'], key=lambda x: x.get('value', 0), reverse=True)[:10]
                    if top_queries:
                        for query in top_queries:
                            st.markdown(f"• {query.get('query', 'N/A')} ({query.get('value', 0)})")
                    else:
                        st.info("No top queries available")
                
                with col2:
                    st.markdown("**📈 Rising Queries**")
                    rising_queries = queries['rising'][:10]
                    if rising_queries:
                        for query in rising_queries:
                            value = query.get('value', 0)
                            value_str = f"{value}%" if isinstance(value, (int, float)) else str(value)
                            st.markdown(f"• {query.get('query', 'N/A')} ({value_str})")
                    else:
                        st.info("No rising queries available")
                        
    except Exception as e:
        st.error(f"Error displaying Google Trends data: {e}")


def collect_new_data(keywords: List[str]):
    """Collect new data for given keywords"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Collect Google Trends data
        status_text.text("🔍 Collecting Google Trends data...")
        progress_bar.progress(20)
        
        google_data = collect_all_google_data(keywords)
        save_google_data(google_data)
        
        # Step 2: Collect Reddit data
        status_text.text("📱 Collecting Reddit data...")
        progress_bar.progress(50)
        
        reddit_data = collect_all_reddit_data(keywords)
        save_reddit_data(reddit_data)
        
        # Step 3: Clean data
        status_text.text("🧹 Cleaning and processing data...")
        progress_bar.progress(80)
        
        cleaner = DataCleaner()
        cleaned_google = cleaner.clean_google_trends_data(google_data)
        cleaned_reddit = cleaner.clean_reddit_data(reddit_data)
        unified_data = cleaner.create_unified_dataset(cleaned_google, cleaned_reddit)
        
        save_cleaned_data(unified_data)
        
        # Step 4: Save to database
        status_text.text("💾 Saving to database...")
        progress_bar.progress(100)
        
        try:
            db_manager = MongoDBManager()
            if db_manager.connect():
                db_manager.create_indexes()
                db_manager.save_data(unified_data)
                db_manager.close_connection()
        except Exception as e:
            st.warning(f"Database save failed: {e}")
        
        status_text.text("✅ Data collection completed!")
        st.success("Data collection completed successfully!")
        
        # Clear cache to reload new data
        st.cache_data.clear()
        
    except Exception as e:
        st.error(f"Error during data collection: {e}")
    finally:
        progress_bar.empty()
        status_text.empty()


def main():
    """Main dashboard function"""
    
    # Header
    st.title("📊 Keyword Trends Dashboard")
    st.markdown("Analyze trending keywords from Google Trends and Reddit")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Data collection section
        st.subheader("📥 Data Collection")
        
        # Keyword input
        new_keywords_input = st.text_area(
            "Enter keywords (one per line):",
            value="\n".join(DEFAULT_KEYWORDS),
            height=100
        )
        
        if st.button("🚀 Collect New Data", type="primary"):
            keywords = [kw.strip() for kw in new_keywords_input.split('\n') if kw.strip()]
            if keywords:
                collect_new_data(keywords)
            else:
                st.error("Please enter at least one keyword")
        
        st.divider()
        
        # Display settings
        st.subheader("⚙️ Display Settings")
        show_charts = st.checkbox("Show Charts", value=True)
        show_reddit = st.checkbox("Show Reddit Posts", value=True)
        show_google = st.checkbox("Show Google Trends", value=True)
        
        # Filters
        st.subheader("🔍 Filters")
        posts_limit = st.slider("Reddit Posts Limit", 5, 50, 10)
    
    # Load and display data
    data = load_data()
    
    if data is None:
        st.warning("⚠️ No data available. Please collect data first using the sidebar controls.")
        
        # Show database summary if available
        db_summary = get_database_summary()
        if db_summary:
            st.info("💡 Data found in database. The dashboard will show cached data.")
            st.json(db_summary)
        
        return
    
    # Data overview
    st.header("📋 Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_keywords = len(data.get('keywords_analyzed', []))
        st.metric("Total Keywords", total_keywords)
    
    with col2:
        reddit_posts = len(data.get('reddit_data', {}).get('posts', []))
        st.metric("Reddit Posts", reddit_posts)
    
    with col3:
        google_queries = len(data.get('google_trends_data', {}).get('related_queries', []))
        st.metric("Google Queries", google_queries)
    
    with col4:
        data_sources = data.get('data_sources', [])
        st.metric("Data Sources", len(data_sources))
    
    # Display data sources
    if data_sources:
        st.markdown("**Data Sources:** " + " ".join([
            f'<span class="data-source-tag">{source}</span>' for source in data_sources
        ]), unsafe_allow_html=True)
    
    # Keywords analyzed
    keywords_analyzed = data.get('keywords_analyzed', [])
    if keywords_analyzed:
        st.markdown("**Keywords Analyzed:** " + " ".join([
            f'<span class="keyword-tag">{kw}</span>' for kw in keywords_analyzed
        ]), unsafe_allow_html=True)
    
    # Keyword filter for detailed views
    st.divider()
    keyword_filter = st.selectbox(
        "Filter by keyword:",
        ["All"] + keywords_analyzed,
        key="keyword_filter"
    )
    
    # Charts section
    if show_charts and data:
        st.header("📈 Data Visualization")
        
        # Keyword frequency chart
        freq_chart = create_keyword_frequency_chart(data)
        if freq_chart:
            st.plotly_chart(freq_chart, use_container_width=True)
        
        # Google Trends interest over time chart
        trends_chart = create_google_trends_chart(data)
        if trends_chart:
            st.plotly_chart(trends_chart, use_container_width=True, key="main_google_trends_chart")
        
        # Reddit engagement chart
        engagement_chart = create_reddit_engagement_chart(data)
        if engagement_chart:
            st.plotly_chart(engagement_chart, use_container_width=True)
        
        # Subreddit distribution
        subreddit_chart = create_subreddit_distribution_chart(data)
        if subreddit_chart:
            st.plotly_chart(subreddit_chart, use_container_width=True)
    
    # Reddit posts section
    if show_reddit:
        st.divider()
        display_reddit_posts(data, keyword_filter, posts_limit)
    
    # Google Trends section
    if show_google:
        st.divider()
        display_google_trends_data(data, keyword_filter)
    
    # Footer
    st.divider()
    st.markdown("---")
    st.markdown(
        f"**Last Updated:** {data.get('creation_timestamp', 'Unknown')} | "
        f"**Database:** MongoDB | "
        f"**Total Records:** {data.get('summary_stats', {}).get('total_keywords', 'N/A')}"
    )


if __name__ == "__main__":
    main() 