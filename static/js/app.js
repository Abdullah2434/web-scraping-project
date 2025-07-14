// ===== GLOBAL VARIABLES =====
let charts = {};
let currentData = {};
let isLoadingDashboard = false; // Prevent multiple simultaneous loads

// ===== CHART MANAGEMENT =====
function destroyAllCharts() {
    console.log('🧹 Destroying all existing charts...');
    
    // Destroy charts from our local registry
    Object.keys(charts).forEach(key => {
        if (charts[key] && typeof charts[key].destroy === 'function') {
            try {
                console.log(`🗑️ Destroying chart: ${key}`);
                charts[key].destroy();
                delete charts[key];
            } catch (error) {
                console.warn(`⚠️ Error destroying chart ${key}:`, error);
            }
        }
    });
    
    // Chart.js v4+ uses a different instance management system
    if (typeof Chart !== 'undefined') {
        // Get all registered chart instances
        if (Chart.instances) {
            // Chart.js v4+ stores instances as an array
            const instances = Array.isArray(Chart.instances) ? Chart.instances : Object.values(Chart.instances);
            instances.forEach((instance, index) => {
                try {
                    if (instance && typeof instance.destroy === 'function') {
                        console.log(`🗑️ Destroying Chart.js instance: ${index}`);
                        instance.destroy();
                    }
                } catch (error) {
                    console.warn(`⚠️ Error destroying Chart.js instance ${index}:`, error);
                }
            });
            
            // Clear the instances array/object
            if (Array.isArray(Chart.instances)) {
                Chart.instances.length = 0;
            } else {
                Chart.instances = {};
            }
        }
        
        // Clear Chart.js registry (v4+ specific)
        if (Chart.registry && Chart.registry.controllers) {
            Chart.registry.controllers.clear?.();
        }
    }
    
    // Replace canvas elements to avoid reuse errors
    const canvasIds = ['keywordFrequencyChart', 'googleTrendsChart', 'redditEngagementChart', 'youtubePerformanceChart', 'twitterEngagementChart'];
    canvasIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas && canvas.parentElement) {
            try {
                // Create a new canvas element
                const newCanvas = document.createElement('canvas');
                newCanvas.id = id;
                
                // Copy all attributes and styles
                Array.from(canvas.attributes).forEach(attr => {
                    if (attr.name !== 'width' && attr.name !== 'height') {
                        newCanvas.setAttribute(attr.name, attr.value);
                    }
                });
                
                // Replace the old canvas with the new one
                canvas.parentElement.replaceChild(newCanvas, canvas);
                console.log(`🔄 Recreated canvas: ${id}`);
            } catch (error) {
                console.warn(`⚠️ Error recreating canvas ${id}:`, error);
                // Fallback: just clear the canvas
                const ctx = canvas.getContext('2d');
                if (ctx) {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                }
            }
        }
    });
    
    console.log('✅ Chart destruction completed');
}

