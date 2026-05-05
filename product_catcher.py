import requests
import pandas as pd
import time
from googletrans import Translator

# --- CONFIG ---
SEARCH_KEYWORDS = ["mens wear", "smart watch", "bedsheets"] # Add as many as you want
API_URL = "https://api.markaz.app/products/v2/search?page=1" # Confirm this from your sniffer
OUTPUT_CSV = "markaz_catalog.csv"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "build-version-code": "479",
    "build-version-name": "2.8.4",
    "device-id": "PQ3B.190801.03250903",
    "os-type": "ANDROID",
    "unique-device-id": "97e9837e15c22eb4", # <--- CRITICAL: Use your actual ID
    "User-Agent": "ktor-client"
}

def translate_text(text, target='ur'):
    try:
        # Detects if text is Chinese/English and converts to Urdu
        return Translator.translate(text, dest=target).text
    except:
        return text # Returns original if translation fails

def main():
    final_list = []
    for query in SEARCH_KEYWORDS:
        payload = {"searchQuery": query, "pageNumber": 1, "pageSize": 20}
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            items = response.json()
        if not items:
            print(f"Warning: No items found for query '{query}'")
            for p in items:
                original_title = p.get("productName", "")
                
                # Translate Title to Urdu for better local Facebook conversion
                urdu_title = translate_text(original_title, 'ur')
                
                final_list.append({
                "id": p.get("productId") or p.get("id"),
                "title": p.get("productName") or p.get("title"),
                "description": p.get("description", "Quality product from Markaz"),
                "availability": "in stock",
                "condition": "new",
                "price": f"{p.get('salePrice')} PKR",
                "link": "https://facebook.com/yourstore", # Required placeholder
                "image_link": p.get("primaryImage") or p.get("image_url"),
                "brand": "Markaz",
                "product_type": query
            })
        time.sleep(3)

    df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
    df.to_csv("markaz_catalog.csv", index=False)
    print("Sync Complete. CSV generated with Urdu titles.")

if __name__ == "__main__":
    main()
