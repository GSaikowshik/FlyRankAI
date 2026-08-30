"""
The Polite Scraper - Week 5 Assignment A9
A polite scraping pipeline for Books to Scrape.
"""
import os
import time
import requests
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime, timezone

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/GSaikowshik)"
TIMEOUT_SECONDS = 10
DELAY_SECONDS = 0.5  # Polite delay between network requests

def fetch_and_cache(url: str, cache_filepath: str) -> str:
    """Fetches a page from the cache if it exists, otherwise from the network."""
    if os.path.exists(cache_filepath):
        with open(cache_filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    print(f"FETCH: {url}")
    # Wait at least half a second between real requests to the site
    time.sleep(DELAY_SECONDS)
    
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}. Status code: {response.status_code}")
        
    html = response.text
    
    with open(cache_filepath, "w", encoding="utf-8") as f:
        f.write(html)
        
    return html

def main():
    os.makedirs("cache", exist_ok=True)
    
    # --- Stage 2: Discover three catalogue pages ---
    current_url = "https://books.toscrape.com/catalogue/page-1.html"
    pages_visited = 0
    book_urls = []
    
    print("Discovering catalogue pages...")
    while current_url and pages_visited < 3:
        page_name = current_url.split("/")[-1]
        cache_file = f"cache/catalogue-{page_name}"
        
        html = fetch_and_cache(current_url, cache_file)
        pages_visited += 1
        
        soup = BeautifulSoup(html, "html.parser")
        
        for article in soup.select(".product_pod"):
            link = article.select_one("h3 a")
            if link:
                relative_url = link.get("href")
                absolute_url = urljoin(current_url, relative_url)
                book_urls.append(absolute_url)
        
        next_button = soup.select_one(".next a")
        if next_button:
            next_relative = next_button.get("href")
            current_url = urljoin(current_url, next_relative)
        else:
            current_url = None

    unique_urls = list(set(book_urls))
    
    print(f"catalogue_pages = {pages_visited}")
    print(f"discovered = {len(book_urls)}")
    print(f"unique_urls = {len(unique_urls)}\n")

    # --- Stage 3: Extract the raw records ---
    print("Extracting detail pages...")
    raw_records = []
    
    for book_url in unique_urls:
        book_id = book_url.split("/")[-2]
        cache_file = f"cache/book-{book_id}.html"
        
        html = fetch_and_cache(book_url, cache_file)
        soup = BeautifulSoup(html, "html.parser")
        
        title_el = soup.select_one("h1")
        price_el = soup.select_one("p.price_color")
        avail_el = soup.select_one("p.instock.availability")
        desc_el = soup.select_one("#product_description ~ p")
        rating_el = soup.select_one("p.star-rating")
        
        record = {
            "title": title_el.text if title_el else None,
            "product_url": book_url,
            "price_text": price_el.text if price_el else None,
            "availability_text": avail_el.text.strip() if avail_el else None,
            "rating_text": rating_el["class"][1] if rating_el and len(rating_el.get("class", [])) > 1 else None,
            "description": desc_el.text if desc_el else None,
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        raw_records.append(record)

    print(f"\ndetail_pages = {len(raw_records)}")
    if raw_records:
        print("Sample raw record:")
        print(json.dumps(raw_records[0], indent=2))

if __name__ == "__main__":
    main()