// ===== UTILITY FUNCTIONS =====
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Add cache-busting utility function
function getCacheBustingUrl(url) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}_t=${Date.now()}`;
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// ===== DATA COLLECTION MODAL =====
async function showDataCollection() {
    document.getElementById('dataCollectionModal').style.display = 'flex';
    await loadKeywordsForModal();
}

function hideDataCollection() {
    document.getElementById('dataCollectionModal').style.display = 'none';
}

async function loadKeywordsForModal() {
    try {
        const response = await fetch(getCacheBustingUrl('/api/keywords'));
        const data = await response.json();
        
        if (response.ok) {
            displayKeywordsInModal(data.keywords);
            createKeywordSelectionCheckboxes(data.keywords);
        } else {
            showKeywordsErrorInModal('Failed to load keywords');
        }
    } catch (error) {
        console.error('Error loading keywords for modal:', error);
        showKeywordsErrorInModal('Failed to load keywords');
    }
}

function displayKeywordsInModal(keywords) {
    const container = document.getElementById('currentKeywordsDisplay');
    
    if (!keywords || keywords.length === 0) {
        container.innerHTML = '<span style="color: #dc2626; font-style: italic;">No keywords configured</span>';
        container.className = 'current-keywords-display empty';
        return;
    }
    
    container.className = 'current-keywords-display';
    container.innerHTML = keywords.map(keyword => 
        `<span class="current-keyword-tag">🔍 ${keyword}</span>`
    ).join('');
}

function createKeywordSelectionCheckboxes(keywords) {
    const container = document.getElementById('keywordSelectionContainer');
    const noKeywordsMsg = document.getElementById('noKeywordsMessage');
    
    if (!keywords || keywords.length === 0) {
        container.innerHTML = '';
        noKeywordsMsg.style.display = 'block';
        return;
    }
    
    noKeywordsMsg.style.display = 'none';
    container.innerHTML = keywords.map((keyword, index) => `
        <label class="checkbox-label">
            <input type="checkbox" class="keyword-checkbox" value="${keyword}" ${index < 5 ? 'checked' : ''}>
            <span class="checkmark"></span>
            ${keyword}
        </label>
    `).join('');
}

function showKeywordsErrorInModal(message) {
    const container = document.getElementById('currentKeywordsDisplay');
    container.innerHTML = `<span style="color: #dc2626;">⚠️ ${message}</span>`;
    container.className = 'current-keywords-display empty';
    
    document.getElementById('keywordSelectionContainer').innerHTML = '';
    document.getElementById('noKeywordsMessage').style.display = 'block';
}

async function refreshKeywordsInModal() {
    showNotification('Refreshing keywords...', 'info');
    await loadKeywordsForModal();
    showNotification('Keywords refreshed!', 'success');
}

function toggleAllKeywords() {
    const selectAllCheckbox = document.getElementById('selectAllKeywords');
    const keywordCheckboxes = document.querySelectorAll('.keyword-checkbox');
    
    keywordCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

function toggleAllSources() {
    const selectAllCheckbox = document.getElementById('selectAllSources');
    const sourceCheckboxes = [
        document.getElementById('collectGoogle'),
        document.getElementById('collectReddit'),
        document.getElementById('collectYoutube'),
        document.getElementById('collectTwitter')
    ];
    
    sourceCheckboxes.forEach(checkbox => {
        if (checkbox) checkbox.checked = selectAllCheckbox.checked;
    });
}

async function startDataCollection() {
    // Get selected keywords
    const selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    // Get selected sources
    const sources = [];
    if (document.getElementById('collectGoogle').checked) sources.push('google');
    if (document.getElementById('collectReddit').checked) sources.push('reddit');
    if (document.getElementById('collectYoutube').checked) sources.push('youtube');
    if (document.getElementById('collectTwitter').checked) sources.push('twitter');
    
    // Validation
    if (selectedKeywords.length === 0) {
        showNotification('Please select at least one keyword for collection', 'error');
        return;
    }
    
    if (sources.length === 0) {
        showNotification('Please select at least one data source', 'error');
        return;
    }
    
    try {
        hideDataCollection();
        showRealTimeLogging();
        
        showNotification(`Starting data collection for ${selectedKeywords.length} keywords from ${sources.length} sources...`, 'info');
        
        // Start data collection
        const response = await fetch('/api/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keywords: selectedKeywords,
                sources: sources
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'started') {
            showNotification('Data collection started! Watch the progress below.', 'info');
            
            // Start listening to real-time logs
            connectToLogStream();
            
        } else {
            throw new Error(result.error || 'Data collection failed to start');
        }
    } catch (error) {
        console.error('Data collection error:', error);
        showNotification(`Data collection failed: ${error.message}`, 'error');
        hideRealTimeLogging();
    }
}

// Real-time logging functionality
function showRealTimeLogging() {
    // Create logging modal
    const modal = document.createElement('div');
    modal.id = 'loggingModal';
    modal.className = 'logging-modal';
    modal.innerHTML = `
        <div class="logging-modal-content">
            <div class="logging-modal-header">
                <h3>🚀 Data Collection in Progress</h3>
                <div class="progress-indicator">
                    <div class="spinner"></div>
                    <span id="progressText">Initializing...</span>
                </div>
            </div>
            <div class="logging-modal-body">
                <div id="logOutput" class="log-output"></div>
            </div>
            <div class="logging-modal-footer">
                <button onclick="stopDataCollection()" class="btn-secondary">Stop Collection</button>
                <button onclick="hideRealTimeLogging()" class="btn-primary" style="display: none;" id="closeLogsBtn">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add styles if not already added
    if (!document.getElementById('loggingStyles')) {
        const style = document.createElement('style');
        style.id = 'loggingStyles';
        style.textContent = `
            .logging-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 5000;
                backdrop-filter: blur(5px);
            }
            
            .logging-modal-content {
                background: white;
                border-radius: 16px;
                width: 90%;
                max-width: 800px;
                max-height: 80vh;
                display: flex;
                flex-direction: column;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }
            
            .logging-modal-header {
                padding: 1.5rem;
                border-bottom: 2px solid #e5e7eb;
                background: linear-gradient(135deg, #1e3a8a, #3b82f6);
                color: white;
                border-radius: 16px 16px 0 0;
            }
            
            .logging-modal-header h3 {
                margin: 0 0 1rem 0;
                font-size: 1.3rem;
            }
            
            .progress-indicator {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            
            .spinner {
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-top: 3px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .logging-modal-body {
                flex: 1;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .log-output {
                flex: 1;
                padding: 1rem;
                overflow-y: auto;
                background: #0f172a;
                color: #e2e8f0;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
                line-height: 1.4;
                max-height: 400px;
            }
            
            .log-entry {
                margin-bottom: 0.5rem;
                padding: 0.25rem 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .log-timestamp {
                color: #94a3b8;
                font-size: 0.8rem;
            }
            
            .log-level-INFO { color: #3b82f6; }
            .log-level-WARNING { color: #f59e0b; }
            .log-level-ERROR { color: #ef4444; }
            .log-level-SUCCESS { color: #10b981; }
            
            .logging-modal-footer {
                padding: 1rem 1.5rem;
                border-top: 2px solid #e5e7eb;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #f8fafc;
                border-radius: 0 0 16px 16px;
            }
        `;
        document.head.appendChild(style);
    }
}

function hideRealTimeLogging() {
    const modal = document.getElementById('loggingModal');
    if (modal) {
        modal.remove();
    }
    
    // Close log stream if open
    if (window.logEventSource) {
        window.logEventSource.close();
        window.logEventSource = null;
    }
}

function connectToLogStream() {
    // Close existing connection if any
    if (window.logEventSource) {
        window.logEventSource.close();
    }
    
    // Create new EventSource connection
    window.logEventSource = new EventSource('/api/logs');
    
    window.logEventSource.onmessage = function(event) {
        try {
            const logData = JSON.parse(event.data);
            
            if (logData.type === 'ping') {
                // Ignore ping messages
                return;
            }
            
            appendLogEntry(logData);
            
        } catch (error) {
            console.error('Error parsing log data:', error);
        }
    };
    
    window.logEventSource.onerror = function(event) {
        console.log('Log stream connection error:', event);
        
        // Check if collection is complete
        setTimeout(() => {
            if (window.logEventSource && window.logEventSource.readyState === EventSource.CLOSED) {
                onCollectionComplete();
            }
        }, 2000);
    };
    
    window.logEventSource.onopen = function(event) {
        console.log('Log stream connected');
        updateProgressText('Connected to log stream...');
    };
}

