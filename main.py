import asyncio
from crawl4ai import AsyncWebCrawler
from filter import filter_news

# Get user input for keywords
def input_keywords():
    inputs = input("Hi, please enter the keywords of news you want to search for (e.g., 'semiconductor news'): ")
    return inputs.strip()

# Get user input for time period
def time_period():
    period = input(
        "Please enter the time period you want to search for the news\n"
        "Available options:\n"
        "1: 'Anytime'\n"
        "2: 'Past Hour'\n"
        "3: 'Past 24 Hours'\n"
        "4: 'Past Week'\n"
        "5: 'Past Year'\n"
        "Enter the number corresponding to your choice: "
    )
    return period.strip()

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
async def search_news(keywords, period_param):
    # Split keywords and join with '%20' for URL formatting
    formatted_keywords = "%20".join(keywords.split())
    # Build the URL
    if period_param:
        url = f"https://news.google.com/search?q={formatted_keywords}%20{period_param}&hl=en-US&gl=US&ceid=US%3Aen"
    else:
        url = f"https://news.google.com/search?q={formatted_keywords}&hl=en-US&gl=US&ceid=US%3Aen"

    print(f"Generated URL: {url}")  # For debugging purposes

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        # Parse and filter articles
        articles = filter_news(result.markdown)

        # Display the extracted articles
        for idx, item in enumerate(articles, start=1):
            title = item.get('title', '(No Title)')
            link = item.get('link', '')
            date = item.get('date', '')
            publisher = item.get('publisher', '(No Publisher)')
            print(f"--- Article #{idx} ---")
            print(f"Title:     {title}")
            print(f"Link:      {link}")
            print(f"Date:      {date}")
            print(f"Publisher: {publisher}")
            print()

# Main function to orchestrate the search
async def main():
    keywords = input_keywords()
    period = time_period()
    period_param = get_period_param(period)

    if period_param is None:
        print("Invalid time period selection. Please try again.")
    else:
        print(f"Searching for '{keywords}' in the selected time period...")
        await search_news(keywords, period_param)

# Run the program
if __name__ == "__main__":
    asyncio.run(main())