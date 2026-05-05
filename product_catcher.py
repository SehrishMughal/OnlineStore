import requests
import pandas as pd
import time
import json     
import gzip    
from googletrans import Translator

# --- CONFIG ---
SEARCH_KEYWORDS = ["mens wear", "smart watch", "bedsheets"]
API_URL = "https://api.markaz.app/products/v2/search?page=1"
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

# Initialize translator once
translator = Translator()

def translate_text(text, target='ur'):
    try:
        # Note: googletrans requires .translate on the instance
        return translator.translate(text, dest=target).text
    except Exception as e:
        return text 

def main():
    final_list = []
    for query in SEARCH_KEYWORDS:
        print(f"Searching for: {query}...")
        payload = {"searchQuery": query, "pageNumber": 1, "pageSize": 20}
        
        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            
            if response.status_code == 200:
                #Handle Gzip
                if response.headers.get('Content-Encoding') == 'gzip':
                    decoded_content = gzip.decompress(response.content)
                    data = json.loads(decoded_content)
                else:
                    data = response.json()
                
                #Handle Data Structure
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get('items', [])
                else:
                    items = []

                #if items EXIST
                if items:
                    print(f"Found {len(items)} items. Processing...")
                    for p in items:
                        original_title = p.get("name") or p.get("productName") or ""
                        
                        # Translate
                        urdu_title = translate_text(original_title, 'ur')
                        
                        final_list.append({
                            "id": p.get("id") or p.get("productId"),
                            "title": urdu_title, # Using the translated title
                            "original_title": original_title,
                            "description": p.get("description", "Quality product from Markaz"),
                            "availability": "in stock",
                            "condition": "new",
                            "price": f"{p.get('price') or p.get('salePrice')} PKR",
                            "link": "https://facebook.com/yourstore",
                            "image_link": p.get("image") or p.get("primaryImage"),
                            "brand": "Markaz",
                            "product_type": query
                        })
                else:
                    print(f" Warning: No items found for query '{query}'")
            else:
                print(f"API Error: {response.status_code}")

        except Exception as e:
            print(f"Critical error during query '{query}': {e}")

        time.sleep(2)

    if final_list:
        df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig') # utf-8-sig helps Excel show Urdu correctly
        print(f"Sync Complete! {len(df)} unique products saved to {OUTPUT_CSV}")
    else:
        print("Final list is empty. No CSV generated.")

if __name__ == "__main__":
    main()
