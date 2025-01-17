from django.shortcuts import render, redirect
from django.http import JsonResponse
from .supabase_client import supabase
import asyncio
import re
from crawl4ai import AsyncWebCrawler

# We define a set of titles we want to exclude from the final output
EXCLUDED_TITLES = {
    "News",
    "Sign in",
    "Home",
    "News Showcase",
    "U.S.",
    "World",
    "Local",
    "Business",
    "Technology",
    "Entertainment",
    "Sports",
    "Science",
    "Health",
}


def filter_news(text: str):
    """
    Extracts the article title, link, date, and publisher from the given text.
    Returns a list of dicts, each with keys: title, link, date, publisher.
    Any article whose title is in EXCLUDED_TITLES will be omitted.
    """
    lines = text.splitlines()
    pattern_article = re.compile(r'^\[(.+)\]\((.+)\)')  # e.g. [Article Title](link)
    pattern_img = re.compile(r'^!\[.*\]\(.*\)')
    pattern_date = re.compile(
        r'^\b((?:\d{1,2}\s\w+\s\d{4})|(?:\d+\s+days\s+ago)|(?:Yesterday)|(?:Today)|(?:\w+\s\d{1,2},\s\d{4}))\b',
        re.IGNORECASE
    )

    articles = []
    current_item = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 1) Match an article title + link: [Title](URL)
        match_article = pattern_article.match(line)
        if match_article:
            # If we already have an unfinished item, store it before creating a new one
            if 'title' in current_item:
                articles.append(current_item)
            current_item = {}
            current_item['title'] = match_article.group(1)
            current_item['link'] = match_article.group(2)

            i += 1
            continue

        # 2) Match date lines: "Yesterday", "3 days ago", "Sep 3, 2024", etc.
        match_date = pattern_date.match(line)
        if match_date:
            current_item['date'] = match_date.group(1)
            i += 1
            continue

        # 3) Potential publisher line:
        #    If line is non-empty, not an image, not bracketed, and we already have a date,
        #    treat it as publisher.
        if (line
                and not pattern_img.match(line)
                and not pattern_article.match(line)
                and 'date' in current_item
        ):
            current_item['publisher'] = line
            i += 1
            continue

        i += 1

    # If there's a leftover article in current_item, append it
    if 'title' in current_item:
        articles.append(current_item)

    # Now filter out articles whose title is in the excluded list
    filtered = []
    for art in articles:
        title = art.get('title', '').strip()
        if title not in EXCLUDED_TITLES:
            filtered.append(art)

    return filtered


async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://barcanewsnetwork.com/barcelona-will-ask-csd-for-a-precautionary-measure-to-register-their-two-players-today/"
        )

        # Parse and filter out excluded articles
        articles = filter_semiconductor_news(result.markdown)

        # Display the extracted articles (that are NOT excluded)
        for idx, item in enumerate(articles, start=1):
            title = item.get('title', '(No Title)')
            link = item.get('link', '')
            date = item.get('date', '')
            print(f"--- Article #{idx} ---")
            print(f"Title:     {title}")
            print(f"Link:      {link}")
            print(f"Date:      {date}")
            print()

        print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())

def get_access_token(request):
    access_token = request.session.get('access_token')
    user_authenticated = False
    user_data = None

    if access_token:
        try:
            # Fetch user data using the access token
            user_response = supabase.auth.get_user(access_token)

            if user_response.user:
                # If valid, mark the user as authenticated and fetch user details
                user_authenticated = True
                user_data = user_response.user  # Access the user object
            else:
                # If invalid, clear the session
                request.session.flush()
        except Exception as e:
            print(f"Error verifying token: {e}")
            request.session.flush()

    return user_authenticated, user_data

