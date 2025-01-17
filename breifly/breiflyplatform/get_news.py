from crawl4ai import AsyncWebCrawler as crawler
from filter_news import filter_news

# Search news
def search_news(keywords, period_param=None, publishers=None):
    """
    Search for news articles on Google News using specified keywords, time period, and publishers.

    Args:
        keywords (list): List of keywords for the search.
        period_param (str, optional): Time period parameter (e.g., "1d" for 1 day).
        publishers (list, optional): List of publishers to filter by.

    Returns:
        list: Filtered articles.
    """
    # Format keywords and publishers for URL
    formatted_keywords = "%20".join(keywords)
    formatted_publishers = "%20".join(publishers) if publishers else ""

    # Build the URL
    if period_param and publishers:
        url = f"https://news.google.com/search?q={formatted_keywords}%20site%3A{formatted_publishers}%20when%3A{period_param}&hl=en-US&gl=US&ceid=US%3Aen"
    elif period_param:
        url = f"https://news.google.com/search?q={formatted_keywords}%20when%3A{period_param}&hl=en-US&gl=US&ceid=US%3Aen"
    elif publishers:
        url = f"https://news.google.com/search?q={formatted_keywords}%20site%3A{formatted_publishers}&hl=en-US&gl=US&ceid=US%3Aen"
    else:
        url = f"https://news.google.com/search?q={formatted_keywords}&hl=en-US&gl=US&ceid=US%3Aen"

    print(f"Generated URL: {url}")

    # Crawl the URL
    result = crawler.arun(url=url)

    # Parse and filter articles
    articles = filter_news(result.markdown)

    return articles