function appendLogEntry(logData) {
    const logOutput = document.getElementById('logOutput');
    if (!logOutput) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-level-${logData.level}`;
    
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    timestamp.textContent = `[${logData.timestamp}] `;
    
    const message = document.createElement('span');
    message.textContent = logData.message;
    
    logEntry.appendChild(timestamp);
    logEntry.appendChild(message);
    logOutput.appendChild(logEntry);
    
    // Auto-scroll to bottom
    logOutput.scrollTop = logOutput.scrollHeight;
    
    // Update progress text based on message
    if (logData.message.includes('completed!') || logData.message.includes('process completed')) {
        updateProgressText('Data collection completed!');
        onCollectionComplete();
    } else if (logData.message.includes('Step')) {
        updateProgressText(logData.message.split(':')[1] || logData.message);
    }
}

function updateProgressText(text) {
    const progressText = document.getElementById('progressText');
    if (progressText) {
        progressText.textContent = text;
    }
}

function onCollectionComplete() {
    // Hide spinner and show completion
    const spinner = document.querySelector('.spinner');
    const progressText = document.getElementById('progressText');
    const closeBtn = document.getElementById('closeLogsBtn');
    
    if (spinner) spinner.style.display = 'none';
    if (progressText) progressText.textContent = 'Data collection completed!';
    if (closeBtn) closeBtn.style.display = 'inline-block';
    
    // Close log stream
    if (window.logEventSource) {
        window.logEventSource.close();
        window.logEventSource = null;
    }
    
    // Show completion notification
    showNotification('Data collection completed successfully!', 'success');
    
    // Refresh dashboard data
    setTimeout(async () => {
        await loadDashboardData();
        showNotification('Dashboard refreshed with new data!', 'success');
    }, 2000);
}

function stopDataCollection() {
    if (window.logEventSource) {
        window.logEventSource.close();
        window.logEventSource = null;
    }
    
    hideRealTimeLogging();
    showNotification('Data collection stopped', 'info');
}

// ===== CHART FUNCTIONS =====
async function createKeywordFrequencyChart() {
    console.log('📊 Creating keyword frequency chart...');
    const ctx = document.getElementById('keywordFrequencyChart');
    if (!ctx) {
        console.error('❌ Canvas element "keywordFrequencyChart" not found');
        console.log('🔍 Available canvas elements:', document.querySelectorAll('canvas'));
        return;
    }
    console.log('✅ Canvas element found:', ctx);
    console.log('📏 Canvas dimensions:', ctx.width, 'x', ctx.height);
    console.log('👁️ Canvas visible:', ctx.offsetWidth, 'x', ctx.offsetHeight);
    
    // Destroy existing chart
    if (charts.keywordFrequency) {
        charts.keywordFrequency.destroy();
        console.log('🗑️ Destroyed existing keyword frequency chart');
    }
    
    try {
        console.log('🌐 Fetching keyword frequency data...');
        const response = await fetch(getCacheBustingUrl('/api/charts/keyword-frequency'));
        console.log('📡 Response status:', response.status);
        
        const chartData = await response.json();
        console.log('📊 Chart data received:', chartData);
        
        if (response.ok && chartData.labels && chartData.labels.length > 0) {
            // Apply keyword filter if active
            let filteredData = chartData;
            if (window.currentKeywordFilter) {
                const filterIndex = chartData.labels.indexOf(window.currentKeywordFilter);
                if (filterIndex !== -1) {
                    filteredData = {
                        labels: [chartData.labels[filterIndex]],
                        datasets: chartData.datasets.map(dataset => ({
                            ...dataset,
                            data: [dataset.data[filterIndex]]
                        }))
                    };
                } else {
                    // No data for this keyword
                    filteredData = {
                        labels: [window.currentKeywordFilter],
                        datasets: chartData.datasets.map(dataset => ({
                            ...dataset,
                            data: [0]
                        }))
                    };
                }
            }
            
            charts.keywordFrequency = new Chart(ctx, {
                type: 'bar',
                data: filteredData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: window.currentKeywordFilter ? 
                                  `Keyword Frequency - ${window.currentKeywordFilter}` : 
                                  'Keyword Frequency Across All Data Sources'
                        },
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } else {
            showChartError(ctx, 'No keyword frequency data available');
        }
    } catch (error) {
        console.error('Error creating keyword frequency chart:', error);
        showChartError(ctx, 'Failed to load keyword frequency data');
    }
}

async function createGoogleTrendsChart() {
    const ctx = document.getElementById('googleTrendsChart');
    if (!ctx) return;
    
    if (charts.googleTrends) {
        charts.googleTrends.destroy();
    }
    
    try {
        const response = await fetch(getCacheBustingUrl('/api/charts/google-trends'));
        const chartData = await response.json();
        
        if (response.ok && chartData.labels && chartData.labels.length > 0) {
            charts.googleTrends = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Google Trends Over Time'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        } else {
            showChartError(ctx, 'No Google Trends data available');
        }
    } catch (error) {
        console.error('Error creating Google Trends chart:', error);
        showChartError(ctx, 'Failed to load Google Trends data');
    }
}

async function createRedditEngagementChart() {
    const ctx = document.getElementById('redditEngagementChart');
    if (!ctx) return;
    
    if (charts.redditEngagement) {
        charts.redditEngagement.destroy();
    }
    
    try {
        const response = await fetch(getCacheBustingUrl('/api/charts/reddit-engagement'));
        const data = await response.json();
        
        if (response.ok && data.labels && data.labels.length > 0 && data.datasets) {
            charts.redditEngagement = new Chart(ctx, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Reddit Engagement by Keyword'
                        },
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } else {
            showChartError(ctx, 'No Reddit engagement data available');
        }
    } catch (error) {
        console.error('Error creating Reddit engagement chart:', error);
        showChartError(ctx, 'Failed to load Reddit engagement data');
    }
}

async function createYouTubePerformanceChart() {
    const ctx = document.getElementById('youtubePerformanceChart');
    if (!ctx) return;
    
    if (charts.youtubePerformance) {
        charts.youtubePerformance.destroy();
    }
    
    try {
        const response = await fetch(getCacheBustingUrl('/api/charts/youtube-engagement'));
        const data = await response.json();
        
        if (response.ok && data.labels && data.labels.length > 0 && data.datasets) {
            charts.youtubePerformance = new Chart(ctx, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'YouTube Performance by Keyword'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } else {
            showChartError(ctx, 'No YouTube performance data available');
        }
    } catch (error) {
        console.error('Error creating YouTube performance chart:', error);
        showChartError(ctx, 'Failed to load YouTube performance data');
    }
}

async function createTwitterEngagementChart() {
    console.log('📊 Creating Twitter engagement chart...');
    const ctx = document.getElementById('twitterEngagementChart');
    if (!ctx) {
        console.error('❌ Canvas element "twitterEngagementChart" not found');
        return;
    }
    console.log('✅ Canvas element found:', ctx);
    
    if (charts.twitterEngagement) {
        try {
            charts.twitterEngagement.destroy();
            delete charts.twitterEngagement;
        } catch (error) {
            console.warn('⚠️ Error destroying existing Twitter chart:', error);
        }
    }
    
    try {
        const response = await fetch('/api/twitter');
        const twitterData = await response.json();
        
        if (response.ok && twitterData.length > 0) {
            // Aggregate engagement data
            const totalLikes = twitterData.reduce((sum, tweet) => sum + (tweet.like_count || 0), 0);
            const totalRetweets = twitterData.reduce((sum, tweet) => sum + (tweet.retweet_count || 0), 0);
            const totalReplies = twitterData.reduce((sum, tweet) => sum + (tweet.reply_count || 0), 0);
            
            const chartData = {
                labels: ['Likes', 'Retweets', 'Replies'],
                datasets: [{
                    data: [totalLikes, totalRetweets, totalReplies],
                    backgroundColor: [
                        '#1da1f2',
                        '#17bf63',
                        '#ffad1f'
                    ],
                    borderWidth: 0
                }]
            };
            
            charts.twitterEngagement = new Chart(ctx, {
                type: 'doughnut',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Twitter Engagement Distribution'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        } else {
            showChartError(ctx, 'No Twitter engagement data available');
        }
    } catch (error) {
        console.error('Error creating Twitter engagement chart:', error);
        showChartError(ctx, 'Failed to load Twitter engagement data');
    }
}

// Helper function to show chart errors
function showChartError(ctx, message) {
    if (!ctx) {
        console.error('❌ Cannot show chart error: canvas element is null');
        return;
    }
    
    const container = ctx.parentElement;
    if (!container) {
        console.error('❌ Cannot show chart error: canvas parent element is null');
        return;
    }
    
    container.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 300px; color: #9ca3af; text-align: center;">
            <div>
                <i class="fas fa-chart-bar" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <p>${message}</p>
            </div>
        </div>
    `;
}

