"""
The Polite Scraper - Week 5 Assignment A9
A polite scraping pipeline for Books to Scrape.
"""
import os
import requests

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/GSaikowshik)"
TIMEOUT_SECONDS = 10

def fetch_and_cache(url: str, cache_filepath: str) -> str:
    """Fetches a page from the cache if it exists, otherwise from the network."""
    
    if os.path.exists(cache_filepath):
        print(f"CACHE HIT: {cache_filepath}")
        with open(cache_filepath, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"Response size: {len(html)} bytes")
        return html
    
    print(f"FETCH: {url}")
    headers = {"User-Agent": USER_AGENT}
    
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}. Status code: {response.status_code}")
        
    html = response.text
    
    with open(cache_filepath, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Response size: {len(html)} bytes")
    return html

def main():
    os.makedirs("cache", exist_ok=True)
    
    target_url = "https://books.toscrape.com/catalogue/page-1.html"
    cache_file = "cache/catalogue-page-1.html"
    
    html = fetch_and_cache(target_url, cache_file)

if __name__ == "__main__":
    main()