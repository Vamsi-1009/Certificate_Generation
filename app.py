from flask import Flask, render_template, request
import pandas as pd
import uuid
import qrcode
import base64
import cairosvg
import os
import re
import requests
import zipfile
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Upgraded Professional SVG Template
SVG_TEMPLATE = """
<svg width="3508" height="2480" viewBox="0 0 3508 2480" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#2563eb;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#1e3a8a;stop-opacity:1" />
        </linearGradient>
        <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#2563eb;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#172554;stop-opacity:1" />
        </linearGradient>
    </defs>
    
    <!-- Background -->
    <rect width="3508" height="2480" fill="#ffffff"/>
    
    <!-- Outer Gradient Border (Width 40) -->
    <rect x="20" y="20" width="3468" height="2440" fill="none" stroke="url(#borderGrad)" stroke-width="40"/>
    
    <!-- Inner Thin Border -->
    <rect x="60" y="60" width="3388" height="2360" fill="none" stroke="#93c5fd" stroke-width="5"/>

    <!-- ================= ID CARD SECTION (Left) ================= -->
    <g transform="translate(250, 1300)">
        <!-- Lanyard Strap (fully extended to top) -->
        <rect x="190" y="-1300" width="120" height="1350" fill="#1e40af"/>
        <!-- Clip -->
        <rect x="170" y="10" width="160" height="60" fill="#94a3b8"/>
        
        <!-- ID Card Body -->
        <rect x="0" y="50" width="500" height="950" rx="30" fill="url(#cardGrad)" filter="drop-shadow(10px 10px 20px rgba(0,0,0,0.5))"/>
        
        <!-- Header Strip -->
        <rect x="0" y="50" width="500" height="250" rx="30" fill="rgba(255,255,255,0.1)"/>
        <!-- Header Text -->
        <text x="40" y="190" font-family="Arial, sans-serif" font-weight="bold" font-size="50" fill="#ffffff">AI Karyashala</text>
        
        <!-- Photo Container -->
        <rect x="90" y="320" width="320" height="400" fill="#ffffff"/>
        <!-- User Photo -->
        <image x="100" y="330" width="300" height="380" href="{photo_base64}" preserveAspectRatio="xMidYMid slice"/>
        
        <!-- QR Code Centered under image -->
        <rect x="175" y="740" width="150" height="150" fill="#ffffff"/>
        <image x="180" y="745" width="140" height="140" href="{qr_base64}"/>
    </g>

    <!-- ================= MAIN CERTIFICATE TEXT (Right) ================= -->
    <!-- Center text around x=2100 -->
    
    <!-- Certificate ID (Top Right) -->
    <text x="3300" y="200" font-family="Arial, sans-serif" font-size="40" fill="#64748b" text-anchor="end">Certificate ID: {cert_id}</text>
    
    <!-- Main Header -->
    <text x="2100" y="500" font-family="Georgia, serif" font-weight="bold" font-size="100" fill="#172554" text-anchor="middle">CERTIFICATE OF PARTICIPATION</text>
    <line x1="1300" y1="540" x2="2900" y2="540" stroke="#2563eb" stroke-width="5"/>
    
    <!-- Event Name -->
    <text x="2100" y="720" font-family="Arial, sans-serif" font-weight="bold" font-size="90" fill="#1e40af" text-anchor="middle">AI KARYASHALA</text>
    <text x="2100" y="810" font-family="Arial, sans-serif" font-size="60" fill="#3b82f6" text-anchor="middle">AI Awareness &amp; Hands-on Bootcamp</text>
    
    <!-- Student Name -->
    <text x="2100" y="1100" font-family="Georgia, serif" font-weight="bold" font-size="160" fill="#0f172a" text-anchor="middle">{name}</text>
    <line x1="1500" y1="1130" x2="2700" y2="1130" stroke="#1e3a8a" stroke-width="4"/>
    
    <!-- Body Text -->
    <text x="2100" y="1300" font-family="Times New Roman, serif" font-style="italic" font-size="55" fill="#374151" text-anchor="middle">has participated in the "AI KARYASHALA"</text>
    <text x="2100" y="1380" font-family="Times New Roman, serif" font-weight="bold" font-size="55" fill="#374151" text-anchor="middle">AI Awareness &amp; Hands-on Bootcamp</text>
    <text x="2100" y="1460" font-family="Times New Roman, serif" font-style="italic" font-size="55" fill="#374151" text-anchor="middle">conducted at</text>
    <text x="2100" y="1540" font-family="Times New Roman, serif" font-weight="bold" font-size="60" fill="#1f2937" text-anchor="middle">KIET, KAKINADA.</text>

    <!-- Footer Line -->
    <line x1="1000" y1="2100" x2="3200" y2="2100" stroke="#e2e8f0" stroke-width="2"/>
    
    <!-- Signature -->
    <text x="3100" y="2070" font-family="Arial, sans-serif" font-weight="bold" font-size="45" fill="#1f2937" text-anchor="end">Coordinator / Trainer</text>
    <!-- Fixed Signature Image -->
    <image x="2600" y="1850" width="550" height="180" href="{signature_base64}"/>
    
</svg>
"""

