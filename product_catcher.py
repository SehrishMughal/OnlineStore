import requests
import pandas as pd
import time
import json

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

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n Scrapping Keyword: {query}")
        
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

                    if not items:
                        break 
                    
                    print(f" Page {page}: Found {len(items)} items.")
                    
                    for p in items:
                        # 1. Primary Image
                        primary = p.get("image") or p.get("primaryImage") or ""
                        
                        # 2. Extract Gallery
                        # Markaz V4 often uses 'productImages' (list of dicts) or 'images' (list of strings)
                        raw_images = p.get("productImages") or p.get("images") or []
                        
                        all_urls = []
                        if isinstance(raw_images, list):
                            for img in raw_images:
                                if isinstance(img, str):
                                    all_urls.append(img)
                                elif isinstance(img, dict):
                                    # Extract URL from dict: check common keys
                                    url_val = img.get("url") or img.get("image") or img.get("src")
                                    if url_val:
                                        all_urls.append(url_val)
                        
                        # Ensure primary is at the start and unique
                        if primary and primary not in all_urls:
                            all_urls.insert(0, primary)
                        
                        # 3. Clean up the list (remove any empty strings)
                        all_urls = [u for u in all_urls if u.startswith('http')]

                        final_list.append({
                            "id": p.get("id") or p.get("productId"),
                            "title": p.get("name") or p.get("productName"),
                            "price": p.get("price") or p.get("salePrice"),
                            "image_1": all_urls[0] if len(all_urls) > 0 else "",
                            "image_2": all_urls[1] if len(all_urls) > 1 else "",
                            "image_3": all_urls[2] if len(all_urls) > 2 else "",
                            "image_4": all_urls[3] if len(all_urls) > 3 else "",
                            "image_5": all_urls[4] if len(all_urls) > 4 else "",
                            "all_images_comma": ",".join(all_urls), # Best for Facebook/Google Feed
                            "product_type": query
                        })
                else:
                    break

            except Exception as e:
                print(f" Error: {e}")
                break
            
            time.sleep(0.5)

    if final_list:
        df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\n Done! Saved {len(df)} products with full galleries.")

if __name__ == "__main__":
    main()
