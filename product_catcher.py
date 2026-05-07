import requests
import pandas as pd
import time
import json
import gzip

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
MAX_PAGES = 5  # Reduced pages because we are doing deep lookups
OUTPUT_CSV = "markaz_catalog.csv"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "os-type": "ANDROID",
    "unique-device-id": "97e9837e15c22eb4", 
    "User-Agent": "ktor-client"
}

def get_full_gallery(product_id):
    """Hits the individual product API to get the full list of 6+ images"""
    # This is the standard Markaz detail endpoint
    detail_url = f"https://apiv2.markaz.app/marketplace/products/v2/details/{product_id}"
    try:
        resp = requests.get(detail_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Look for images in the detail response
            imgs = data.get("productImages") or data.get("images") or []
            return [i if isinstance(i, str) else i.get("url") for i in imgs if i]
    except:
        pass
    return []

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n Scrapping: {query}")
        for page in range(1, MAX_PAGES + 1):
            search_url = f"https://apiv2.markaz.app/marketplace/products/search/v4/{page}/0/{query}"
            
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    data = json.loads(response.content) if 'gzip' in response.headers.get('Content-Encoding', '') else response.json()
                    items = data if isinstance(data, list) else data.get('products', [])
                    
                    if not items: break
                    print(f" Page {page}: Processing {len(items)} items...")

                    for p in items:
                        p_id = p.get("id") or p.get("productId")
                        # 1. Start with what search gave us
                        images = p.get("productImages") or p.get("images") or []
                        urls = [i if isinstance(i, str) else i.get("url") for i in images if i]

                        # 2. IF EMPTY or LESS THAN 2: Go deeper
                        if len(urls) < 2 and p_id:
                            print(f"      🔍 Deep lookup for product {p_id}...")
                            urls = get_full_gallery(p_id)
                            time.sleep(0.5) # Be kind to the API

                        # 3. Add primary image if still empty
                        if not urls:
                            primary = p.get("image") or p.get("primaryImage")
                            if primary: urls.append(primary)

                        final_list.append({
                            "id": p_id,
                            "title": p.get("name") or p.get("productName"),
                            "price": p.get("price") or p.get("salePrice"),
                            "image_1": urls[0] if len(urls) > 0 else "",
                            "image_2": urls[1] if len(urls) > 1 else "",
                            "image_3": urls[2] if len(urls) > 2 else "",
                            "image_4": urls[3] if len(urls) > 3 else "",
                            "image_5": urls[4] if len(urls) > 4 else "",
                            "image_6": urls[5] if len(urls) > 5 else "",
                            "product_type": query
                        })
                else: break
            except: break
            time.sleep(1)

    if final_list:
        df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\n SUCCESS! Deep sync complete. {len(df)} items saved.")

if __name__ == "__main__":
    main()
