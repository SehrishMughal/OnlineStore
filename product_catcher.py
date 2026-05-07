import requests
import pandas as pd
import time
import json
import gzip

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

def harvest_urls(data):
    """
    Recursively scans the entire JSON object for any string starting with http.
    This catches .webp thumbnails, alicdn jpgs, and everything in between.
    """
    urls = []
    if isinstance(data, dict):
        for val in data.values():
            urls.extend(harvest_urls(val))
    elif isinstance(data, list):
        for item in data:
            urls.extend(harvest_urls(item))
    elif isinstance(data, str):
        # We look for any URL that looks like an image
        if data.startswith("http") and any(ext in data.lower() for ext in [".jpg", ".png", ".webp", "ibank", "thumbnails"]):
            urls.append(data)
    return urls

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n Deep-Scanning: {query}")
        for page in range(1, MAX_PAGES + 1):
            url = f"https://apiv2.markaz.app/marketplace/products/search/v4/{page}/0/{query}"
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    # Decompress if necessary
                    if 'gzip' in response.headers.get('Content-Encoding', ''):
                        data = json.loads(gzip.decompress(response.content))
                    else:
                        data = response.json()
                    
                    items = data if isinstance(data, list) else data.get('products', [])
                    if not items: break 
                    
                    print(f" Page {page}: Processing {len(items)} items...")
                    
                    for p in items:
                        # Find every URL hidden inside this specific product
                        raw_urls = harvest_urls(p)
                        
                        # Remove duplicates while keeping the original order
                        # Usually, the best/main image appears first in the JSON
                        unique_urls = []
                        for u in raw_urls:
                            if u not in unique_urls:
                                unique_urls.append(u)

                        final_list.append({
                            "id": p.get("id") or p.get("productId") or "N/A",
                            "title": p.get("name") or p.get("productName") or "N/A",
                            "price": f"{p.get('price') or p.get('salePrice') or '0'} PKR",
                            "image_1": unique_urls[0] if len(unique_urls) > 0 else "",
                            "image_2": unique_urls[1] if len(unique_urls) > 1 else "",
                            "image_3": unique_urls[2] if len(unique_urls) > 2 else "",
                            "image_4": unique_urls[3] if len(unique_urls) > 3 else "",
                            "image_5": unique_urls[4] if len(unique_urls) > 4 else "",
                            "image_6": unique_urls[5] if len(unique_urls) > 5 else "",
                            "product_type": query
                        })
                else: 
                    break
            except Exception as e:
                print(f" Error on page {page}: {e}")
                break
            
            time.sleep(0.5)

    if final_list:
        # Deduplicate the product list by ID
        df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\n SUCCESS! {len(df)} unique products saved.")
        print(f"Columns filled with both Alibaba (.jpg) and Markaz (.webp) links.")

if __name__ == "__main__":
    main()
