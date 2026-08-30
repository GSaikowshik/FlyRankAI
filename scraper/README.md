# The Polite Scraper (Books to Scrape)

A polite, robust web scraping pipeline that extracts book data from the first three catalogue pages of Books to Scrape, normalizes and validates the records, handles errors gracefully, and generates a structured run report.

## Target Classification
* **Target Site:** `https://books.toscrape.com`
* **Purpose & Permission:** Books to Scrape is an official sandbox website built specifically for testing and practicing web scraping.
* **Scope:** Exactly the first 3 catalogue pages (60 books total).
* **Data Collected:** Title, product URL, raw price, numeric price (GBP), availability status, star rating, description, source page, and fetch timestamp.
* **Robots.txt Check:** Requesting `https://books.toscrape.com/robots.txt` returns `404 Not Found` (no robots file found).
* **Pledge:** I will not reuse this code on another site without checking its rules and terms first.