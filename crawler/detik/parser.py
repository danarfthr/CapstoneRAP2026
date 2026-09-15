import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from config import config, logger

def normalize_spaces(text: str) -> str:
    """Removes extra whitespaces and newlines."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def is_noise_paragraph(text: str) -> bool:
    """
    Checks if a paragraph is an injected advertisement or UI boilerplate.
    Uses the noise_paragraphs list defined in config.py.
    """
    normalized = normalize_spaces(text).upper()
    if not normalized:
        return True
        
    for noise_marker in config.noise_paragraphs:
        if normalized == noise_marker or normalized.startswith("ADVERTIS"):
            return True
    return False

def contains_keywords(text: str) -> bool:
    """
    Evaluates if the article text contains any of the target energy keywords.
    Uses word-boundary regex to prevent partial matches (e.g., matching "Uap" but not "Suap").
    """
    if not text:
        return False
        
    text_lower = text.lower()
    for keyword in config.target_keywords:
        # Use regex boundary \b to match exact phrases/words
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False

def extract_article_date(soup: BeautifulSoup) -> str:
    """Attempts to extract the publication date from Detik's metadata."""
    # Detik usually stores the date in meta tags or specific div classes
    meta_date = soup.find('meta', {'name': 'publishdate'})
    if meta_date and meta_date.get('content'):
        return meta_date['content']
    
    # Fallback to visual date div
    date_div = soup.find('div', class_='detail__date')
    if date_div:
        return normalize_spaces(date_div.get_text())
        
    return ""

def parse_article_html(html: str, url: str) -> Optional[Dict]:
    """
    Parses the raw HTML of a Detik article.
    Returns a dictionary of article data IF it matches the target keywords.
    Returns None if the article is irrelevant or empty.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Extract Title
    meta_title = soup.find('meta', property='og:title')
    h1_title = soup.find('h1')
    
    if meta_title and meta_title.get('content'):
        title = meta_title['content']
    elif h1_title:
        title = h1_title.get_text()
    else:
        title = soup.title.get_text() if soup.title else url
        
    title = normalize_spaces(title)

    # 2. Extract Body Text using fallback selectors
    body_selectors = [
        ".detail__body-text p",
        ".detail__body-text",
        ".itp_bodycontent p",
        ".itp_bodycontent",
        "article p",
    ]
    
    paragraphs = []
    for selector in body_selectors:
        elements = soup.select(selector)
        if elements:
            for el in elements:
                text = normalize_spaces(el.get_text())
                if not is_noise_paragraph(text):
                    paragraphs.append(text)
            break # Stop if we found the body container
            
    # Fallback to meta description if body is entirely empty
    if not paragraphs:
        meta_desc = soup.find('meta', property='og:description')
        if meta_desc and meta_desc.get('content'):
            paragraphs.append(normalize_spaces(meta_desc['content']))

    full_body = "\n\n".join(paragraphs)

    # 3. Filter check: Does this article mention PLTN/PLTU?
    # We check both the title and the body
    combined_text = f"{title} {full_body}"
    if not contains_keywords(combined_text):
        return None # Discard irrelevant article

    # 4. Extract Tags
    tags = []
    for tag_link in soup.select('a[href*="/tag/"]'):
        tag_text = normalize_spaces(tag_link.get_text())
        if tag_text and tag_text not in tags:
            tags.append(tag_text)

    # 5. Extract Date
    published_date = extract_article_date(soup)

    # Return structured data
    return {
        "url": url,
        "title": title,
        "date": published_date,
        "body": full_body,
        "tags": tags
    }

def parse_search_results(html: str) -> List[str]:
    """
    Extracts article URLs from Detik's search result pages.
    Useful for the Option B Strategy (Search Crawl).
    """
    soup = BeautifulSoup(html, "html.parser")
    article_urls = []
    
    # Detik search results usually wrap articles in standard article tags or list items
    links = soup.select("article a[href], .list-berita a[href]")
    
    for link in links:
        href = link.get('href')
        if href and re.search(r'/d-\d+', href): # Ensure it's an actual news article link
            if href not in article_urls:
                article_urls.append(href)
                
    return article_urls