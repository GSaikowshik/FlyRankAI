# The Polite Scraper (Books to Scrape)

A polite, robust web scraping pipeline that extracts book data from the first three catalogue pages of Books to Scrape. It normalizes and validates the records, handles errors gracefully, and generates a structured run report.

## Target Classification
* **Target Site:** `https://books.toscrape.com`
* **Purpose & Permission:** Books to Scrape is an official sandbox website built specifically for testing and practicing web scraping.
* **Scope:** Exactly the first 3 catalogue pages (60 books total).
* **Robots.txt Check:** Requesting `https://books.toscrape.com/robots.txt` returns `404 Not Found` (no robots file found).
* **Pledge:** I will not reuse this code on another site without checking its rules and terms first.

## Installation & Run Instructions (Python Lane)
1. Install the required dependencies:
   ```bash
   pip install requests beautifulsoup4 pydantic
   ```
2. Run the scraper:
   ```bash
   python main.py
   ```

## Record Schema
Each valid record is validated using Pydantic before storage, ensuring this exact structure:
* `title` (string)
* `product_url` (string, absolute URL)
* `price_text` (string, raw text)
* `price_gbp` (float, cleaned numeric value)
* `availability_text` (string)
* `rating_text` (string, optional)
* `description` (string, optional)
* `source_page` (string, provenance URL)
* `fetched_at` (string, ISO timestamp)

## Politeness Rules
* **User-Agent:** Identifies the scraper and provides a GitHub contact link.
* **Delay:** Waits at least 0.5 seconds between real network requests.
* **Timeout:** Limits network requests to 10 seconds to avoid hanging indefinitely.
* **Cache:** Saves all fetched HTML locally. Subsequent runs read from the disk instead of querying the live server.
* **Failure Handling:** Retries 5xx server errors once, but immediately skips 404/403 responses without retrying. 

## Limitations & Ethics
* **Limitation:** This scraper relies on specific HTML class names (like `.product_pod`). If the website redesigns its layout, the selectors will break and need updating.
* **Browser Note:** This assignment required no browser automation (like Playwright) because all the necessary book data is directly available in the initial HTML document the server sends. Using a full browser would only add unnecessary memory and compute costs.
* **Ethics Note:** Always use an official API when one exists. Never bypass logins, paywalls, or blocks, and only collect the exact data you need.

## Run Report Evidence
```json
 {
  "start_time": "2026-08-30T16:43:40.257393+00:00",
  "duration_seconds": 2.86,
  "pages_fetched": 1,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```