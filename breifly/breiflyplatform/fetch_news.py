import asyncio
from crawl4ai import AsyncWebCrawler
from .news_filter import filter_news

# Map period to corresponding URL parameter
def get_period_param(period):
    period_map = {
        "1": "",               # Anytime (no parameter needed)
        "2": "when%3A1h",      # Past hour
        "3": "when%3A1d",      # Past 24 hours
        "4": "when%3A7d",      # Past week
        "5": "when%3A1y",      # Past year
    }
    return period_map.get(period, None)

# Search news
async def search_news(keywords, period_param, publishers):
    # Split keywords and join with '%20' for URL formatting
    formatted_keywords = "%20".join(keywords.split()) if keywords else ""

    # Format publishers for the URL if provided
    formatted_publishers = f"site%3A{publishers}" if publishers else ""

    # Combine keywords and publishers if both are provided
    query = " ".join(filter(None, [formatted_keywords, formatted_publishers]))

    # Build the URL
    if period_param:
        url = f"https://news.google.com/search?q={query}%20{period_param}&hl=en-US&gl=US&ceid=US%3Aen"
    else:
        url = f"https://news.google.com/search?q={query}&hl=en-US&gl=US&ceid=US%3Aen"

    print(f"Generated URL: {url}")  # For debugging purposes

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        # Parse and filter articles
        articles = filter_news(result.markdown)

        # Return the extracted articles
        return [
            {
                "title": item.get("title", "(No Title)"),
                "link": item.get("link", ""),
                "date": item.get("date", ""),
                "publisher": item.get("publisher", "(No Publisher)"),
                "image": item.get("image", "")  # Extract image URL if available
            }
            for item in articles
        ]