def get_wrapped_name_svg(name, max_chars=12):
    """Wrap name for ID card into SVG tspans."""
    # If first name is long, just use first name
    words = name.split()
    if not words: return "", 50
    
    # If single word is very long
    if len(name) <= max_chars:
        return f'<tspan x="250" dy="1.2em">{name}</tspan>', 50
    
    # Split into two lines
    line1 = words[0]
    line2 = " ".join(words[1:]) if len(words) > 1 else ""
    
    if not line2:
        return f'<tspan x="250" dy="1.2em">{line1}</tspan>', 40
        
    return f'<tspan x="250" dy="0">{line1}</tspan><tspan x="250" dy="1.1em">{line2}</tspan>', 40

def get_qr_base64(name, roll, date, cert_id):
    raw_data = f"{name};{roll};{date};{cert_id}"
    encoded_data = base64.urlsafe_b64encode(raw_data.encode()).decode()
    domain = request.host_url.rstrip('/')
    url = f"{domain}/v#{encoded_data}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

def get_photo_from_drive(drive_url):
    """Download photo from Google Drive link and return as base64 data URI."""
    if not drive_url or pd.isna(drive_url) or str(drive_url).strip() == '':
        return ""
    
    try:
        # Extract file ID from various Google Drive URL formats
        drive_url = str(drive_url)
        
        # Pattern 1: ?id=FILE_ID or &id=FILE_ID
        match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_url)
        if match:
            file_id = match.group(1)
        # Pattern 2: /d/FILE_ID/ (sharing links)
        elif '/d/' in drive_url:
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_url)
            file_id = match.group(1) if match else None
        else:
            print(f"Could not extract file ID from: {drive_url}")
            return ""
        
        if not file_id:
            return ""
        
        # Use session to handle cookies for large file confirmation
        session = requests.Session()
        
        # First attempt - direct download
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(download_url, timeout=15)
        
        # Check if we got a confirmation page (for large files or virus scan)
        if b'confirm=' in response.content or b'download_warning' in response.text.encode():
            # Extract confirm token and retry
            confirm_match = re.search(r'confirm=([a-zA-Z0-9_-]+)', response.text)
            if confirm_match:
                confirm_token = confirm_match.group(1)
                download_url = f"https://drive.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
                response = session.get(download_url, timeout=15)
        
        # Verify we got actual image data (not HTML)
        content_type = response.headers.get('Content-Type', '')
        if response.status_code == 200 and 'image' in content_type:
            return f"data:image/png;base64,{base64.b64encode(response.content).decode()}"
        
        # Fallback: Check if content looks like an image (starts with image magic bytes)
        if response.status_code == 200:
            content = response.content
            # Check for common image signatures (JPEG, PNG, GIF, WebP)
            if (content[:3] == b'\xff\xd8\xff' or  # JPEG
                content[:8] == b'\x89PNG\r\n\x1a\n' or  # PNG
                content[:6] in (b'GIF87a', b'GIF89a') or  # GIF
                content[:4] == b'RIFF'):  # WebP
                return f"data:image/png;base64,{base64.b64encode(content).decode()}"
        
        print(f"Failed to download valid image for file_id: {file_id}")
        return ""
    except Exception as e:
        print(f"Error downloading photo: {e}")
        return ""

