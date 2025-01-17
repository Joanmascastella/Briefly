import asyncio
from crawl4ai import AsyncWebCrawler
from .filter_news import filter_news  # Adjust the import path as necessary
from django.http import JsonResponse

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
async def search_news(keywords, period_param, publishers=None):
    """
    Fetch news articles based on keywords, time period, and publishers.

    Args:
        keywords (str): Keywords to search for.
        period_param (str): Time period parameter for filtering.
        publishers (list): List of publishers to filter results (optional).

    Returns:
        list: Parsed and filtered news articles.
    """
    # Format keywords and publishers for URL
    formatted_keywords = "%20".join(keywords.split())
    formatted_publishers = "%20".join(publishers) if publishers else ""

    # Build the URL based on inputs
    if period_param and publishers:
        url = f"https://news.google.com/search?q={formatted_keywords}%20site%3A{formatted_publishers}%20{period_param}&hl=en-US&gl=US&ceid=US%3Aen"
    elif period_param:
        url = f"https://news.google.com/search?q={formatted_keywords}%20{period_param}&hl=en-US&gl=US&ceid=US%3Aen"
    elif publishers:
        url = f"https://news.google.com/search?q={formatted_keywords}%20site%3A{formatted_publishers}&hl=en-US&gl=US&ceid=US%3Aen"
    else:
        url = f"https://news.google.com/search?q={formatted_keywords}&hl=en-US&gl=US&ceid=US%3Aen"

    print(f"Generated URL: {url}")  # Debugging purposes

    # Fetch results asynchronously
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        # Parse and filter articles
        articles = filter_news(result.markdown)

        return articles

# Django view
async def get_news(request):
    if request.method == "GET":
        keywords = request.GET.get('keywords', '')
        period = request.GET.get('period', '1')  # Default to "Anytime"
        period_param = get_period_param(period)
        publishers = request.GET.getlist('publishers', [])

        if not keywords:
            return JsonResponse({'error': 'Keywords are required'}, status=400)

        if period_param is None:
            return JsonResponse({'error': 'Invalid time period selected'}, status=400)

        # Call the async search_news function
        articles = await search_news(keywords, period_param, publishers)

        return JsonResponse({'articles': articles}, safe=False)

    return JsonResponse({'error': 'Invalid request method'}, status=400)