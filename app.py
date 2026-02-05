from flask import Flask, render_template, request
import pandas as pd
import shutil
from smart_ingestion import SmartIngestor
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
import time

app = Flask(__name__)

# Upgraded Professional SVG Template

def load_svg_template():
    """Load the SVG template from the file."""
    template_path = os.path.join(app.root_path, 'templates', 'certificate_template.svg')
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()



def get_wrapped_name_svg(name):
    """Wrap name for ID card into SVG tspans with dynamic font size."""
    words = name.split()
    if not words: return "", 50
    
    full_name_len = len(name)
    
    # Case 1: Short name (1 line)
    if full_name_len <= 15:
        return f'<tspan x="300" dy="1.2em">{name}</tspan>', 45
    
    # Case 2: Medium name (2 lines) - split evenly-ish
    if full_name_len <= 30:
        mid = len(words) // 2
        if len(words) > 1:
            line1 = " ".join(words[:mid+1]) if mid < len(words) else " ".join(words) # bias to top line slightly or just simple split
            # Better split logic: fill line 1
            line1 = words[0]
            line2_words = words[1:]
            
            # Try to balance if multiple words
            current_len = len(line1)
            idx = 1
            while idx < len(words):
                if current_len + 1 + len(words[idx]) < 18: # arbitrary char limit for top line
                    line1 += " " + words[idx]
                    current_len += 1 + len(words[idx])
                    idx += 1
                else:
                    break
            line2 = " ".join(words[idx:])
            return f'<tspan x="300" dy="0">{line1}</tspan><tspan x="300" dy="1.2em">{line2}</tspan>', 40
        else:
             # Single long word
             return f'<tspan x="300" dy="1.2em">{name}</tspan>', 35

    # Case 3: Long name (2-3 lines)
    # Simple strategy: Max 3 lines
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= 18:
            if current_line: current_line += " "
            current_line += word
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    
    if len(lines) == 1:
         return f'<tspan x="300" dy="1.2em">{lines[0]}</tspan>', 35
    elif len(lines) == 2:
         return f'<tspan x="300" dy="0">{lines[0]}</tspan><tspan x="300" dy="1.2em">{lines[1]}</tspan>', 35
    else:
         # 3 or more lines, shrink font
         svg_lines = []
         svg_lines.append(f'<tspan x="300" dy="-0.5em">{lines[0]}</tspan>')
         for l in lines[1:3]: # Take max 3 lines
             svg_lines.append(f'<tspan x="300" dy="1.1em">{l}</tspan>')
         return "".join(svg_lines), 30

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

import traceback

def log_error(e):
    with open("error.log", "a") as f:
        f.write(f"ERROR: {str(e)}\n")
        f.write(traceback.format_exc())
        f.write("\n" + "-"*50 + "\n")
    print(f"ERROR: {e}", file=sys.stderr)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test', methods=['GET', 'POST'])
def test_route():
    print("DEBUG: Entered test_route")
    return "OK", 200

@app.before_request
def log_request_info():
    print(f"DEBUG: Request Path: {request.path} Method: {request.method}")

@app.route('/smart', methods=['POST'])
def smart_generate():
    print("DEBUG: Entered smart_generate")
    """Universal generation route for CSV/Excel/PDF + Images."""
    data_file = request.files.get('data_file') # csv, xlsx, pdf
    photos_zip = request.files.get('photos_zip')
    
    if not data_file:
        return "No data file provided", 400

    ingestor = SmartIngestor()
    
    # Create unique run directory
    run_id = str(uuid.uuid4())
    base_temp_dir = os.path.join(app.root_path, 'temp_runs') # Base temp folder
    run_dir = os.path.join(base_temp_dir, run_id)
    img_out_dir = os.path.join(run_dir, 'certificates')
    os.makedirs(img_out_dir, exist_ok=True)
    
    # Cleanup old runs (older than 1 hour)
    try:
        current_time = time.time()
        for f in os.listdir(base_temp_dir):
            f_path = os.path.join(base_temp_dir, f)
            if os.stat(f_path).st_mtime < current_time - 3600:
                if os.path.isdir(f_path): shutil.rmtree(f_path)
                else: os.remove(f_path)
    except: pass
    
    input_save_path = os.path.join(run_dir, data_file.filename)
    data_file.save(input_save_path)
        
    try:
        # Process Data
        success, msg = ingestor.process_data_file(input_save_path)
        if not success:
            return f"Error processing data file: {msg}", 400
            
        # Process Photos
        if photos_zip:
            photo_zip_path = os.path.join(run_dir, photos_zip.filename)
            photos_zip.save(photo_zip_path)
            ingestor.process_images(zip_path=photo_zip_path)
        
        # Generate Certificates
        records = ingestor.get_records()
        
        # Get fixed signature
        with open("signature.png", "rb") as f:
            sig_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
            
        svg_template = load_svg_template()
        
        count = 0
        for rec in records:
            name = str(rec.get('name', 'Unknown')).upper()
            roll = str(rec.get('roll', 'N/A')).upper()
            date_val = str(rec.get('date', '2024')) 
            
            cert_id = f"AIK{roll}"
            qr_b64 = get_qr_base64(name, roll, date_val, cert_id)
            photo_b64 = rec.get('photo_base64', '')
            
            id_name_content, id_name_fontsize = get_wrapped_name_svg(name)
            svg_data = svg_template.format(
                name=name, 
                roll_no=roll, 
                photo_base64=photo_b64, 
                qr_base64=qr_b64, 
                cert_id=cert_id,
                signature_base64=sig_b64,
                id_name_content=id_name_content,
                id_name_fontsize=id_name_fontsize
            )
            
            png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
            
            # Save PNG to disk
            # Sanitize filename
            safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
            safe_roll = re.sub(r'[^a-zA-Z0-9_\-]', '_', roll)
            filename = f"{safe_roll}_{safe_name}.png"
            with open(os.path.join(img_out_dir, filename), 'wb') as f:
                f.write(png_data)
            count += 1
            
        # Zip the output directory
        shutil.make_archive(img_out_dir, 'zip', img_out_dir)
        final_zip_path = img_out_dir + '.zip'
        
        return send_file(final_zip_path, as_attachment=True, download_name='Certificates.zip')

    except Exception as e:
        log_error(e)
        return f"Internal Server Error: {e}", 500
    # Note: We are relying on the startup cleanup logic to clear this run's files later, 
    # because deleting them immediately after 'return' is tricky with send_file unless using streams.

@app.route('/generate', methods=['POST'])
def generate():
    try:
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

        svg_template = load_svg_template()
        id_name_content, id_name_fontsize = get_wrapped_name_svg(name)
        svg_data = svg_template.format(
            name=name, 
            roll_no=roll, 
            photo_base64=photo_b64, 
            qr_base64=qr_b64, 
            cert_id=cert_id, 
            signature_base64=sig_b64,
            id_name_content=id_name_content,
            id_name_fontsize=id_name_fontsize
        )
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        b64_img = base64.b64encode(png_data).decode()
        
        certs = [{'name': name, 'roll': roll, 'image': f"data:image/png;base64,{b64_img}", 'cert_id': cert_id}]
        return render_template('results.html', certificates=certs)
    except Exception as e:
        log_error(e)
        return f"Internal Server Error: {e}", 500






if __name__ == '__main__':
    print(app.url_map)
    port = int(os.environ.get("PORT", 5003))
    app.run(host='0.0.0.0', port=port)
