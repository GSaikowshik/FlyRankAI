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
DELAY_SECONDS = 0.5  # Polite delay between network requests

# --- Stage 4: Pydantic Schema ---
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

def fetch_and_cache(url: str, cache_filepath: str) -> str:
    """Fetches a page from the cache if it exists, otherwise from the network."""
    if os.path.exists(cache_filepath):
        with open(cache_filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    print(f"FETCH: {url}")
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
    os.makedirs("output", exist_ok=True)
    
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
    
    # --- Stage 3: Extract the raw records ---
    print("\nExtracting detail pages...")
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

    # --- Stage 4: Clean, Validate, and Store ---
    print("\nValidating and storing records...")
    valid_books = []
    errors = []
    
    for raw in raw_records:
        try:
            # 1. Clean the price (remove £ and any weird encoding characters, turn into float)
            raw_price = raw.get("price_text", "")
            if raw_price:
                clean_string = raw_price.replace("£", "").replace("Â", "").strip()
                raw["price_gbp"] = float(clean_string)
            else:
                raw["price_gbp"] = 0.0
                
            # 2. Validate against schema
            valid_book = BookRecord(**raw)
            valid_books.append(valid_book.model_dump())
            
        except ValidationError as e:
            # 3. Bad records go to errors.json
            errors.append({"url": raw.get("product_url"), "error": str(e), "raw_data": raw})
        except Exception as e:
            errors.append({"url": raw.get("product_url"), "error": str(e), "raw_data": raw})
            
    # Write to files
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_books, f, indent=2)
        
    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2)
        
    print(f"Valid records saved to output/books.json: {len(valid_books)}")
    print(f"Errors saved to output/errors.json: {len(errors)}")

if __name__ == "__main__":
    main()