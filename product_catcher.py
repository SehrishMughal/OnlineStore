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
            url = f"https://apiv2.markaz.app/marketplace/products/search/v4/{page}/0/{query}"
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                
                if response.status_code == 200:
                    if 'gzip' in response.headers.get('Content-Encoding', ''):
                        data = json.loads(gzip.decompress(response.content))
                    else:
                        data = response.json()
                    
                    items = data if isinstance(data, list) else data.get('products', [])

                    if not items:
                        print(f"End of data reached at page {page}.")
                        break 
                    
                    print(f"Page {page}: Found {len(items)} items.")
                    
                    for p in items:
                        # --- MULTI-IMAGE LOGIC ---
                        # 1. Get the primary image
                        primary = p.get("image") or p.get("primaryImage") or ""
                        
                        # 2. Look for the list of all images
                        image_list = p.get("images") or p.get("productImages") or []
                        
                        # 3. Clean and combine images
                        all_images = []
                        if isinstance(image_list, list):
                            for img in image_list:
                                # Check if the list contains strings or objects
                                if isinstance(img, str):
                                    all_images.append(img)
                                elif isinstance(img, dict):
                                    all_images.append(img.get("url") or img.get("image"))
                        
                        # Add primary image to the front if it's not already in the list
                        if primary and primary not in all_images:
                            all_images.insert(0, primary)
                        
                        # Join with commas for the CSV
                        image_string = ",".join(filter(None, all_images))

                        final_list.append({
                            "id": p.get("id") or p.get("productId"),
                            "title": p.get("name") or p.get("productName"),
                            "price": p.get("price") or p.get("salePrice"),
                            "currency": "PKR",
                            "description": p.get("description", "Quality product from Markaz"),
                            "main_image": primary,
                            "all_images": image_string, # <--- All pictures here
                            "product_type": query,
                            "stock": p.get("stock", "In Stock")
                        })
                else:
                    print(f"Page {page} Error: {response.status_code}")
                    break

            except Exception as e:
                print(f"Page {page} failed: {e}")
                break
            
            time.sleep(0.5)

    if not final_list:
        print("Final list is empty!")
        return

    df = pd.DataFrame(final_list).drop_duplicates(subset=['id'])
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    
    print(f"\n--- COMPLETE ---")
    print(f"Saved {len(df)} products with multi-image support to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
