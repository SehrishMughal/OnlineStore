import requests
import pandas as pd
import time
import json     
import gzip    
from googletrans import Translator

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
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
        print(f"\n--- Searching for: {query} ---")
        
        # 1. CLEAN URL: Remove the hardcoded ?page=1
        # 2. Add the query to the URL (This is often how mobile APIs work)
        clean_url = f"https://api.markaz.app/products/v2/search?searchQuery={query}&pageNumber=1&pageSize=50"
        
        payload = {
            "searchQuery": query, 
            "pageNumber": 1, 
            "pageSize": 50
        }
        
        try:
            # Try sending both the URL params AND the payload
            response = requests.post(clean_url, headers=HEADERS, json=payload, timeout=20)
            
            if response.status_code == 200:
                # Decompression logic...
                if 'gzip' in response.headers.get('Content-Encoding', ''):
                    data = json.loads(response.content)
                else:
                    data = response.json()
                
                items = data if isinstance(data, list) else data.get('items', [])
                
                if items:
                    # Check the first item to see if it actually matches our query
                    first_item_name = items[0].get('name', 'Unknown')
                    print(f" Received {len(items)} items. First item: {first_item_name}")
                    
                    for p in items:
                        # Use a composite ID to prevent overwriting
                        p_id = p.get("id") or p.get("productId")
                        unique_id = f"{query}_{p_id}" 

                        final_list.append({
                            "id": unique_id,
                            "title": p.get("name") or p.get("productName"),
                            "title_urdu": "placeholder",
                            "description": p.get("description", "Quality product"),
                            "price": f"{p.get('price') or p.get('salePrice')} PKR",
                            "image_link": p.get("image") or p.get("primaryImage"),
                            "product_type": query
                        })
                else:
                    print(f" Server returned 0 items for {query}")

    # --- BATCH TRANSLATION ---
    #print(f"\nTranslating {len(final_list)} unique items to Urdu...")
    for entry in final_list:
        # We only translate if we haven't been blocked yet
        entry["title_urdu"] = translate_text(entry["title"], 'ur')

    # --- SAVE ---
    df = pd.DataFrame(final_list)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Success! {len(df)} total items saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
