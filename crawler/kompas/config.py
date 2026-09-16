import urllib.parse

SOURCE = "kompas"

SEARCH_SCHEMA = {
    "name": "kompas_search",
    "baseSelector": ".articleList .articleItem",
    "fields": [
        {"name": "title", "selector": ".articleTitle", "type": "text"},
        {"name": "url", "selector": "a.article-link", "type": "attribute",
         "attribute": "href"},
        {"name": "date", "selector": ".articlePost-date", "type": "text"},
        {"name": "kanal", "selector": ".articlePost-subtitle", "type": "text"},
        {"name": "lead", "selector": ".articleLead", "type": "text"},
    ],
}

ARTICLE_SCHEMA = {
    # Dicek di dua pola URL (baru & lama/xml) - keduanya diserve lewat
    # template yang sama sekarang, jadi selector-nya sama untuk semua tahun.
    # date_raw contoh: "Kompas.com, 5 April 2026, 06:30 WIB" - parse belakangan.
    "name": "kompas_article",
    "baseSelector": "body",
    "fields": [
        {"name": "title", "selector": "h1.read__title", "type": "text"},
        {"name": "date_raw", "selector": ".read__time", "type": "text"},
        {"name": "author", "selector": ".credit-title-nameEditor", "type": "text"},
        {"name": "content", "selector": ".read__content", "type": "text"},
    ],
}

ARTICLE_WAIT_FOR = "css:.read__content"

WAIT_FOR = "css:.articleItem"

def search_url(keyword: str, page: int, start_date: str = None,
                end_date: str = None) -> str:
    """start_date/end_date: "YYYY-MM-DD". Diverifikasi lewat form filter
    Kompas (?time=custom&start-date=...&end-date=...), yang redirect ke
    parameter asli start_date=/end_date= (underscore) di URL search."""
    q = urllib.parse.quote_plus(keyword)
    url = f"https://search.kompas.com/search?q={q}&site_id=all&page={page}"
    if start_date and end_date:
        url += f"&start_date={start_date}&end_date={end_date}"
    else:
        url += "&last_date=all"
    return url

def valid_artikel(u: str) -> bool:
    return ".kompas.com/read/" in (u or "")