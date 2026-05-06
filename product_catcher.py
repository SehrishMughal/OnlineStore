import requests
import pandas as pd
import time
import json    
import random
from googletrans import Translator

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
# Use the base URL without any parameters
API_URL = "https://apiv2.markaz.app/marketplace/products/search/v4/1/0/"
OUTPUT_CSV = "markaz_catalog.csv"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "build-version-code": "479",
    "build-version-name": "2.8.4",
    "os-type": "ANDROID",
    "unique-device-id": "PQ3B.190801.04221524", 
    "User-Agent": "ktor-client"
}

translator = Translator()

def translate_text(text, target='ur'):
    if not text or len(text) < 3: return text
    try:
        return translator.translate(text, dest=target).text
    except:
        return text

def main():
    final_list = []
    for query in SEARCH_KEYWORDS:
        # We use the V4 structure you found: 
        # pageNumber = 1, pageSize = 50 (or 0 if that's their 'all' code), query = bags
        v4_url = f"https://apiv2.markaz.app/marketplace/products/search/v4/1/50/{query}"
        
        print(f"\n--- Searching V4 for: {query} ---")
        
        try:
            # Note: This is likely a GET request based on that URL structure
            response = requests.get(v4_url, headers=HEADERS, timeout=20)
            
            if response.status_code == 200:
                # Handle Gzip
                if 'gzip' in response.headers.get('Content-Encoding', ''):
                    data = json.loads(response.content)
                else:
                    data = response.json()
                
                # Check if the structure is a direct list or wrapped in 'products'
                items = data if isinstance(data, list) else data.get('products', data.get('items', []))
                
                if items:
                    print(f" Success! Found {len(items)} items.")
                    for p in items:
                        # Composite ID to ensure no data is lost
                        p_id = p.get("id") or p.get("productId")
                        final_list.append({
                            "id": f"{query}_{p_id}",
                            "title": p.get("name") or p.get("productName"),
                            "title_urdu": "Pending",
                            "price": f"{p.get('price') or p.get('salePrice')} PKR",
                            "image_link": p.get("image") or p.get("primaryImage"),
                            "product_type": query
                        })
                else:
                    print(f" URL worked but returned 0 items. Check if {query} needs to be URL-encoded.")
            else:
                print(f" API Error {response.status_code} at V4 URL")

        except Exception as e:
            print(f" V4 Request failed: {e}")
        
        time.sleep(2)

    # --- SAVE ---
    if final_list:
        df = pd.DataFrame(final_list).drop_duplicates(subset=['title', 'price'])
        # Add translation loop here as before...
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        print(f"\n Done! {len(df)} items saved.")

if __name__ == "__main__":
    main()
