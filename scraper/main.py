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
from pydantic import BaseModel, ValidationError
from typing import Optional

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/GSaikowshik)"
TIMEOUT_SECONDS = 10
DELAY_SECONDS = 0.5  

class BookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: Optional[str]
    description: Optional[str]
    source_page: str
    fetched_at: str

def fetch_and_cache(url: str, cache_filepath: str, stats: dict) -> Optional[str]:
    """Fetches a page smartly, utilizing cache, and retrying on 5xx errors."""
    if os.path.exists(cache_filepath):
        stats["cache_hits"] += 1
        with open(cache_filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    stats["pages_fetched"] += 1
    print(f"FETCH: {url}")
    time.sleep(DELAY_SECONDS)
    
    headers = {"User-Agent": USER_AGENT}
    
    for attempt in range(2): 
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                html = response.text
                with open(cache_filepath, "w", encoding="utf-8") as f:
                    f.write(html)
                return html
                
            elif response.status_code in (403, 404):
                print(f"Skipped {url} (Status: {response.status_code}) - No retry allowed.")
                return None
                
            elif response.status_code >= 500:
                print(f"Server error {response.status_code}. Retrying...")
            else:
                print(f"Failed {url} with status {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Network error on {url}: {e}. Retrying...")
            
        if attempt == 0:
            time.sleep(2) 
            
    return None 

def main():
    start_time = datetime.now(timezone.utc)
    stats = {
        "start_time": start_time.isoformat(),
        "duration_seconds": 0.0,
        "pages_fetched": 0,
        "cache_hits": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "failed_pages": 0
    }
    
    os.makedirs("cache", exist_ok=True)
    os.makedirs("output", exist_ok=True)
 
    current_url = "https://books.toscrape.com/catalogue/page-1.html"
    pages_visited = 0
    book_urls = []
    
    print("Discovering catalogue pages...")
    while current_url and pages_visited < 3:
        page_name = current_url.split("/")[-1]
        cache_file = f"cache/catalogue-{page_name}"
        
        html = fetch_and_cache(current_url, cache_file, stats)
        if not html:
            break
            
        pages_visited += 1
        soup = BeautifulSoup(html, "html.parser")
        
        for article in soup.select(".product_pod"):
            link = article.select_one("h3 a")
            if link:
                book_urls.append(urljoin(current_url, link.get("href")))
        
        next_button = soup.select_one(".next a")
        current_url = urljoin(current_url, next_button.get("href")) if next_button else None

    unique_urls = list(set(book_urls))
    

    unique_urls.append("https://books.toscrape.com/catalogue/fake-book-url/index.html")
 
    print("\nExtracting detail pages...")
    raw_records = []
    
    for book_url in unique_urls:
        book_id = book_url.split("/")[-2] if len(book_url.split("/")) >= 2 else "unknown"
        cache_file = f"cache/book-{book_id}.html"
        
        html = fetch_and_cache(book_url, cache_file, stats)
        if not html:
            stats["failed_pages"] += 1
            continue 
            
        soup = BeautifulSoup(html, "html.parser")
        
        title_el = soup.select_one("h1")
        price_el = soup.select_one("p.price_color")
        avail_el = soup.select_one("p.instock.availability")
        desc_el = soup.select_one("#product_description ~ p")
        rating_el = soup.select_one("p.star-rating")
        
        raw_records.append({
            "title": title_el.text if title_el else None,
            "product_url": book_url,
            "price_text": price_el.text if price_el else None,
            "availability_text": avail_el.text.strip() if avail_el else None,
            "rating_text": rating_el["class"][1] if rating_el and len(rating_el.get("class", [])) > 1 else None,
            "description": desc_el.text if desc_el else None,
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "fetched_at": datetime.now(timezone.utc).isoformat()
        })

    valid_books, errors = [], []
    for raw in raw_records:
        try:
            raw_price = raw.get("price_text", "")
            raw["price_gbp"] = float(raw_price.replace("£", "").replace("Â", "").strip()) if raw_price else 0.0
            valid_books.append(BookRecord(**raw).model_dump())
        except Exception as e:
            errors.append({"url": raw.get("product_url"), "error": str(e)})
            
    stats["valid_records"] = len(valid_books)
    stats["invalid_records"] = len(errors)
    stats["duration_seconds"] = round((datetime.now(timezone.utc) - start_time).total_seconds(), 2)

    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_books, f, indent=2)
    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2)
    with open("output/run-report.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print(f"\nDone! Valid: {stats['valid_records']} | Failed pages: {stats['failed_pages']}")

if __name__ == "__main__":
    main()