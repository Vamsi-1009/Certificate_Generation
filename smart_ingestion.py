import os
import pandas as pd
import zipfile
import re
import io
import shutil
import base64
from PIL import Image

import requests

class SmartIngestor:
    def __init__(self):
        self.data_df = None
        self.photos_map = {} # {normalized_name: base64_data}

    def process_data_file(self, file_path):
        """Intelligently parse CSV, Excel, or PDF into a DataFrame."""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.csv':
                self.data_df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                self.data_df = pd.read_excel(file_path)
            elif ext == '.pdf':
                self.data_df = self._parse_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            # Normalize columns
            self._normalize_columns()
            print(f"DEBUG INGESTOR: Columns after norm: {self.data_df.columns}")
            print(f"DEBUG INGESTOR: First record: {self.data_df.iloc[0].to_dict() if not self.data_df.empty else 'EMPTY'}")
            return True, f"Successfully loaded {len(self.data_df)} records."
        except Exception as e:
            return False, str(e)

    def _parse_pdf(self, file_path):
        """Extract table data from PDF using pdfplumber."""
        import pdfplumber
        data = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Simple heuristic: Row must have at least 2 non-empty cells to be data
                        if len([c for c in row if c]) >= 2:
                            data.append(row)
        
        if not data:
            raise ValueError("No tabular data found in PDF")

        # Assume first row is header if it looks like one (contains 'Name' or 'Roll')
        header = data[0]
        # Clean header
        header = [str(h).strip() for h in header]
        
        # Check if first row is actually header
        is_header = any('NAME' in h.upper() for h in header) or any('ROLL' in h.upper() for h in header)
        
        if is_header:
            df = pd.DataFrame(data[1:], columns=header)
        else:
            # Generate generic columns
            df = pd.DataFrame(data)
            # Try to identify columns by content? For now leave generic
        
        return df

    def _normalize_columns(self):
        """Standardize column names to 'name', 'roll', 'image'."""
        if self.data_df is None: return
        
        # Lowercase and strip
        self.data_df.columns = [str(c).strip().lower() for c in self.data_df.columns]
        
        # Rename common variations
        rename_map = {}
        for col in self.data_df.columns:
            if 'roll' in col or 'registration' in col:
                rename_map[col] = 'roll'
            elif 'name' in col and 'file' not in col: # avoid 'filename'
                rename_map[col] = 'name'
            elif any(x in col for x in ['image', 'photo', 'pic']):
                rename_map[col] = 'image'
        
        if rename_map:
            self.data_df.rename(columns=rename_map, inplace=True)
            
        # Ensure name and roll exist
        if 'name' not in self.data_df.columns:
            # Heuristic: First column with string text might be name?
            # For safety, just create Unknown if missing
            pass
            
    def process_images(self, zip_path=None, loose_folder=None):
        """Load images and map them to students using parallel processing."""
        import concurrent.futures
        
        raw_photos = {} # filename -> bytes
        
        # Load from ZIP
        if zip_path and os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for file in zf.namelist():
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        name = os.path.basename(file)
                        raw_photos[name] = zf.read(file)
                        
        # Load from Folder
        if loose_folder and os.path.exists(loose_folder):
            for file in os.listdir(loose_folder):
                 if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                     with open(os.path.join(loose_folder, file), 'rb') as f:
                        raw_photos[file] = f.read()

        # Match to Data
        if self.data_df is None: return "No data loaded yet."
        
        matched_count = 0
        
        # Parallel Execution for per-row processing
        # We prefer ThreadPool for network operations (downloading images)
        print("DEBUG: Starting parallel image processing...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # Create list of rows to avoid pandas iterrows overhead in thread
            rows = [row for _, row in self.data_df.iterrows()]
            
            # Submit all tasks
            future_to_row = {executor.submit(self._process_single_row, row, raw_photos): row for row in rows}
            
            for future in concurrent.futures.as_completed(future_to_row):
                try:
                    result = future.result()
                    if result:
                        key, b64 = result
                        self.photos_map[key] = b64
                        matched_count += 1
                except Exception as exc:
                    print(f"DEBUG: Row processing generated an exception: {exc}")

        print(f"DEBUG: Parallel processing matched {matched_count} images.")
        return matched_count

    def _process_single_row(self, row, raw_photos):
        """Helper to process a single row: find locally or download."""
        roll = str(row.get('roll', 'N/A')).strip().upper()
        name = str(row.get('name', 'Unknown')).strip().upper()
        
        photo_bytes = None
        
        # 1. Exact Roll Match (in local raw_photos)
        if roll != 'N/A':
            for fname, pbytes in raw_photos.items():
                base = os.path.splitext(fname)[0].upper()
                if roll in base:
                    photo_bytes = pbytes
                    break
        
        # 2. Exact Name Match (in local raw_photos)
        if not photo_bytes:
             for fname, pbytes in raw_photos.items():
                if not pbytes: continue
                # clean filename
                clean_fname = re.sub(r'[^A-Z0-9]', '', os.path.splitext(fname)[0].upper())
                clean_name = re.sub(r'[^A-Z0-9]', '', name)
                if clean_name and clean_name in clean_fname and len(clean_name) > 3:
                    photo_bytes = pbytes
                    break
        
        # 3. Image URL/Path in CSV (Google Drive logic)
        # This is the slow part that benefits from threads
        if not photo_bytes and 'image' in row:
            img_ref = str(row['image'])
            if 'http' in img_ref:
                # Check for Google Drive URL
                file_id = None
                if 'drive.google.com' in img_ref:
                    # Extract ID
                    patterns = [
                        r'id=([a-zA-Z0-9_-]+)',
                        r'/d/([a-zA-Z0-9_-]+)',
                        r'/open\?id=([a-zA-Z0-9_-]+)'
                    ]
                    for p in patterns:
                        match = re.search(p, img_ref)
                        if match:
                            file_id = match.group(1)
                            break
                
                if file_id:
                    download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
                    try:
                        # Shorter timeout for bulk processing to avoid hanging everything
                        response = requests.get(download_url, timeout=5)
                        if response.status_code == 200:
                            photo_bytes = response.content
                    except Exception as e:
                        print(f"DEBUG: Exception downloading image for {name}: {e}")
        
        if photo_bytes:
            b64 = self._bytes_to_base64(photo_bytes)
            if b64:
                # Store in map using Roll (preferred) or Name
                key = roll if roll != 'N/A' else name
                return (key, b64)
        return None

    def _bytes_to_base64(self, data):
        try:
             # Validate image
             img = Image.open(io.BytesIO(data))
             if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
             buf = io.BytesIO()
             # Resize if too huge to save memory
             if img.width > 800:
                 ratio = 800 / img.width
                 new_h = int(img.height * ratio)
                 img = img.resize((800, new_h), Image.Resampling.LANCZOS)
                 
             img.save(buf, format='JPEG', quality=85) # Convert to JPEG 85 to save zip size
             return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except Exception as e:
            # print(f"DEBUG: Image validation failed: {e}")
            return None

    def get_records(self):
        """Return list of dicts with integrated photo data."""
        records = []
        if self.data_df is None: return []
        
        for _, row in self.data_df.iterrows():
            rec = row.to_dict()
            # Clean keys
            clean_rec = {}
            for k,v in rec.items():
                clean_rec[k.lower()] = v
                
            roll = str(clean_rec.get('roll', 'N/A')).strip().upper()
            name = str(clean_rec.get('name', 'Unknown')).strip().upper()
            
            # Find photo
            photo = self.photos_map.get(roll)
            if not photo:
                photo = self.photos_map.get(name)
            
            clean_rec['photo_base64'] = photo if photo else ""
            records.append(clean_rec)
        return records

if __name__ == "__main__":
    # Test stub
    print("Smart Ingestor Module")
    # Simple test if file exists
    test_csv = "Contact Information.csv"
    if os.path.exists(test_csv):
        print(f"Testing with {test_csv}...")
        ingestor = SmartIngestor()
        success, msg = ingestor.process_data_file(test_csv)
        if success:
            count = ingestor.process_images()
            print(f"Matched {count} images.")
            records = ingestor.get_records()
            if records:
                print(f"Sample Record Photo Length: {len(records[0].get('photo_base64', ''))}")
        else:
            print(f"Failed to process CSV: {msg}")
