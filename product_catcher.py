import requests
import pandas as pd
import time
import json     
import gzip    
from googletrans import Translator

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
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
    if not text or text == "Product": 
        return text
    try:
        # Removed the 'timeout' argument from here
        result = translator.translate(text, dest=target)
        return result.text
    except Exception as e:
        # This will now only trigger on actual blocks/network errors
        print(f" Translation failed: {e}")
        return text

def main():
    final_list = []
    for query in SEARCH_KEYWORDS:
        print(f"--- Fetching {query} ---")
        # Increase pageSize to 50 to get more data per request
        payload = {"searchQuery": query, "pageNumber": 1, "pageSize": 50}
        
        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)
            
            if response.status_code == 200:
                # Automatic decompression check
                if 'gzip' in response.headers.get('Content-Encoding', ''):
                    data = json.loads(response.content)
                else:
                    data = response.json()
                
                items = data if isinstance(data, list) else data.get('items', [])
                
                if not items:
                    print(f"No items found for {query}")
                    continue

                print(f"Found {len(items)} items. Processing...")
                
                for p in items:
                    # Capture everything immediately
                    name = p.get("name") or p.get("productName") or "Product"
                    id = p.get("id") or p.get("productId")
                    # We will translate this later or keep a fallback
                    final_list.append({
                        "id": str(id)+name,
                        "title": name, # Initial title is English
                        "title_urdu": "placeholder",
                        "description": p.get("description", "Quality product"),
                        "price": f"{p.get('price') or p.get('salePrice')} PKR",
                        "image_link": p.get("image") or p.get("primaryImage"),
                        "product_type": query
                    })
            else:
                print(f"API Error {response.status_code}")

        except Exception as e:
            print(f"Request failed for {query}: {e}")
        
        time.sleep(1) # Short sleep to avoid Markaz API ban

    if not final_list:
        print("No data collected at all.")
        return

    # --- BATCH TRANSLATION ---
    print(f"\nTranslating {len(final_list)} unique items to Urdu...")
    for entry in final_list:
        # We only translate if we haven't been blocked yet
        entry["title_urdu"] = translate_text(entry["title"], 'ur')

    # --- SAVE ---
    df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Success! {len(df)} total items saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
