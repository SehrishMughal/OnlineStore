import requests
import pandas as pd
import time
import json     
import gzip    
from googletrans import Translator

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
API_URL = "https://api.markaz.app/products/v2/search" # Clean Base URL
OUTPUT_CSV = "markaz_catalog.csv"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "build-version-code": "479",
    "build-version-name": "2.8.4",
    "device-id": "PQ3B.190801.03250903",
    "os-type": "ANDROID",
    "unique-device-id": "97e9837e15c22eb4", 
    "User-Agent": "ktor-client"
}

translator = Translator()

def translate_text(text, target='ur'):
    if not text or text == "Product": 
        return text
    try:
        result = translator.translate(text, dest=target)
        return result.text
    except Exception as e:
        print(f" Translation failed for '{text[:20]}': {e}")
        return text

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n--- Searching for: {query} ---")
        
        # We put parameters in the URL to force the server to acknowledge the new search
        query_url = f"{API_URL}?searchQuery={query}&pageNumber=1&pageSize=50"
        payload = {"searchQuery": query, "pageNumber": 1, "pageSize": 50}
        
        try:
            response = requests.post(query_url, headers=HEADERS, json=payload, timeout=20)
            
            if response.status_code == 200:
                if 'gzip' in response.headers.get('Content-Encoding', ''):
                    try:
                        data = json.loads(response.content)
                    except:
                        data = response.json()
                else:
                    data = response.json()
                
                items = data if isinstance(data, list) else data.get('items', [])
                
                if items:
                    first_item_name = items[0].get('name') or items[0].get('productName') or "Unknown"
                    print(f" Received {len(items)} items. First item: {first_item_name}")
                    
                    for p in items:
                        p_id = p.get("id") or p.get("productId")
                        p_name = p.get("name") or p.get("productName") or "Product"
                        
                        # Composite ID ensures 'Shirts' don't overwrite 'Bags' if IDs overlap
                        unique_id = f"{query}_{p_id}" 

                        final_list.append({
                            "markaz_id": id,
                            "id": unique_id,
                            "title": p_name,
                            "title_urdu": "placeholder",
                            "description": p.get("description", "Quality product"),
                            "price": f"{p.get('price') or p.get('salePrice')} PKR",
                            "image_link": p.get("image") or p.get("primaryImage"),
                            "product_type": query
                        })
                else:
                    print(f" Server returned 0 items for {query}")
            else:
                print(f" API Error {response.status_code}")

        except Exception as e:
            print(f" Request failed for {query}: {e}")
        
        time.sleep(2) # Prevent rate limiting

    if not final_list:
        print("No data collected. Check logs above.")
        return

    # --- BATCH TRANSLATION ---
    print(f"\nTranslating {len(final_list)} items to Urdu...")
    for entry in final_list:
        entry["title_urdu"] = translate_text(entry["title"], 'ur')
        # Tiny sleep to keep Google happy
        time.sleep(0.1)

    # --- SAVE ---
    df = pd.DataFrame(final_list)
    # Final check: drop duplicates based on the title and price to be safe
    df = df.drop_duplicates(subset=['title', 'price'])
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\nSuccess! {len(df)} total items saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
