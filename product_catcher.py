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

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n Scrapping Keyword: {query}")
        
        for page in range(1, MAX_PAGES + 1):
            # Using your discovered V4 URL structure
            url = f"https://apiv2.markaz.app/marketplace/products/search/v4/{page}/0/{query}"
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                
                if response.status_code == 200:
                    # Decompress if the server sent gzipped data
                    if 'gzip' in response.headers.get('Content-Encoding', ''):
                        data = json.loads(response.content)
                    else:
                        data = response.json()
                    
                    # V4 API usually returns a direct list
                    items = data if isinstance(data, list) else data.get('products', [])

                    if not items:
                        print(f"End of data reached at page {page}.")
                        break 
                    
                    print(f"Page {page}: Found {len(items)} items.")
                    
                    for p in items:
                        final_list.append({
                            "id": p.get("id") or p.get("productId"),
                            "title": p.get("name") or p.get("productName"),
                            "price": p.get("price") or p.get("salePrice"),
                            "currency": "PKR",
                            "description": p.get("description", "Quality product from Markaz"),
                            "image_link": p.get("image") or p.get("primaryImage"),
                            "product_type": query,
                            "stock": p.get("stock", "In Stock")
                        })
                else:
                    print(f"Page {page} Error: {response.status_code}")
                    break

            except Exception as e:
                print(f"Page {page} failed: {e}")
                break
            
            # Very short sleep since we aren't worrying about translation blocks
            time.sleep(0.5)

    if not final_list:
        print("Final list is empty! Check your unique-device-id or headers.")
        return

    # 1. Convert to DataFrame
    df = pd.DataFrame(final_list)

    # 2. Deduplicate
    initial_count = len(df)
    df = df.drop_duplicates(subset=['id'])
    final_count = len(df)

    # 3. Save to CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    
    print(f"\n--- SCRAPING COMPLETE ---")
    print(f"Total entries found: {initial_count}")
    print(f"Unique products saved: {final_count}")
    print(f"File saved as: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
