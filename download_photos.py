import pandas as pd
import requests
import os
import re

# Configuration
DEFAULT_CSV_PATH = r"c:\Users\VAMSI\OneDrive\Desktop\Contact Information.csv"
OUTPUT_DIR = "downloaded_photos"

def get_drive_file_id(url):
    """Extract file ID from Google Drive URL."""
    if not url or pd.isna(url) or str(url).strip() == '':
        return None
    
    url = str(url)
    
    # Clean up URL (remove /u/1/, /u/2/ etc that cause auth redirects)
    url = re.sub(r'/u/\d+/', '/', url)
    
    # Pattern 1: ?id=FILE_ID or &id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    # Pattern 2: /d/FILE_ID/ (sharing links)
    if '/d/' in url:
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
            
    # Pattern 3: forms_web links sometimes hide id differently or need cleaning
    # https://drive.google.com/open?id=...
    return None

def download_file(file_id, save_path):
    """Download file from Google Drive with confirmation token handling."""
    try:
        session = requests.Session()
        url = "https://drive.google.com/uc?export=download"
        params = {'id': file_id}
        
        response = session.get(url, params=params, stream=True)
        
        # Handle "File too large" / "Virus scan" confirmation
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        
        if token:
            params['confirm'] = token
            response = session.get(url, params=params, stream=True)
            
        if response.status_code == 200:
            # Check content type to ensure it's not HTML (login page)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                print("Error: Link returned HTML (login page). Check sharing permissions.")
                return False
                
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(32768):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            print(f"Failed to download. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error downloading {file_id}: {e}")
        return False

def main():
    print("--- AI Karyashala Photo Downloader ---")
    
    csv_path = input(f"Enter CSV path (Press Enter for default: {DEFAULT_CSV_PATH}): ").strip()
    if not csv_path:
        csv_path = DEFAULT_CSV_PATH
        
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    # Create output directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    print("Reading CSV...")
    df = pd.read_csv(csv_path)
    # Standardize headers
    df.columns = [c.strip().lower() for c in df.columns]
    
    print(f"Found {len(df)} students. Starting download...")
    
    success_count = 0
    fail_count = 0
    
    for index, row in df.iterrows():
        # Get Student Details - More robust mapping
        roll = str(row.get('roll no', row.get('roll_no', row.get('roll number', 'N/A')))).strip().upper()
        name = str(row.get('name', 'Unknown')).strip()
        
        # Smart detection of photo column
        photo_url = None
        for col in df.columns:
            if any(term in col for term in ['image', 'photo', 'link', 'drive', 'upload', 'passport']):
                photo_url = row.get(col)
                break
        
        if roll == 'N/A' or not photo_url:
            print(f"Skipping row {index+1}: Missing Roll No or Photo URL")
            fail_count += 1
            continue
            
        file_id = get_drive_file_id(photo_url)
        if not file_id:
            print(f"Skipping {roll} ({name}): Invalid Google Drive URL")
            fail_count += 1
            continue
            
        # Determine filename (defaulting to .jpg, but content checking would be better. 
        # For simplicity, we save as .jpg or .png based on basic assumption or just no ext and let viewer handle it?
        # Let's verify content type header to guess extension if possible, but for now app handles conversion.
        # Let's save as .jpg by default or try to guess. 
        # Actually Google Drive download usually has content-disposition with filename.
        # But to match requirements, we force rename to Roll Number.
        # We will append .jpg as safe default, user can fix if needed.
        # Or even better: convert_image_to_base64 in app handles it regardless of extension correctness often.
        save_name = f"{roll}.jpg"
        save_path = os.path.join(OUTPUT_DIR, save_name)
        
        print(f"Downloading photo for {roll} ({name})...", end=" ")
        if download_file(file_id, save_path):
            print("✅ Done")
            success_count += 1
        else:
            print("❌ Failed")
            fail_count += 1
            
    print("\n" + "="*40)
    print(f"Download Complete!")
    print(f"Successful: {success_count}")
    print(f"Failed:     {fail_count}")
    print(f"Photos saved in folder: {os.path.abspath(OUTPUT_DIR)}")
    print("="*40)
    print("Now you can ZIP this folder and upload it to the app!")

if __name__ == "__main__":
    main()
