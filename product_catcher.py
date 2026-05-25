import requests
import pandas as pd
import time
import json
import math
import re

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
MAX_PAGES = 15  
OUTPUT_CSV = "markaz_catalog.csv"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "os-type": "ANDROID",
    "unique-device-id": "PQ3B.190801.04221524", 
    "User-Agent": "ktor-client"
}

def harvest_urls(data):
    """
    Recursively scans the entire JSON object for any string starting with http.
    Filters specifically for standard static JPEG images (.jpg, .jpeg, .jif).
    """
    urls = []
    if isinstance(data, dict):
        for val in data.values():
            urls.extend(harvest_urls(val))
    elif isinstance(data, list):
        for item in data:
            urls.extend(harvest_urls(item))
    elif isinstance(data, str):
        if data.startswith("http"):
            lower_url = data.lower()
            if any(ext in lower_url for ext in [".jpg", ".jpeg", ".jif"]):
                urls.append(data)
    return urls

def clean_html(raw_html):
    """Removes HTML tags and cleans up whitespace for Meta compatibility."""
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', ' ', str(raw_html))
    return re.sub(r'\s+', ' ', clean_text).strip()

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n Deep-Scanning: {query}")
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
                        raw_urls = harvest_urls(p)
                        
                        unique_urls = []
                        for u in raw_urls:
                            if u not in unique_urls:
                                unique_urls.append(u)

                        # --- PRICE & PROFIT CALCULATIONS ---
                        base_price_raw = p.get('price') or p.get('salePrice') or 0
                        try:
                            base_price = float(base_price_raw)
                        except (ValueError, TypeError):
                            base_price = 0.0

                        marked_up_price = math.ceil(base_price * 1.40)
                        
                        # Validate ID and skip completely broken ones
                        product_id = str(p.get("id") or p.get("productId") or "").strip()
                        if not product_id:
                            continue

                        product_title = clean_html(p.get("name") or p.get("productName") or "")
                        raw_desc = p.get("description") or f"Premium {product_title} available at best price."
                        product_desc = clean_html(raw_desc)

                        # Ensure we actually have a valid main image
                        image_link = unique_urls[0] if len(unique_urls) > 0 else ""
                        if not image_link:
                            continue

                        # --- META COMPLIANT FEED MAPPING ---
                        final_list.append({
                            "id": product_id,
                            "title": product_title[:140],  # Meta title cap limit recommendation
                            "description": product_desc[:4900],  # Meta description character fallback
                            "price": f"{marked_up_price} PKR",
                            "image_link": image_link,
                            "additional_image_link": ",".join(unique_urls[1:6]) if len(unique_urls) > 1 else "",
                            "link": f"https://yourwebsite.com/products/{product_id}", 
                            "availability": "in stock",
                            "condition": "new",
                            "product_type": query
                        })
                else: 
                    break
            except Exception as e:
                print(f" Error on page {page}: {e}")
                break
            
            time.sleep(0.5)

    if final_list:
        df = pd.DataFrame(final_list)
        
        # Deduplicate strictly by product ID
        df.drop_duplicates(subset=['id'], inplace=True)
        
        # Hard drop any lingering bad rows
        df = df[df['id'].str.strip() != '']
        df = df[df['image_link'].str.strip() != '']
        df = df[df['title'].str.strip() != '']
        
        # Save explicitly with standard UTF-8 and quoting parameters to avoid broken commas
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8', quoting=1)
        print(f"\n SUCCESS! {len(df)} heavily-sanitized Meta products saved.")

if __name__ == "__main__":
    main()
