import os
import pandas as pd
import zipfile
import re
import io
import shutil
import base64
from PIL import Image

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
        """Load images and map them to students."""
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
        
        # Pre-process raw photos dictionary for faster lookup
        # key: normalized name/roll -> value: filename
        # We store just the normalized keys for fuzzy matching
        
        for idx, row in self.data_df.iterrows():
            roll = str(row.get('roll', 'N/A')).strip().upper()
            name = str(row.get('name', 'Unknown')).strip().upper()
            
            photo_bytes = None
            
            # 1. Exact Roll Match (in filename)
            for fname, pbytes in raw_photos.items():
                base = os.path.splitext(fname)[0].upper()
                if roll in base and roll != 'N/A':
                    photo_bytes = pbytes
                    break
            
            # 2. Exact Name Match
            if not photo_bytes:
                 for fname, pbytes in raw_photos.items():
                    # clean filename
                    clean_fname = re.sub(r'[^A-Z0-9]', '', os.path.splitext(fname)[0].upper())
                    clean_name = re.sub(r'[^A-Z0-9]', '', name)
                    if clean_name in clean_fname and len(clean_name) > 3:
                        photo_bytes = pbytes
                        break
            
            # 3. Image URL/Path in CSV
            if not photo_bytes and 'image' in row:
                img_ref = str(row['image'])
                # logic to download or finding path would go here
                pass
            
            if photo_bytes:
                # Convert to Base64
                b64 = self._bytes_to_base64(photo_bytes)
                # Store in map using Roll (preferred) or Name
                key = roll if roll != 'N/A' else name
                self.photos_map[key] = b64
                matched_count += 1
                
        return matched_count

    def _bytes_to_base64(self, data):
        try:
             # Validate image
             img = Image.open(io.BytesIO(data))
             if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
             buf = io.BytesIO()
             img.save(buf, format='PNG')
             return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except:
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
