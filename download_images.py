import os
import csv
import requests
import time

# Create images folder if it doesn't exist
IMAGE_DIR = "images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

CSV_FILE = "markaz_catalog.csv"  # Update this if your CSV has a different filename
TEMP_ROWS = []

# Your GitHub details to generate raw links
GITHUB_USERNAME = "Sehrish Mughal"
GITHUB_REPO = "OnlineStore"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def process_single_url(img_url, product_id, suffix=""):
    """Downloads a single image from Markaz if it doesn't exist, and returns the GitHub Raw URL."""
    img_url = img_url.strip()
    if not img_url or "static.markaz.app" not in img_url:
        return img_url # Return original if empty or not a Markaz link

    file_extension = ".jpg" if ".jpeg" not in img_url.lower() else ".jpeg"
    local_filename = f"prod_{product_id}{suffix}{file_extension}"
    local_filepath = os.path.join(IMAGE_DIR, local_filename)
    new_raw_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{IMAGE_DIR}/{local_filename}"

    if os.path.exists(local_filepath):
        return new_raw_url

    print(f"Downloading: Product {product_id} {suffix}...")
    try:
        response = requests.get(img_url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            with open(local_filepath, 'wb') as img_file:
                img_file.write(response.content)
            time.sleep(1) # Rate-limiting safety pause
            return new_raw_url
        else:
            print(f"Warning: Could not download asset. Status: {response.status_code}")
            return img_url
    except Exception as e:
        print(f"Error downloading image for product {product_id}: {e}")
        return img_url

print("Starting bulk image and secondary asset optimization script...")

with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    fieldnames = reader.fieldnames
    
    for row in reader:
        product_id = row.get('id', '').strip()
        
        # 1. Handle Primary Image Link
        main_img = row.get('image_link', '')
        if main_img:
            row['image_link'] = process_single_url(main_img, product_id, suffix="")
            
        # 2. Handle Additional Image Links (Can contain multiple comma-separated URLs)
        add_img_cell = row.get('additional_image_link', '')
        if add_img_cell:
            # Split by comma in case there are multiple gallery images
            urls = [url.strip() for url in add_img_cell.split(',') if url.strip()]
            updated_urls = []
            
            for index, url in enumerate(urls):
                # Use a suffix like _alt_0, _alt_1 to keep file names unique
                new_url = process_single_url(url, product_id, suffix=f"_alt_{index}")
                updated_urls.append(new_url)
            
            # Join them right back with commas
            row['additional_image_link'] = ",".join(updated_urls)
                    
        TEMP_ROWS.append(row)

# Overwrite the CSV with updated clean URLs
with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(TEMP_ROWS)

print("All processing for primary and additional images complete!")
