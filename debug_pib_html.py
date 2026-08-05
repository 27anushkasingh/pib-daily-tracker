"""Debug script to inspect PIB website HTML structure."""

import requests
from bs4 import BeautifulSoup

url = "https://pib.gov.in/allRelease.aspx"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

response = requests.get(url, headers=headers, timeout=30)
print(f"Status Code: {response.status_code}\n")

soup = BeautifulSoup(response.content, "html.parser")

# Print the first 2000 characters of HTML to see structure
print("=== HTML Structure (first 3000 chars) ===\n")
print(response.text[:3000])

print("\n\n=== Looking for potential release containers ===\n")

# Try to find common container patterns
containers = [
    ("div.content", soup.find_all("div", class_="content")),
    ("div.news-item", soup.find_all("div", class_="news-item")),
    ("div.release-item", soup.find_all("div", class_="release-item")),
    ("tr (table rows)", soup.find_all("tr")),
    ("div.media-body", soup.find_all("div", class_="media-body")),
    ("article", soup.find_all("article")),
]

for selector, elements in containers:
    if elements:
        print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
        print(f"  First element:\n{elements[0]}\n")
