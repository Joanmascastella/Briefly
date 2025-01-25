import re

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
    Extracts the article title, link, date, publisher, and image from the given text.
    Returns a list of dicts, each with keys: title, link, date, publisher, image.
    Any article whose title is in EXCLUDED_TITLES will be omitted.
    """
    lines = text.splitlines()
    pattern_article = re.compile(r'^\[(.+)\]\((.+)\)')  # e.g. [Article Title](link)
    pattern_img = re.compile(r'^!\[.*\]\((.+)\)')       # e.g. ![Alt Text](image URL)
    pattern_date = re.compile(
        r'^\b((?:\d{1,2}\s\w+\s\d{4})|(?:\d+\s+days\s+ago)|(?:Yesterday)|(?:Today)|(?:\w+\s\d{1,2},\s\d{4})|(?:\d+\s+minutes\s+ago)|(?:\d+\s+hours\s+ago))\b',
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

            # Clean the URL:
            # - Remove <./ at any position
            # - Remove > at the end
            url = match_article.group(2)
            url = url.replace("<./", "")  # Remove <./ wherever it occurs
            url = url.rstrip(">")         # Remove trailing >
            current_item['link'] = url

            # Look for the date exactly two lines below the title
            if i + 2 < len(lines):
                potential_date = lines[i + 2].strip()
                if pattern_date.match(potential_date):
                    current_item['date'] = potential_date

            i += 1
            continue

        # 2) Match an image: ![Alt Text](Image URL)
        match_img = pattern_img.match(line)
        if match_img:
            current_item['image'] = match_img.group(1)
            i += 1
            continue

        # 3) Check for the publisher above "More"
        if line == "More":
            # The publisher should be in the previous non-empty line
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0:
                current_item['publisher'] = lines[j].strip()

            i += 1
            continue

        # 4) Catch any additional publisher lines
        if (line
                and not pattern_img.match(line)
                and not pattern_article.match(line)
                and 'date' in current_item
                and 'publisher' not in current_item):
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