def convert_image_to_base64(image_bytes):
    """Convert any image format to PNG base64 data URI."""
    if not image_bytes:
        return ""
    try:
        img = Image.open(BytesIO(image_bytes))
        # Convert to RGB if necessary (for RGBA or P mode images)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        # Save as PNG
        buf = BytesIO()
        img.save(buf, format='PNG')
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    except Exception as e:
        print(f"Error converting image: {e}")
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    name = request.form.get('name', '').upper()
    roll = request.form.get('roll_no', '')
    date = request.form.get('date', '') # We still get it from form, but template ignores it per request
    photo_file = request.files.get('photo')
    
    cert_id = f"AIK{roll}"
    qr_b64 = get_qr_base64(name, roll, date, cert_id)
    photo_b64 = f"data:image/png;base64,{base64.b64encode(photo_file.read()).decode()}" if photo_file else ""

    # Get fixed signature
    with open("signature.png", "rb") as f:
        sig_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

    svg_data = SVG_TEMPLATE.format(name=name, roll_no=roll, photo_base64=photo_b64, qr_base64=qr_b64, cert_id=cert_id, signature_base64=sig_b64)
    png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
    b64_img = base64.b64encode(png_data).decode()
    
    certs = [{'name': name, 'roll': roll, 'image': f"data:image/png;base64,{b64_img}", 'cert_id': cert_id}]
    return render_template('results.html', certificates=certs)

@app.route('/bulk_generate', methods=['POST'])
def bulk_generate():
    file = request.files.get('csv_file')
    if not file: return "No file", 400
    
    df = pd.read_csv(file)
    
    # NEW: Standardize Google Form column names by making them lowercase and stripping spaces
    df.columns = [c.strip().lower() for c in df.columns]
    
    certificates = []
    for _, row in df.iterrows():
        # NEW: Handle Google Form Mapping (accepts both 'roll_no' and 'roll no')
        name = str(row.get('name', 'Unknown')).upper()
        roll = str(row.get('roll no', row.get('roll_no', row.get('roll number', row.get('registration number', 'N/A')))))
        
        cert_id = f"AIK{roll}"
        
        # Get date from Timestamp if a 'date' column doesn't exist
        full_timestamp = str(row.get('timestamp', ''))
        date_val = str(row.get('date', full_timestamp.split(' ')[0]))

        qr_b64 = get_qr_base64(name, roll, date_val, cert_id)
        
        # NEW: Fetch photo from Google Drive if 'image' column exists
        photo_url = row.get('image', row.get('photo', ''))
        photo_b64 = get_photo_from_drive(photo_url)
        
        # SVG creation with photo from Drive
        # Get fixed signature
        with open("signature.png", "rb") as f:
            sig_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

        svg_data = SVG_TEMPLATE.format(
            name=name, 
            roll_no=roll, 
            photo_base64=photo_b64, 
            qr_base64=qr_b64, 
            cert_id=cert_id,
            signature_base64=sig_b64
        )
        
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        
        certificates.append({
            'name': name, 
            'roll': roll, 
            'image': f"data:image/png;base64,{base64.b64encode(png_data).decode()}",
            'cert_id': cert_id
        })
    return render_template('results.html', certificates=certificates)

