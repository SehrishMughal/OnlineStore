import requests
import pandas as pd
import time
import json    
import random
from googletrans import Translator

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
# Use the base URL without any parameters
API_URL = "https://api.markaz.app/products/v2/search" 
OUTPUT_CSV = "markaz_catalog.csv"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "build-version-code": "479",
    "build-version-name": "2.8.4",
    "os-type": "ANDROID",
    "unique-device-id": "97e9837e15c22eb4", 
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
        print(f"\n🚀 Target: {query}")
        
        # 1. Add a random 'cb' (cache-buster) to the URL
        # 2. Use the exact params the App uses
        params = {
            "searchQuery": query,
            "pageNumber": 1,
            "pageSize": 50,
            "cb": random.randint(1000, 9999) 
        }
        
        try:
            # TRY GET FIRST (Common in Search APIs)
            response = requests.get(API_URL, headers=HEADERS, params=params, timeout=15)
            
            # If GET fails or returns 0, try POST
            if response.status_code != 200 or not response.json():
                response = requests.post(API_URL, headers=HEADERS, json=params, timeout=15)

            if response.status_code == 200:
                # Handle Gzip/Plain text
                try:
                    if 'gzip' in response.headers.get('Content-Encoding', ''):
                        data = json.loads(response.content)
                    else:
                        data = response.json()
                except:
                    data = response.json()
                
                items = data if isinstance(data, list) else data.get('items', [])
                
                if items:
                    print(f"  Captured {len(items)} items.")
                    for p in items:
                        p_name = p.get("name") or p.get("productName") or "Product"
                        p_id = p.get("id") or p.get("productId") or hash(p_name)
                        
                        # Use a prefix to prevent duplicate IDs from different categories
                        unique_id = f"{query[:3]}_{p_id}" 

                        final_list.append({
                            "id": unique_id,
                            "title": p_name,
                            "title_urdu": "Pending",
                            "price": f"{p.get('price') or p.get('salePrice')} PKR",
                            "image_link": p.get("image") or p.get("primaryImage"),
                            "product_type": query
                        })
                else:
                    print(f"Server gave empty list for {query}")
            else:
                print(f"Server Error: {response.status_code}")

        except Exception as e:
            print(f"Connection Error: {e}")
        
        time.sleep(3) # Slow down to look more human

    # --- PROCESS FINAL DATA ---
    if not final_list:
        print("No items captured. Check your unique-device-id.")
        return

    # Convert to DataFrame and drop TRUE duplicates (same title and price)
    df = pd.DataFrame(final_list).drop_duplicates(subset=['title', 'price'])
    
    print(f"\nTranslating {len(df)} unique products...")
    
    # We use a list comprehension for faster/safer translation
    translated_titles = []
    for t in df['title']:
        translated_titles.append(translate_text(t, 'ur'))
        time.sleep(0.2)
    
    df['title_urdu'] = translated_titles

    # --- SAVE ---
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n SUCCESS! CSV saved with {len(df)} products.")

if __name__ == "__main__":
    main()
