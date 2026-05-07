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
        print(f"\n Scrapping: {query}")
        for page in range(1, MAX_PAGES + 1):
            # Using the V4 Path you confirmed
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
                    
                    print(f"Page {page}: Found {len(items)} items.")
                    
                    for p in items:
                        # 1. Grab all possible image sources
                        # The Alibaba links you provided are almost always in 'productImages'
                        raw_images = p.get("productImages") or p.get("images") or []
                        
                        # 2. Extract URLs into a flat list
                        urls = []
                        if isinstance(raw_images, list):
                            for img in raw_images:
                                if isinstance(img, str):
                                    urls.append(img)
                                elif isinstance(img, dict):
                                    # Handles cases where it's a list of objects
                                    u = img.get("url") or img.get("image") or img.get("src")
                                    if u: urls.append(u)
                        
                        # 3. Fallback: if list is empty, use the single primary image
                        if not urls:
                            primary = p.get("image") or p.get("primaryImage")
                            if primary: urls.append(primary)

                        # 4. Map the first 6 images to specific columns
                        final_list.append({
                            "id": p.get("id") or p.get("productId"),
                            "title": p.get("name") or p.get("productName"),
                            "price": f"{p.get('price') or p.get('salePrice')} PKR",
                            "image_1": urls[0] if len(urls) > 0 else "",
                            "image_2": urls[1] if len(urls) > 1 else "",
                            "image_3": urls[2] if len(urls) > 2 else "",
                            "image_4": urls[3] if len(urls) > 3 else "",
                            "image_5": urls[4] if len(urls) > 4 else "",
                            "image_6": urls[5] if len(urls) > 5 else "",
                            "all_images_comma": ",".join(urls), # Backup column with everything
                            "product_type": query
                        })
                else:
                    print(f" Error {response.status_code}")
                    break
            except Exception as e:
                print(f" Failed: {e}")
                break
            
            time.sleep(0.5)

    if final_list:
        df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
        # Save to CSV
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\n SUCCESS! Captured {len(df)} products.")
        print(f"Check the columns image_1 through image_6 in '{OUTPUT_CSV}'")

if __name__ == "__main__":
    main()