// ===== TRENDING KEYWORDS =====
function loadTrendingKeywords(data) {
    const container = document.getElementById('trendingKeywords');
    if (!container) return;
    
    if (!data || !data.trending_keywords || data.trending_keywords.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h4>No Trending Keywords Available</h4>
                <p>Run data collection to discover trending keywords from your sources.</p>
                <button class="btn btn-primary" onclick="showDataCollection()">
                    <i class="fas fa-play"></i>
                    Start Data Collection
                </button>
            </div>
        `;
        return;
    }
    
    const keywords = data.trending_keywords.slice(0, 10); // Show top 10
    
    container.innerHTML = keywords.map((kw, index) => `
        <div class="trending-keyword-card">
            <div class="keyword-rank">${index + 1}</div>
            <div class="keyword-content">
                <h4 class="keyword-text">${kw.keyword}</h4>
                <div class="keyword-details">
                    <span class="trending-score">Score: ${kw.trending_score}</span>
                    <span class="keyword-mentions">${kw.total_mentions} mentions</span>
                </div>
                <div class="keyword-sources">
                    ${Object.entries(kw.sources || {}).map(([source, count]) => 
                        `<span class="source-tag source-${source}">${source.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${count}</span>`
                    ).join('')}
                </div>
                ${kw.sentiment ? `
                    <div class="keyword-sentiment sentiment-${kw.sentiment.sentiment_label.toLowerCase()}">
                        ${kw.sentiment.sentiment_label}
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// ===== DASHBOARD DATA LOADING =====
async function loadDashboardData() {
    // Prevent multiple simultaneous loads
    if (isLoadingDashboard) {
        console.log('⏳ Dashboard loading already in progress, skipping...');
        return;
    }
    
    try {
        isLoadingDashboard = true;
        console.log('🔄 Loading dashboard data...');
        showLoading();
        
        // Destroy all existing charts first to prevent conflicts
        destroyAllCharts();
        
        // Load basic data first with cache-busting
        const [statsData, trendsData] = await Promise.all([
            fetch(getCacheBustingUrl('/api/stats')).then(r => r.json().catch(() => null)),
            fetch(getCacheBustingUrl('/api/trending')).then(r => r.json().catch(() => null))
        ]);
        
        console.log('📊 Stats data:', statsData);
        console.log('🔥 Trends data:', trendsData);
        
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js is not loaded!');
            showNotification('Chart.js library not loaded', 'error');
            hideLoading();
            return;
        }
        
        console.log('✅ Chart.js is available, version:', Chart.version);
        
        // Check if all chart canvas elements exist
        const chartElements = [
            'keywordFrequencyChart',
            'googleTrendsChart', 
            'redditEngagementChart',
            'youtubePerformanceChart',
            'twitterEngagementChart'
        ];
        
        console.log('🔍 Checking chart canvas elements...');
        chartElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                console.log(`✅ ${id}: Found (${element.offsetWidth}x${element.offsetHeight})`);
            } else {
                console.error(`❌ ${id}: Not found!`);
            }
        });
        
        // Create charts sequentially to avoid Chart.js ID conflicts
        try {
            console.log('📈 Creating charts sequentially...');
            
            // Longer delay to ensure destruction is complete
            await new Promise(resolve => setTimeout(resolve, 200));
            
            const chartFunctions = [
                { name: 'Keyword Frequency', func: createKeywordFrequencyChart },
                { name: 'Google Trends', func: createGoogleTrendsChart },
                { name: 'Reddit Engagement', func: createRedditEngagementChart },
                { name: 'YouTube Performance', func: createYouTubePerformanceChart },
                { name: 'Twitter Engagement', func: createTwitterEngagementChart }
            ];
            
            for (const { name, func } of chartFunctions) {
                try {
                    console.log(`🔄 Creating ${name} chart...`);
                    await func();
                    console.log(`✅ ${name} chart created successfully`);
                    // Longer delay between chart creations to prevent conflicts
                    await new Promise(resolve => setTimeout(resolve, 100));
                } catch (error) {
                    console.error(`❌ ${name} chart failed:`, error);
                }
            }
            
        } catch (chartError) {
            console.error('❌ Error creating charts:', chartError);
            showNotification('Some charts failed to load', 'warning');
        }
        
        // Load trending keywords
        loadTrendingKeywords(trendsData);
        
        // Load recent activity
        await loadRecentActivity();
        
        console.log('✅ Dashboard data loading completed');
        hideLoading();
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        hideLoading();
        showNotification('Failed to load dashboard data', 'error');
    } finally {
        isLoadingDashboard = false;
    }
}

// ===== RECENT ACTIVITY =====
async function loadRecentActivity() {
    try {
        const response = await fetch(getCacheBustingUrl('/api/recent-activity'));
        const activityData = await response.json();
        
        if (response.ok) {
            loadRecentReddit(activityData.reddit);
            loadRecentYouTube(activityData.youtube);
            loadRecentTwitter(activityData.twitter);
        } else {
            console.error('Failed to load recent activity data');
        }
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

function loadRecentReddit(data) {
    const container = document.getElementById('recentReddit');
    if (!container) return;
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="no-data">No Reddit data available</p>';
        return;
    }
    
    const posts = data.slice(0, 3); // Show latest 3
    
    container.innerHTML = posts.map(post => `
        <div class="activity-item">
            <h5>${(post.title || 'No title').substring(0, 60)}...</h5>
            <div class="activity-meta">
                <span>r/${post.subreddit || 'unknown'}</span>
                <span>${post.score || 0} points</span>
                <span>${post.num_comments || 0} comments</span>
            </div>
        </div>
    `).join('');
}

function loadRecentYouTube(data) {
    const container = document.getElementById('recentYoutube');
    if (!container) return;
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="no-data">No YouTube data available</p>';
        return;
    }
    
    const videos = data.slice(0, 3); // Show latest 3
    
    container.innerHTML = videos.map(video => `
        <div class="activity-item">
            <h5>${(video.title || 'No title').substring(0, 60)}...</h5>
            <div class="activity-meta">
                <span>${video.channel_title || 'Unknown channel'}</span>
                <span>${formatNumber(video.view_count || 0)} views</span>
                <span>${formatNumber(video.like_count || 0)} likes</span>
            </div>
        </div>
    `).join('');
}

function loadRecentTwitter(data) {
    const container = document.getElementById('recentTwitter');
    if (!container) return;
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="no-data">No Twitter data available</p>';
        return;
    }
    
    const tweets = data.slice(0, 3); // Show latest 3
    
    container.innerHTML = tweets.map(tweet => `
        <div class="activity-item">
            <h5>${(tweet.text || 'No text').substring(0, 60)}...</h5>
            <div class="activity-meta">
                <span>@${tweet.author_username || 'unknown'}</span>
                <span>${tweet.like_count || 0} likes</span>
                <span>${tweet.retweet_count || 0} retweets</span>
            </div>
        </div>
    `).join('');
}

// ===== UTILITY HELPER FUNCTIONS =====
function getChartColor(index, alpha = 1) {
    const colors = [
        `rgba(54, 162, 235, ${alpha})`,   // Bright blue
        `rgba(255, 99, 132, ${alpha})`,   // Bright red
        `rgba(75, 192, 192, ${alpha})`,   // Teal
        `rgba(255, 206, 86, ${alpha})`,   // Bright yellow
        `rgba(153, 102, 255, ${alpha})`,  // Purple
        `rgba(255, 159, 64, ${alpha})`,   // Orange
        `rgba(199, 199, 199, ${alpha})`,  // Gray
        `rgba(83, 102, 255, ${alpha})`,   // Indigo
        `rgba(255, 99, 255, ${alpha})`,   // Magenta
        `rgba(54, 235, 162, ${alpha})`    // Green
    ];
    return colors[index % colors.length];
}

function generateDateRange(days) {
    const dates = [];
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date);
    }
    return dates;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// ===== CHART EXPANSION =====
function expandChart(chartType) {
    // Create modal for expanded chart
    const modal = document.createElement('div');
    modal.className = 'chart-modal';
    modal.innerHTML = `
        <div class="chart-modal-content">
            <div class="chart-modal-header">
                <h3>${getChartTitle(chartType)}</h3>
                <button onclick="this.closest('.chart-modal').remove()">&times;</button>
            </div>
            <div class="chart-modal-body">
                <canvas id="expanded-${chartType}"></canvas>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Recreate chart in modal (simplified for demo)
    // In a real app, you'd clone the chart data
}

function getChartTitle(chartType) {
    const titles = {
        keywordFrequency: 'Keyword Frequency Analysis',
        googleTrends: 'Google Trends Analysis',
        redditEngagement: 'Reddit Engagement Metrics',
        youtubePerformance: 'YouTube Performance Dashboard',
        twitterEngagement: 'Twitter Engagement Analytics'
    };
    return titles[chartType] || 'Chart Analysis';
}

// ===== DATA FILTERING =====
function filterData() {
    const selectedKeyword = document.getElementById('keywordFilter').value;
    console.log('Filtering data by keyword:', selectedKeyword);
    
    // Filter charts based on selected keyword
    filterChartsByKeyword(selectedKeyword);
    
    // Filter recent activity based on keyword
    filterRecentActivityByKeyword(selectedKeyword);
    
    // Show notification
    if (selectedKeyword) {
        showNotification(`Filtered data for keyword: ${selectedKeyword}`, 'info');
    } else {
        showNotification('Showing all keywords', 'info');
    }
}

async function filterChartsByKeyword(keyword) {
    // This will re-create charts with filtered data
    try {
        // Store the current filter for use in chart creation
        window.currentKeywordFilter = keyword;
        
        // Recreate all charts with the filter applied
        await Promise.all([
            createKeywordFrequencyChart(),
            createGoogleTrendsChart(),
            createRedditEngagementChart(),
            createYouTubePerformanceChart(),
            createTwitterEngagementChart()
        ]);
        
    } catch (error) {
        console.error('Error filtering charts:', error);
    }
}

async function filterRecentActivityByKeyword(keyword) {
    // Filter the recent activity tables
    try {
        const response = await fetch('/api/recent-activity');
        const data = await response.json();
        
        if (!response.ok) return;
        
        // Filter data by keyword if specified
        let filteredData = data;
        if (keyword) {
            filteredData = {
                reddit: data.reddit?.filter(item => item.search_keyword === keyword) || [],
                youtube: data.youtube?.filter(item => item.search_keyword === keyword) || [],
                twitter: data.twitter?.filter(item => item.keyword === keyword) || []
            };
        }
        
        // Update the recent activity sections
        loadRecentReddit(filteredData);
        loadRecentYouTube(filteredData);
        loadRecentTwitter(filteredData);
        
    } catch (error) {
        console.error('Error filtering recent activity:', error);
    }
}

// ===== REFRESH FUNCTIONS =====
async function refreshData() {
    try {
        showLoading();
        showNotification('Refreshing dashboard data...', 'info');
        
        // Reload all dashboard data
        await loadDashboardData();
        
        // Refresh charts with current filter
        const currentFilter = window.currentKeywordFilter || '';
        if (currentFilter) {
            await filterChartsByKeyword(currentFilter);
        }
        
        hideLoading();
        showNotification('Dashboard refreshed successfully!', 'success');
        
    } catch (error) {
        console.error('Error refreshing data:', error);
        hideLoading();
        showNotification('Failed to refresh dashboard', 'error');
    }
}

async function refreshTrending() {
    try {
        showNotification('Refreshing trending analysis...', 'info');
        
        // Trigger trending analysis refresh with cache-busting
        const response = await fetch(getCacheBustingUrl('/api/trending'));
        const trendingData = await response.json();
        
        if (response.ok) {
            // Reload trending keywords if on dashboard
            if (document.getElementById('trendingKeywords')) {
                loadTrendingKeywords(trendingData);
            }
            showNotification('Trending analysis refreshed!', 'success');
        } else {
            throw new Error('Failed to refresh trending data');
        }
        
    } catch (error) {
        console.error('Error refreshing trending:', error);
        showNotification('Failed to refresh trending analysis', 'error');
    }
}

// ===== UPGRADE MODAL =====
function showUpgradeModal() {
    showNotification('Upgrade feature coming soon!', 'info');
}

// ===== DATA SOURCE FUNCTIONS =====
function showRedditData() {
    window.location.href = '/reddit';
}

function showYouTubeData() {
    window.location.href = '/youtube';
}

function showTwitterData() {
    window.location.href = '/twitter';
}

function showGoogleTrends() {
    window.location.href = '/google-trends';
}

function showTrendingAnalysis() {
    window.location.href = '/trending-analysis';
}

// ===== REAL-TIME LOGGING ENHANCEMENT =====
// Add real-time logging modal for data collection
function showRealTimeLogging() {
    // Create enhanced logging modal for better user experience
    const modal = document.createElement('div');
    modal.id = 'loggingModal';
    modal.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 5000;">
            <div style="background: white; border-radius: 16px; width: 90%; max-width: 800px; max-height: 80vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                <div style="padding: 1.5rem; border-bottom: 2px solid #e5e7eb; background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; border-radius: 16px 16px 0 0;">
                    <h3 style="margin: 0 0 1rem 0; font-size: 1.3rem;">Data Collection in Progress</h3>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div id="progressSpinner" style="width: 20px; height: 20px; border: 3px solid rgba(255, 255, 255, 0.3); border-top: 3px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                        <span id="progressText">Initializing...</span>
                    </div>
                </div>
                <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column;">
                    <div id="logOutput" style="flex: 1; padding: 1rem; overflow-y: auto; background: #0f172a; color: #e2e8f0; font-family: 'Courier New', monospace; font-size: 0.9rem; line-height: 1.4; max-height: 400px;"></div>
                </div>
                <div style="padding: 1rem 1.5rem; border-top: 2px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; border-radius: 0 0 16px 16px;">
                    <button onclick="stopDataCollection()" style="background: #6b7280; color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer;">Stop Collection</button>
                    <button onclick="hideRealTimeLogging()" id="closeLogsBtn" style="display: none; background: #1e3a8a; color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer;">Close</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Add spinner animation styles
    if (!document.getElementById('spinnerStyles')) {
        const style = document.createElement('style');
        style.id = 'spinnerStyles';
        style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
        document.head.appendChild(style);
    }
}

function hideRealTimeLogging() {
    const modal = document.getElementById('loggingModal');
    if (modal) modal.remove();
    if (window.logEventSource) {
        window.logEventSource.close();
        window.logEventSource = null;
    }
}

function connectToLogStream() {
    if (window.logEventSource) window.logEventSource.close();
    
    window.logEventSource = new EventSource('/api/logs');
    window.logEventSource.onmessage = function(event) {
        try {
            const logData = JSON.parse(event.data);
            if (logData.type !== 'ping') appendLogEntry(logData);
        } catch (error) {
            console.error('Error parsing log data:', error);
        }
    };
    
    window.logEventSource.onerror = function(event) {
        setTimeout(() => {
            if (window.logEventSource && window.logEventSource.readyState === EventSource.CLOSED) {
                onCollectionComplete();
            }
        }, 2000);
    };
}

function appendLogEntry(logData) {
    const logOutput = document.getElementById('logOutput');
    if (!logOutput) return;
    
    const logEntry = document.createElement('div');
    logEntry.style.marginBottom = '0.5rem';
    logEntry.style.padding = '0.25rem 0';
    logEntry.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
    
    const timestamp = document.createElement('span');
    timestamp.style.color = '#94a3b8';
    timestamp.style.fontSize = '0.8rem';
    timestamp.textContent = `[${logData.timestamp}] `;
    
    const message = document.createElement('span');
    message.textContent = logData.message;
    if (logData.level === 'ERROR' || logData.message.includes('ERROR:')) message.style.color = '#ef4444';
    else if (logData.level === 'WARNING' || logData.message.includes('WARNING:')) message.style.color = '#f59e0b';
    else if (logData.message.includes('SUCCESS:') || logData.message.includes('COMPLETED:')) message.style.color = '#10b981';
    
    logEntry.appendChild(timestamp);
    logEntry.appendChild(message);
    logOutput.appendChild(logEntry);
    logOutput.scrollTop = logOutput.scrollHeight;
    
    if (logData.message.includes('COMPLETED:') || logData.message.includes('process completed')) {
        document.getElementById('progressText').textContent = 'Data collection completed!';
        onCollectionComplete();
    } else if (logData.message.includes('STEP')) {
        document.getElementById('progressText').textContent = logData.message.split(':')[1] || logData.message;
    }
}

function onCollectionComplete() {
    const spinner = document.getElementById('progressSpinner');
    const closeBtn = document.getElementById('closeLogsBtn');
    if (spinner) spinner.style.display = 'none';
    if (closeBtn) closeBtn.style.display = 'inline-block';
    if (window.logEventSource) {
        window.logEventSource.close();
        window.logEventSource = null;
    }
    showNotification('Data collection completed successfully!', 'success');
    setTimeout(async () => {
        await loadDashboardData();
        showNotification('Dashboard refreshed with new data!', 'success');
    }, 2000);
}

function stopDataCollection() {
    if (window.logEventSource) {
        window.logEventSource.close();
        window.logEventSource = null;
    }
    hideRealTimeLogging();
    showNotification('Data collection stopped', 'info');
}

// ===== NOTIFICATION STYLES =====
const notificationCSS = `
.notification {
    position: fixed;
    top: 2rem;
    right: 2rem;
    z-index: 4000;
    max-width: 400px;
    border-radius: 12px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    animation: slideInRight 0.3s ease;
}

.notification-content {
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
    font-weight: 500;
}

.notification-success {
    background: linear-gradient(135deg, #059669, #10b981);
}

.notification-error {
    background: linear-gradient(135deg, #dc2626, #ef4444);
}

.notification-info {
    background: linear-gradient(135deg, #1e40af, #3b82f6);
}

.notification-content button {
    background: none;
    border: none;
    color: white;
    font-size: 1.25rem;
    cursor: pointer;
    margin-left: 1rem;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
`;

// Add notification styles to head
const style = document.createElement('style');
style.textContent = notificationCSS;
document.head.appendChild(style);

// Initialize dashboard with filters
async function initializeDashboard() {
    try {
        // Load initial data
        await loadDashboardData();
        
        // Set up chart refresh interval (every 5 minutes)
        setInterval(async () => {
            try {
                await loadDashboardData();
                console.log('Dashboard auto-refreshed');
            } catch (error) {
                console.error('Auto-refresh failed:', error);
            }
        }, 300000); // 5 minutes
        
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        showNotification('Dashboard initialization failed', 'error');
    }
}

// ===== KEYWORDS MANAGEMENT =====

async function initializeSettingsPage() {
    try {
        await loadKeywordsData();
        setupKeywordsEventListeners();
    } catch (error) {
        console.error('Error initializing settings page:', error);
        showNotification('Failed to load keywords settings', 'error');
    }
}

async function loadKeywordsData() {
    try {
        const response = await fetch(getCacheBustingUrl('/api/keywords'));
        const data = await response.json();
        
        if (response.ok) {
            displayKeywords(data.keywords);
            updateKeywordsStats(data);
        } else {
            throw new Error(data.error || 'Failed to load keywords');
        }
    } catch (error) {
        console.error('Error loading keywords:', error);
        showKeywordsError('Failed to load keywords');
    }
}

function displayKeywords(keywords) {
    const container = document.getElementById('keywordsContainer');
    const statsDiv = document.getElementById('keywordsStats');
    
    if (!container) return;
    
    if (!keywords || keywords.length === 0) {
        container.innerHTML = `
            <div class="keywords-empty">
                <div class="keywords-empty-icon">🔍</div>
                <p>No keywords configured</p>
                <small>Add your first keyword below to get started</small>
            </div>
        `;
        if (statsDiv) statsDiv.style.display = 'none';
        return;
    }
    
    const keywordsGrid = keywords.map(keyword => `
        <div class="keyword-tag">
            <span class="keyword-text">${escapeHtml(keyword)}</span>
            <button class="remove-keyword" onclick="removeKeyword('${escapeHtml(keyword)}')" title="Remove keyword">
                ×
            </button>
        </div>
    `).join('');
    
    container.innerHTML = `<div class="keywords-grid">${keywordsGrid}</div>`;
    
    if (statsDiv) {
        statsDiv.style.display = 'flex';
    }
}

function updateKeywordsStats(data) {
    const elements = {
        keywordCount: document.getElementById('keywordCount'),
        lastUpdated: document.getElementById('lastUpdated'),
        lastCollection: document.getElementById('lastCollection')
    };
    
    if (elements.keywordCount) {
        elements.keywordCount.textContent = `${data.count}/${data.max_keywords}`;
    }
    
    if (elements.lastUpdated && data.last_updated) {
        elements.lastUpdated.textContent = formatDateTime(data.last_updated);
    }
    
    if (elements.lastCollection && data.last_collection) {
        elements.lastCollection.textContent = formatDateTime(data.last_collection);
    }
}

function setupKeywordsEventListeners() {
    // Add keyword button
    const addBtn = document.getElementById('addKeywordBtn');
    const input = document.getElementById('newKeywordInput');
    
    if (addBtn && input) {
        addBtn.addEventListener('click', handleAddKeyword);
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleAddKeyword();
            }
        });
        
        // Real-time validation
        input.addEventListener('input', function() {
            validateKeywordInput(this.value);
        });
    }
    
    // Reset keywords button
    const resetBtn = document.getElementById('resetKeywordsBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', handleResetKeywords);
    }
    
    // Validate keywords button
    const validateBtn = document.getElementById('validateKeywordsBtn');
    if (validateBtn) {
        validateBtn.addEventListener('click', handleValidateKeywords);
    }
    
    // Manual collection button
    const collectBtn = document.getElementById('manualCollectBtn');
    if (collectBtn) {
        collectBtn.addEventListener('click', handleManualCollection);
    }
}

