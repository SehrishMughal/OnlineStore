import requests
import pandas as pd
import time
import json
import gzip
import re

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
MAX_PAGES = 15  
OUTPUT_CSV = "markaz_catalog.csv"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "os-type": "ANDROID",
    "unique-device-id": "97e9837e15c22eb4", 
    "User-Agent": "ktor-client"
}

def find_urls_in_dict(data):
    """Recursively searches for any strings starting with http in the JSON"""
    urls = []
    if isinstance(data, dict):
        for val in data.values():
            urls.extend(find_urls_in_dict(val))
    elif isinstance(data, list):
        for item in data:
            urls.extend(find_urls_in_dict(item))
    elif isinstance(data, str):
        if data.startswith("http") and (".jpg" in data or ".png" in data or "ibank" in data):
            urls.append(data)
    return urls

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n🚀 Scanning: {query}")
        for page in range(1, MAX_PAGES + 1):
            url = f"https://apiv2.markaz.app/marketplace/products/search/v4/{page}/0/{query}"
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    if 'gzip' in response.headers.get('Content-Encoding', ''):
                        data = json.loads(response.content)
                    else:
                        data = response.json()
                    
                    items = data if isinstance(data, list) else data.get('products', [])
                    if not items: break 
                    
                    print(f" Page {page}: Processing {len(items)} items...")
                    
                    for p in items:
                        # This looks through EVERYTHING in the product (nested lists, objects, etc)
                        all_found_urls = find_urls_in_dict(p)
                        
                        # Remove duplicates while keeping order
                        seen = set()
                        unique_urls = [x for x in all_found_urls if not (x in seen or seen.add(x))]

                        final_list.append({
                            "id": p.get("id") or p.get("productId") or "N/A",
                            "title": p.get("name") or p.get("productName") or "N/A",
                            "price": p.get("price") or p.get("salePrice") or "0",
                            "image_1": unique_urls[0] if len(unique_urls) > 0 else "",
                            "image_2": unique_urls[1] if len(unique_urls) > 1 else "",
                            "image_3": unique_urls[2] if len(unique_urls) > 2 else "",
                            "image_4": unique_urls[3] if len(unique_urls) > 3 else "",
                            "image_5": unique_urls[4] if len(unique_urls) > 4 else "",
                            "image_6": unique_urls[5] if len(unique_urls) > 5 else "",
                            "product_type": query
                        })
                else: break
            except: break
            time.sleep(0.5)

    if final_list:
        df = pd.DataFrame(final_list).drop_duplicates(subset=['id', 'title'])
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\n SUCCESS! Captured {len(df)} products with all image columns filled.")

if __name__ == "__main__":
    main()