@app.route('/bulk_generate_zip', methods=['POST'])
def bulk_generate_zip():
    """Bulk generate certificates with photos from ZIP file."""
    csv_file = request.files.get('csv_file')
    zip_file = request.files.get('photos_zip')
    
    if not csv_file:
        return "No CSV file provided", 400
    
    df = pd.read_csv(csv_file)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Load photos from ZIP into a dictionary (filename -> base64)
    photos = {}
    if zip_file:
        try:
            with zipfile.ZipFile(BytesIO(zip_file.read()), 'r') as zf:
                for filename in zf.namelist():
                    # Skip directories and hidden files
                    if filename.endswith('/') or filename.startswith('__') or filename.startswith('.'):
                        continue
                    # Get just the filename without extension for matching
                    name_without_ext = os.path.splitext(os.path.basename(filename))[0].strip().upper()
                    try:
                        image_bytes = zf.read(filename)
                        photo_b64 = convert_image_to_base64(image_bytes)
                        if photo_b64:
                            photos[name_without_ext] = photo_b64
                            print(f"Loaded photo: {name_without_ext}")
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")
        except Exception as e:
            print(f"Error opening ZIP: {e}")
    
    certificates = []
    for _, row in df.iterrows():
        name = str(row.get('name', 'Unknown')).upper()
        roll = str(row.get('roll no', row.get('roll_no', row.get('roll number', row.get('registration number', 'N/A'))))).strip().upper()
        
        cert_id = f"AIK{roll}"
        
        full_timestamp = str(row.get('timestamp', ''))
        date_val = str(row.get('date', full_timestamp.split(' ')[0]))
        
        qr_b64 = get_qr_base64(name, roll, date_val, cert_id)
        
        # Try to match photo by roll number (exact match)
        photo_b64 = photos.get(roll, '')
        
        if not photo_b64:
            # Try to match by name (exact match)
            photo_b64 = photos.get(name.replace(' ', ''), '')
            
        if not photo_b64:
            # Fuzzy match: Checking if student name is IN the filename
            # Google Forms output example: "My File - Student Name.jpg"
            for filename_key, b64_data in photos.items():
                # Check if NAME is in the filename (ignoring case/spaces)
                clean_filename = filename_key.replace(' ', '').replace('-', '').upper()
                clean_name = name.replace(' ', '').upper()
                
                # Check if name appears in filename (minimum 4 chars to avoid false positives)
                if len(clean_name) > 3 and clean_name in clean_filename:
                    photo_b64 = b64_data
                    print(f"Fuzzy match: {name} found in {filename_key}")
                    break
        
        # Get fixed signature
        with open("signature.png", "rb") as f:
            sig_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

        svg_data = SVG_TEMPLATE.format(
            name=name, 
            roll_no=roll, 
            photo_base64=photo_b64, 
            qr_base64=qr_b64, 
            cert_id=cert_id,
            signature_base64=sig_b64
        )
        
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        
        certificates.append({
            'name': name, 
            'roll': roll, 
            'image': f"data:image/png;base64,{base64.b64encode(png_data).decode()}",
            'cert_id': cert_id
        })
    
    return render_template('results.html', certificates=certificates)

@app.route('/download_photos_from_csv', methods=['POST'])
def download_photos_from_csv():
    """Tool: Upload CSV -> Get ZIP of renamed photos."""
    file = request.files.get('csv_file')
    if not file: return "No file", 400
    
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Create in-memory ZIP
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        
        session = requests.Session()
        success_count = 0
        photo_col = None
        
        # Smart detection of photo column
        for col in df.columns:
            if any(term in col for term in ['image', 'photo', 'link', 'drive', 'upload', 'passport']):
                photo_col = col
                print(f"Detected photo column: {photo_col}")
                break
        
        if not photo_col:
            print("Error: No photo column found in CSV!")
            # We return early or just let it finish (which results in empty zip)
        else:
            for _, row in df.iterrows():
                roll = str(row.get('roll no', row.get('roll_no', row.get('roll number', row.get('registration number', 'N/A'))))).strip().upper()
                photo_url = row.get(photo_col, '')
                
                if roll == 'N/A' or not photo_url or pd.isna(photo_url):
                    continue
                    
                # Logic to extract ID and download
                photo_url = str(photo_url)
                photo_url = re.sub(r'/u/\d+/', '/', photo_url)
                
                file_id = None
                match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', photo_url)
                if match: file_id = match.group(1)
                elif '/d/' in photo_url:
                    match = re.search(r'/d/([a-zA-Z0-9_-]+)', photo_url)
                    if match: file_id = match.group(1)
                    
                if not file_id: continue
                
                try:
                    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    resp = session.get(download_url, timeout=15)
                    
                    if b'download_warning' in resp.content or b'confirm=' in resp.content:
                         match_confirm = re.search(r'confirm=([a-zA-Z0-9_-]+)', resp.text)
                         if match_confirm:
                             download_url += f"&confirm={match_confirm.group(1)}"
                             resp = session.get(download_url, timeout=15)
                    
                    if resp.status_code == 200:
                        ct = resp.headers.get('Content-Type', '').lower()
                        if 'text/html' not in ct:
                            filename = f"{roll}.jpg"
                            zf.writestr(filename, resp.content)
                            success_count += 1
                            print(f"Downloaded: {filename}")
                except Exception as e:
                    print(f"Error zipping {roll}: {e}")
        
        if success_count == 0:
            print("WARNING: Zero photos were successfully downloaded and zipped.")

                
    memory_file.seek(0)
    
    from flask import send_file
    return send_file(memory_file, download_name='student_photos.zip', as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
