import requests
import pandas as pd
import time
import json
import gzip
import math

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
            # Only allow .jpg, .jpeg, and .jif formats
            if any(ext in lower_url for ext in [".jpg", ".jpeg", ".jif"]):
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
                        data = json.loads(response.content)
                    else:
                        data = response.json()
                    
                    items = data if isinstance(data, list) else data.get('products', [])
                    if not items: break 
                    
                    print(f" Page {page}: Processing {len(items)} items...")
                    
                    for p in items:
                        # Find every URL hidden inside this specific product
                        raw_urls = harvest_urls(p)
                        
                        # Remove duplicates while keeping the original order
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

                        # Calculate price with a 40% markup profit rate
                        marked_up_price = math.ceil(base_price * 1.40)

                        # Define title and backup string for fallback matching
                        product_title = p.get("name") or p.get("productName") or "N/A"

                        # --- META COMPLIANT FEED MAPPING ---
                        final_list.append({
                            "id": str(p.get("id") or p.get("productId") or "N/A"),
                            "title": product_title,
                            "description": p.get("description") or f"Premium {product_title} available at best price.",
                            
                            # Meta standard absolute currency formatting string
                            "price": f"{marked_up_price} PKR",
                            
                            # Primary and secondary image lists structured natively
                            "image_link": unique_urls[0] if len(unique_urls) > 0 else "",
                            "additional_image_link": ",".join(unique_urls[1:6]) if len(unique_urls) > 1 else "",
                            
                            # Required operational static field fallbacks
                            "link": f"https://yourwebsite.com/products/{p.get('id') or 'shop'}", 
                            "availability": "in stock",
                            "condition": "new",
                            
                            # Custom reference filtering meta tags
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
        print(f"\n SUCCESS! {len(df)} unique Meta-ready products saved.")
        print(f" Calculated 40% profit margin into all 'price' fields automatically.")

if __name__ == "__main__":
    main()
