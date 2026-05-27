import os
import csv
import requests

# Setup directories
IMAGE_DIR = "images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

CSV_FILE = "markaz_catalog.csv"  # Rename this if your CSV file has a different name
TEMP_ROWS = []

# Headers to mimic a real web browser to bypass the scraper block
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Starting automated image sync...")

with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    fieldnames = reader.fieldnames
    
    for row in reader:
        img_url = row.get('image_link', '')
        product_id = row.get('id', '')
        
        # Check if the image link belongs to Markaz
        if "static.markaz.app" in img_url:
            print(f"Processing image for Product ID: {product_id}")
            
            # Formulate a clean filename
            file_extension = ".jpg" if ".jpeg" not in img_url.lower() else ".jpeg"
            local_filename = f"prod_{product_id}{file_extension}"
            local_filepath = os.path.join(IMAGE_DIR, local_filename)
            
            try:
                # Download image using human-like headers
                response = requests.get(img_url, headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    with open(local_filepath, 'wb') as img_file:
                        img_file.write(response.content)
                    
                    # UPDATE THIS VALUE: Replace username and repo with your actual GitHub details
                    github_username = "Sehrish Mughal"
                    github_repo = "OnlineStore"
                    
                    # Rewrite the CSV cell to point to your repo's raw asset folder
                    new_raw_url = f"https://raw.githubusercontent.com/{github_username}/{github_repo}/main/{IMAGE_DIR}/{local_filename}"
                    row['image_link'] = new_raw_url
                    print(f"Successfully moved image to: {new_raw_url}")
                else:
                    print(f"Failed to fetch image. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error handling product {product_id}: {e}")
                
        TEMP_ROWS.append(row)

# Rewrite the CSV file with the updated GitHub Raw URLs
with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(TEMP_ROWS)

print("Image sync complete!")