async function handleAddKeyword() {
    const input = document.getElementById('newKeywordInput');
    const btn = document.getElementById('addKeywordBtn');
    
    if (!input || !btn) return;
    
    const keyword = input.value.trim();
    if (!keyword) {
        showNotification('Please enter a keyword', 'warning');
        return;
    }
    
    // Disable button and show loading
    btn.disabled = true;
    btn.textContent = 'Adding...';
    
    try {
        const response = await fetch('/api/keywords/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showNotification(`Keyword "${keyword}" added successfully!`, 'success');
            input.value = '';
            await loadKeywordsData();
        } else {
            showNotification(result.message || 'Failed to add keyword', 'error');
        }
    } catch (error) {
        console.error('Error adding keyword:', error);
        showNotification('Failed to add keyword', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Add Keyword';
    }
}

async function removeKeyword(keyword) {
    if (!confirm(`Remove keyword "${keyword}"?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/keywords/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showNotification(`Keyword "${keyword}" removed successfully!`, 'success');
            await loadKeywordsData();
        } else {
            showNotification(result.message || 'Failed to remove keyword', 'error');
        }
    } catch (error) {
        console.error('Error removing keyword:', error);
        showNotification('Failed to remove keyword', 'error');
    }
}

async function handleResetKeywords() {
    if (!confirm('Reset all keywords to defaults? This will replace your current keywords.')) {
        return;
    }
    
    const btn = document.getElementById('resetKeywordsBtn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = '🔄 Resetting...';
    
    try {
        const response = await fetch('/api/keywords/reset', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showNotification('Keywords reset to defaults successfully!', 'success');
            await loadKeywordsData();
        } else {
            showNotification('Failed to reset keywords', 'error');
        }
    } catch (error) {
        console.error('Error resetting keywords:', error);
        showNotification('Failed to reset keywords', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Reset to Defaults';
    }
}

async function handleValidateKeywords() {
    const btn = document.getElementById('validateKeywordsBtn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = '✓ Validating...';
    
    try {
        const keywordsResponse = await fetch(getCacheBustingUrl('/api/keywords'));
        const keywordsData = await keywordsResponse.json();
        
        if (!keywordsResponse.ok) {
            throw new Error('Failed to get current keywords');
        }
        
        const response = await fetch('/api/keywords/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keywords: keywordsData.keywords })
        });
        
        const result = await response.json();
        
        if (response.ok && result.valid) {
            showNotification('All keywords are valid! ✅', 'success');
        } else {
            showNotification(result.message || 'Validation failed', 'warning');
        }
    } catch (error) {
        console.error('Error validating keywords:', error);
        showNotification('Failed to validate keywords', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '✓ Validate Current';
    }
}

async function handleManualCollection() {
    const btn = document.getElementById('manualCollectBtn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = '🚀 Starting Collection...';
    
    try {
        // Get current keywords first
        const keywordsResponse = await fetch(getCacheBustingUrl('/api/keywords'));
        const keywordsData = await keywordsResponse.json();
        
        if (!keywordsResponse.ok || !keywordsData.keywords || keywordsData.keywords.length === 0) {
            showNotification('No keywords configured for collection', 'warning');
            return;
        }
        
        // Get selected sources
        const sourceCheckboxes = document.querySelectorAll('input[name="sources"]:checked');
        const sources = Array.from(sourceCheckboxes).map(cb => cb.value);
        
        if (sources.length === 0) {
            showNotification('Please select at least one data source', 'warning');
            return;
        }
        
        showNotification(`Starting data collection for ${keywordsData.keywords.length} keywords from ${sources.length} sources...`, 'info');
        
        // Start collection
        const response = await fetch('/api/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keywords: keywordsData.keywords,
                sources: sources
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Data collection started! Check the dashboard for progress.', 'success');
            
            // Redirect to dashboard after a moment
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            showNotification(result.error || 'Failed to start collection', 'error');
        }
    } catch (error) {
        console.error('Error starting manual collection:', error);
        showNotification('Failed to start data collection', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Collect Data Now';
    }
}

function validateKeywordInput(value) {
    const input = document.getElementById('newKeywordInput');
    const btn = document.getElementById('addKeywordBtn');
    
    if (!input || !btn) return;
    
    const trimmed = value.trim();
    const isValid = trimmed.length >= 2 && trimmed.length <= 50;
    
    btn.disabled = !isValid;
    
    if (trimmed.length > 0 && trimmed.length < 2) {
        input.style.borderColor = '#ef4444';
    } else if (trimmed.length > 50) {
        input.style.borderColor = '#ef4444';
    } else if (trimmed.length >= 2) {
        input.style.borderColor = '#10b981';
    } else {
        input.style.borderColor = '#e2e8f0';
    }
}

function showKeywordsError(message) {
    const container = document.getElementById('keywordsContainer');
    if (container) {
        container.innerHTML = `
            <div class="keywords-empty">
                <div class="keywords-empty-icon">⚠️</div>
                <p>Error loading keywords</p>
                <small>${escapeHtml(message)}</small>
                <br><br>
                <button class="btn btn-outline" onclick="loadKeywordsData()">🔄 Retry</button>
            </div>
        `;
    }
}

function formatDateTime(isoString) {
    try {
        const date = new Date(isoString);
        return date.toLocaleString();
    } catch (error) {
        return 'Invalid date';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Call initialization when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 DOM loaded, checking for chart elements...');
    
    // Check if we're on the dashboard page
    const chartElements = [
        'keywordFrequencyChart',
        'googleTrendsChart', 
        'redditEngagementChart',
        'youtubePerformanceChart',
        'twitterEngagementChart'
    ];
    
    let foundElements = 0;
    chartElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            foundElements++;
            console.log(`✅ Found chart element: ${id}`);
        } else {
            console.log(`❌ Missing chart element: ${id}`);
        }
    });
    
    console.log(`📊 Found ${foundElements}/${chartElements.length} chart elements`);
    
    if (foundElements > 0) {
        console.log('🚀 Initializing dashboard...');
        initializeDashboard();
    } else {
        console.log('⚠️ No chart elements found - not on dashboard page or elements not loaded');
    }
}); 