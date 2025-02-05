import feedparser
import urllib.parse

def search_news(keywords, period_param=None, publishers=None):
    """
    Fetch Google News results using RSS instead of Playwright.
    This method is compliant with Render's restrictions on headless browsing.
    """
    formatted_keywords = urllib.parse.quote_plus(keywords) if keywords else ""
    rss_url = f"https://news.google.com/rss/search?q={formatted_keywords}"

    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "date": entry.published,
            "publisher": entry.source.title if "source" in entry else "Unknown",
            "image": "",  # Google News RSS does not provide images
        })

    return articles