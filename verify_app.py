import requests
import os
import csv
import zipfile
from io import BytesIO

BASE_URL = "http://127.0.0.1:5002"

def test_index():
    print("Testing Index Page...")
    try:
        resp = requests.get(BASE_URL)
        if resp.status_code == 200:
            print("✅ Index Page Load Success")
        else:
            print(f"❌ Index Page Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_single_generation():
    print("\nTesting Single Generation...")
    
    # Create a dummy image for upload
    img = BytesIO()
    from PIL import Image
    image = Image.new('RGB', (100, 100), color = 'red')
    image.save(img, format='PNG')
    img.seek(0)
    
    files = {'photo': ('test.png', img, 'image/png')}
    data = {
        'name': 'TEST USER',
        'roll_no': '12345',
        'date': '2024-01-01'
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/generate", data=data, files=files)
        if resp.status_code == 200 and 'TEST USER' in resp.text:
            print("✅ Single Generation Success")
        else:
            print(f"❌ Single Generation Failed: {resp.status_code}")
            # print(resp.text[:500])
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_bulk_generation():
    print("\nTesting Bulk Generation...")
    
    # Create dummy CSV
    csv_content = "Name,Roll No,Date\nBulk User 1,B001,2024-01-01\nBulk User 2,B002,2024-01-01"
    csv_file = BytesIO(csv_content.encode())
    
    files = {'csv_file': ('test.csv', csv_file, 'text/csv')}
    
    try:
        resp = requests.post(f"{BASE_URL}/bulk_generate", files=files)
        if resp.status_code == 200 and 'Bulk User 1' in resp.text:
            print("✅ Bulk Generation Success")
        else:
            print(f"❌ Bulk Generation Failed: {resp.status_code}")
            print(f"Response Preview: {resp.text[:1000]}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_bulk_zip_generation():
    print("\nTesting Bulk ZIP Generation...")
    
    # Create dummy CSV
    csv_content = "Name,Roll No,Date\nZip User 1,Z001,2024-01-01"
    csv_file = BytesIO(csv_content.encode())
    
    # Create dummy ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr('Z001.jpg', b'dummy content') # simple content
    zip_buffer.seek(0)
    
    files = {
        'csv_file': ('test_zip.csv', csv_file, 'text/csv'),
        'photos_zip': ('photos.zip', zip_buffer, 'application/zip')
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/bulk_generate_zip", files=files)
        if resp.status_code == 200 and 'Zip User 1' in resp.text:
            print("✅ Bulk ZIP Generation Success")
        else:
            print(f"❌ Bulk ZIP Generation Failed: {resp.status_code}")
            print(f"Response Preview: {resp.text[:1000]}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_index()
    test_single_generation()
    test_bulk_generation()
    test_bulk_zip_generation()
