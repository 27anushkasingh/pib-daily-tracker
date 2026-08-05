"""Debug script to fetch and analyze PIB website HTML."""

import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://pib.gov.in/allRelease.aspx"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

print("Fetching PIB website...")
response = requests.get(url, headers=headers, timeout=30)
print(f"Status Code: {response.status_code}\n")

soup = BeautifulSoup(response.content, "html.parser")

# Find all table rows
print("=== Looking for table rows ===")
rows = soup.find_all("tr")
print(f"Found {len(rows)} table rows\n")

if rows:
    print("First 5 rows:\n")
    for i, row in enumerate(rows[:5]):
        print(f"Row {i}:")
        cells = row.find_all("td")
        print(f"  Cells: {len(cells)}")
        for j, cell in enumerate(cells[:3]):
            text = cell.get_text(strip=True)[:100]
            print(f"    Cell {j}: {text}")
        
        # Look for links
        links = row.find_all("a")
        if links:
            print(f"  Links: {len(links)}")
            for link in links[:2]:
                print(f"    - {link.get_text(strip=True)[:50]} -> {link.get('href', 'NO HREF')[:80]}")
        print()

# Look for divs with content class
print("\n=== Looking for divs with class='content' ===")
content_divs = soup.find_all("div", class_="content")
print(f"Found {len(content_divs)} divs with class='content'\n")

if content_divs:
    print("First 3 content divs:")
    for i, div in enumerate(content_divs[:3]):
        text = div.get_text(strip=True)[:200]
        print(f"Div {i}: {text}\n")

# Look for any links
print("\n=== All links on page ===")
all_links = soup.find_all("a", limit=20)
print(f"First 20 links:")
for link in all_links:
    href = link.get("href", "")
    text = link.get_text(strip=True)[:50]
    if text:  # Only if has text
        print(f"  {text} -> {href[:80]}")

print("\n=== Page title and meta ===")
print(f"Page title: {soup.title}")
