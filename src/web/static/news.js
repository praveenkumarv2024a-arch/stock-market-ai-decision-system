document.addEventListener('DOMContentLoaded', () => {
    const newsLoader = document.querySelector('.content-placeholder');
    const newsContainer = document.createElement('div');
    newsContainer.className = 'news-feed';
    newsContainer.style.maxWidth = '800px';
    newsContainer.style.margin = '0 auto';

    // Replace placeholder with container
    if (newsLoader) {
        newsLoader.parentNode.replaceChild(newsContainer, newsLoader);
    }

    function fetchNews() {
        newsContainer.innerHTML = '<div class="loading">Loading Global Market News...</div>';

        return fetch('/api/news?t=' + Date.now())
            .then(res => res.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                renderNews(data);
            })
            .catch(err => {
                newsContainer.innerHTML = `<div class="loading">Error loading news: ${err.message}</div>`;
            });
    }

    function renderNews(newsItems) {
        if (!newsItems || newsItems.length === 0) {
            newsContainer.innerHTML = '<div class="loading">No recent news found.</div>';
            return;
        }

        newsContainer.innerHTML = '';

        newsItems.forEach(item => {
            const card = document.createElement('div');
            card.className = 'news-item glass'; // Use glass class for styling
            card.style.marginBottom = '1.5rem';
            card.style.padding = '1.5rem';
            card.style.borderRadius = '1rem';

            // Sentiment Badge
            let sentimentClass = 'neutral';
            let sentimentText = 'Neutral';
            if (item.sentiment_score > 0.1) {
                sentimentClass = 'pos';
                sentimentText = 'Positive';
            } else if (item.sentiment_score < -0.1) {
                sentimentClass = 'neg';
                sentimentText = 'Negative';
            }

            const date = new Date(item.published).toLocaleString();

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <h3 style="margin:0 0 0.5rem 0;">
                        <a href="${item.link}" target="_blank" style="text-decoration:none; color:var(--text-primary);">${item.title}</a>
                    </h3>
                    <span class="sentiment-badge ${sentimentClass}" style="font-size:0.8rem; margin-left:10px; white-space:nowrap;">
                        ${sentimentText}
                    </span>
                </div>
                <div class="news-meta" style="margin-top:0.5rem; display:flex; justify-content:space-between;">
                    <span><i class="fa-solid fa-clock"></i> ${date}</span>
                    <span><i class="fa-solid fa-tag"></i> ${item.symbol || 'General'}</span>
                </div>
            `;

            newsContainer.appendChild(card);
        });
    }

    const refreshBtn = document.getElementById('refresh-news-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            const icon = refreshBtn.querySelector('i');
            if (icon) icon.classList.add('fa-spin');
            refreshBtn.disabled = true;

            // Trigger backend refresh first
            fetch('/api/news/refresh', { method: 'POST' })
                .then(res => res.json())
                .then(() => fetchNews()) // Fetch new data
                .catch(err => {
                    console.error("Manual refresh failed", err);
                    // Try to fetch anyway in case it was a partial success
                    fetchNews();
                })
                .finally(() => {
                    if (icon) icon.classList.remove('fa-spin');
                    refreshBtn.disabled = false;
                });
        });
    }

    fetchNews();

    // Auto refresh every 60s
    setInterval(fetchNews, 60000);
});
