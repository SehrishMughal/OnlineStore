import os
import csv
import re
import math
import time
import json
import requests
import pandas as pd

# --- CONFIG ---
SEARCH_KEYWORDS = ["shirts", "smart watch", "bedsheets", "bags"]
MAX_PAGES = 15  
OUTPUT_CSV = "markaz_catalog.csv"
IMAGE_DIR = "images"

# --- GITHUB CONFIGURATION ---
# Replace these with your actual GitHub repository details
GITHUB_USERNAME = "YOUR_GITHUB_USERNAME"
GITHUB_REPO = "YOUR_REPO_NAME"

# Create local image directory if it doesn't exist
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "os-type": "ANDROID",
    "unique-device-id": "PQ3B.190801.04221524", 
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def harvest_urls(data):
    """Recursively scans the JSON object for standard static JPEG images."""
    urls = []
    if isinstance(data, dict):
        for val in data.values():
            urls.extend(harvest_urls(val))
    elif isinstance(data, list):
        for item in data:
            urls.extend(harvest_urls(item))
    elif isinstance(data, str):
        if data.startswith("http"):
            lower_url = data.lower()
            if any(ext in lower_url for ext in [".jpg", ".jpeg", ".jif"]):
                urls.append(data)
    return urls

def clean_html(raw_html):
    """Removes HTML tags and cleans up whitespace for Meta compatibility."""
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', ' ', str(raw_html))
    return re.sub(r'\s+', ' ', clean_text).strip()

def download_local_image(img_url, product_id, suffix=""):
    """
    Downloads an image from Markaz, saves it inside the repository's 
    images/ folder, and returns the direct GitHub Raw URL.
    """
    img_url = img_url.strip()
    if not img_url or "static.markaz.app" not in img_url:
        return img_url

    file_extension = ".jpg" if ".jpeg" not in img_url.lower() else ".jpeg"
    local_filename = f"prod_{product_id}{suffix}{file_extension}"
    local_filepath = os.path.join(IMAGE_DIR, local_filename)
    new_github_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{IMAGE_DIR}/{local_filename}"

    # Idempotency check: Skip if already downloaded
    if os.path.exists(local_filepath):
        return new_github_url

    try:
        response = requests.get(img_url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            with open(local_filepath, 'wb') as img_file:
                img_file.write(response.content)
            print(f"   [Downloaded] {local_filename}")
            time.sleep(1)  # 1-second delay to protect against rate limits
            return new_github_url
        else:
            print(f"   [Warning] Failed to fetch image. Status: {response.status_code}")
            return img_url
    except Exception as e:
        print(f"   [Error] Exception saving image locally: {e}")
        return img_url

def main():
    final_list = []
    
    for query in SEARCH_KEYWORDS:
        print(f"\n Deep-Scanning: {query}")
        for page in range(1, MAX_PAGES + 1):
            url = f"https://apiv2.markaz.app/marketplace/products/search/v4/{page}/0/{query}"
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    if 'gzip' in response.headers.get('Content-Encoding', ''):
                        data = json.loads(response.content)
                    else:
                        data = response.json()
                    
                    items = data if isinstance(data, list) else data.get('products', [])
                    if not items: 
                        break 
                    
                    print(f" Page {page}: Processing {len(items)} items...")
                    
                    for p in items:
                        raw_urls = harvest_urls(p)
                        
                        unique_urls = []
                        for u in raw_urls:
                            if u not in unique_urls:
                                unique_urls.append(u)

                        # --- ID & Field Validation ---
                        product_id = str(p.get("id") or p.get("productId") or "").strip()
                        if not product_id:
                            continue

                        product_title = clean_html(p.get("name") or p.get("productName") or "")
                        raw_desc = p.get("description") or f"Premium {product_title} available at best price."
                        product_desc = clean_html(raw_desc)

                        # --- PRICE & PROFIT CALCULATIONS (40% Markup) ---
                        base_price_raw = p.get('price') or p.get('salePrice') or 0
                        try:
                            base_price = float(base_price_raw)
                        except (ValueError, TypeError):
                            base_price = 0.0
                        marked_up_price = math.ceil(base_price * 1.40)

                        # --- LOCAL PRIMARY IMAGE SYNC ---
                        raw_image_link = unique_urls[0] if len(unique_urls) > 0 else ""
                        if not raw_image_link:
                            continue
                        image_link = download_local_image(raw_image_link, product_id, suffix="")

                        # --- LOCAL GALLERY IMAGE SYNC ---
                        gallery_urls = unique_urls[1:6] if len(unique_urls) > 1 else []
                        updated_gallery_urls = []
                        for index, gal_url in enumerate(gallery_urls):
                            local_gal_url = download_local_image(gal_url, product_id, suffix=f"_alt_{index}")
                            updated_gallery_urls.append(local_gal_url)
                        
                        additional_image_link = ",".join(updated_gallery_urls) if updated_gallery_urls else ""

                        # --- META COMPLIANT FEED MAPPING ---
                        final_list.append({
                            "id": product_id,
                            "title": product_title[:140],  
                            "description": product_desc[:4900],  
                            "price": f"{marked_up_price} PKR",
                            "image_link": image_link,
                            "additional_image_link": additional_image_link,
                            "link": f"https://yourwebsite.com/products/{product_id}", 
                            "availability": "in stock",
                            "condition": "new",
                            "product_type": query
                        })
                else: 
                    break
            except Exception as e:
                print(f" Error on page {page}: {e}")
                break
            
            time.sleep(0.5)

    if final_list:
        df = pd.DataFrame(final_list)
        
        # Deduplicate strictly by product ID
        df.drop_duplicates(subset=['id'], inplace=True)
        
        # Hard drop any lingering bad rows
        df = df[df['id'].str.strip() != '']
        df = df[df['image_link'].str.strip() != '']
        df = df[df['title'].str.strip() != '']
        
        # Save explicitly with quoting=1 (QUOTE_ALL) to completely protect comma-separated values
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8', quoting=1)
        print(f"\n SUCCESS! {len(df)} heavily-sanitized local repo products saved.")

if __name__ == "__main__":
    main()
