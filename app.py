import sys
import flask
from flask import Flask, render_template, request, send_file
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
    # Clean non-ascii
    name = re.sub(r'[^\x00-\x7F]+', '', name).strip()
    
    words = name.split()
    if not words: return "", 50
    
    full_name_len = len(name)
    
    # IMPROVED: Prefer single line if possible up to 20 chars
    if full_name_len <= 20:
        fontsize = 45 if full_name_len <= 15 else 35
        return f'<tspan x="300" dy="1.2em">{name}</tspan>', fontsize
    
    # Case 2: Medium name (2 lines) - split evenly-ish
    if full_name_len <= 35:
        mid = len(words) // 2
        if len(words) > 1:
            line1 = words[0]
            line2_words = words[1:]
            current_len = len(line1)
            idx = 1
            while idx < len(words):
                if current_len + 1 + len(words[idx]) < 18: 
                    line1 += " " + words[idx]
                    current_len += 1 + len(words[idx])
                    idx += 1
                else:
                    break
            line2 = " ".join(words[idx:])
            return f'<tspan x="300" dy="0">{line1}</tspan><tspan x="300" dy="1.2em">{line2}</tspan>', 40
        else:
             # Single long word
             return f'<tspan x="300" dy="1.2em">{name}</tspan>', 30

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

def get_qr_base64(name, roll, date, cert_id, domain=None):
    raw_data = f"{name};{roll};{date};{cert_id}"
    encoded_data = base64.urlsafe_b64encode(raw_data.encode()).decode()
    if not domain:
        # Fallback if no domain passed (e.g. single gen route)
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
        
        # Prepare for Batch Processing
        import subprocess
        import json
        
        # Save records to JSON
        records_path = os.path.join(run_dir, 'records.json')
        with open(records_path, 'w') as f:
            json.dump(records, f)
            
        # Save Metadata
        metadata = {
            'total': len(records),
            'timestamp': time.time(),
            'status': 'processing'
        }
        metadata_path = os.path.join(run_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
            
        # Paths for worker
        template_path = os.path.join(app.root_path, 'templates', 'certificate_template.svg')
        signature_path = os.path.join(app.root_path, 'signature.png')
        domain = request.host_url.rstrip('/')
        
        # Spawn Async Worker
        print("DEBUG: Spawning batch_processor.py details...")
        cmd = [
            sys.executable, 'batch_processor.py', 
            '--run_dir', run_dir,
            '--domain', domain,
            '--template', template_path,
            '--signature', signature_path
        ]
        
        # Use Popen to run in background (independent process)
        # On Windows, we need creationflags=subprocess.DETACHED_PROCESS or shell=True to avoid killing it if parent dies? 
        # Actually standard Popen is fine as long as we don't wait()
        # creationflags=0x00000008 (DETACHED_PROCESS) is good but tricky with console.
        # simple Popen is usually enough for "fire and forget" in this context
        
        subprocess.Popen(cmd)
        
        print("DEBUG: Async worker spawned. Redirecting to preview.")
        return flask.redirect(flask.url_for('preview_route', run_id=run_id))

    except Exception as e:
        log_error(e)
        return f"Internal Server Error: {e}", 500

@app.route('/preview/<run_id>')
def preview_route(run_id):
    """Show preview of generated certificates."""
    base_temp_dir = os.path.join(app.root_path, 'temp_runs')
    run_dir = os.path.join(base_temp_dir, run_id)
    img_out_dir = os.path.join(run_dir, 'certificates')
    metadata_path = os.path.join(run_dir, 'metadata.json')
    
    if not os.path.exists(run_dir):
        return "Run ID not found or expired.", 404
        
    filenames = []
    if os.path.exists(img_out_dir):
        filenames = sorted([f for f in os.listdir(img_out_dir) if f.lower().endswith('.png')])
        
    total_count = 0
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                meta = json.load(f)
                total_count = meta.get('total', 0)
        except: pass
        
    if total_count == 0: total_count = len(filenames) # fallback
    
    return render_template('preview.html', run_id=run_id, filenames=filenames, total_count=total_count, current_count=len(filenames))

@app.route('/download/zip/<run_id>')
def download_zip_route(run_id):
    """Download certificates as ZIP."""
    base_temp_dir = os.path.join(app.root_path, 'temp_runs')
    run_dir = os.path.join(base_temp_dir, run_id)
    img_out_dir = os.path.join(run_dir, 'certificates')
    
    if not os.path.exists(img_out_dir):
        return "Run ID not found.", 404
        
    # Zip the output directory if not already zipped? 
    # Or just re-zip to be safe (or check if exists)
    zip_path = os.path.join(run_dir, 'Certificates.zip')
    if not os.path.exists(zip_path):
        shutil.make_archive(os.path.join(run_dir, 'Certificates'), 'zip', img_out_dir)
        
    return send_file(zip_path, as_attachment=True, download_name='Certificates.zip')

@app.route('/download/pdf/<run_id>')
def download_pdf_route(run_id):
    """Download all certificates merged into one PDF."""
    try:
        base_temp_dir = os.path.join(app.root_path, 'temp_runs')
        run_dir = os.path.join(base_temp_dir, run_id)
        img_out_dir = os.path.join(run_dir, 'certificates')
        
        if not os.path.exists(img_out_dir):
            return "Run ID not found.", 404
            
        pdf_path = os.path.join(run_dir, 'All_Certificates.pdf')
        
        # If already exists, return
        if os.path.exists(pdf_path):
             return send_file(pdf_path, as_attachment=True, download_name='All_Certificates.pdf')
        
        # Generate PDF
        filenames = sorted([f for f in os.listdir(img_out_dir) if f.lower().endswith('.png')])
        if not filenames:
            return "No certificates found to merge.", 404
            
        # Helper to open images
        image_list = []
        for fname in filenames:
            img_path = os.path.join(img_out_dir, fname)
            img = Image.open(img_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            image_list.append(img)
            
        if image_list:
            first_img = image_list[0]
            rest_imgs = image_list[1:]
            first_img.save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=rest_imgs)
            
        return send_file(pdf_path, as_attachment=True, download_name='All_Certificates.pdf')
        
    except Exception as e:
        log_error(e)
        return f"Error generating PDF: {e}", 500

@app.route('/temp_runs/<run_id>/certificates/<filename>')
def serve_temp_image(run_id, filename):
    """Serve individual certificate images for preview."""
    base_temp_dir = os.path.join(app.root_path, 'temp_runs')
    run_dir = os.path.join(base_temp_dir, run_id)
    img_out_dir = os.path.join(run_dir, 'certificates')
    return send_file(os.path.join(img_out_dir, filename))

@app.route('/generate', methods=['POST'])
def generate():
    try:
        raw_name = request.form.get('name', '')
        name = re.sub(r'[^\x00-\x7F]+', '', raw_name).strip().upper()
        if not name: name = "UNKNOWN"
        
        roll = request.form.get('roll_no', '')
        date = request.form.get('date', '') 
        photo_file = request.files.get('photo')
        
        cert_id = f"AIK{roll}"
        qr_b64 = get_qr_base64(name, roll, date, cert_id)
        photo_b64 = f"data:image/png;base64,{base64.b64encode(photo_file.read()).decode()}" if photo_file else ""

        # Main Font Size Calc
        name_len = len(name)
        if name_len <= 15: main_fontsize = 160
        elif name_len <= 20: main_fontsize = 140
        elif name_len <= 30: main_fontsize = 110
        elif name_len <= 40: main_fontsize = 90
        else: main_fontsize = 70

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
            id_name_fontsize=id_name_fontsize,
            main_name_fontsize=main_fontsize,
            date=date
        )
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        b64_img = base64.b64encode(png_data).decode()
        
        certs = [{'name': name, 'roll': roll, 'image': f"data:image/png;base64,{b64_img}", 'cert_id': cert_id}]

        return render_template('results.html', certificates=certs)
    except Exception as e:
        log_error(e)
        return f"Internal Server Error: {e}", 500


def generate_single_certificate(rec, svg_template, sig_b64, img_out_dir, domain):
    """Helper to generate one certificate (render, convert, save)."""
    try:
        raw_name = str(rec.get('name', 'Unknown'))
        name = re.sub(r'[^\x00-\x7F]+', '', raw_name).strip().upper()
        if not name: name = "UNKNOWN"

        roll = str(rec.get('roll', 'N/A')).upper()
        date_val = str(rec.get('date', '08-02-2026')) 
        
        cert_id = f"AIK{roll}"
        qr_b64 = get_qr_base64(name, roll, date_val, cert_id, domain)
        photo_b64 = rec.get('photo_base64', '')
        
        # Main Font Size Calc
        name_len = len(name)
        if name_len <= 15: main_fontsize = 160
        elif name_len <= 20: main_fontsize = 140
        elif name_len <= 30: main_fontsize = 110
        elif name_len <= 40: main_fontsize = 90
        else: main_fontsize = 70

        id_name_content, id_name_fontsize = get_wrapped_name_svg(name)
        svg_data = svg_template.format(
            name=name, 
            roll_no=roll, 
            photo_base64=photo_b64, 
            qr_base64=qr_b64, 
            cert_id=cert_id,
            signature_base64=sig_b64,
            id_name_content=id_name_content,
            id_name_fontsize=id_name_fontsize,
            main_name_fontsize=main_fontsize,
            date=date_val
        )
        
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        
        # Save PNG to disk
        # Sanitize filename
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
        safe_roll = re.sub(r'[^a-zA-Z0-9_\-]', '_', roll)
        filename = f"{safe_roll}_{safe_name}.png"
        
        # Use a safe path join
        out_path = os.path.join(img_out_dir, filename)
        with open(out_path, 'wb') as f:
            f.write(png_data)
            
    except Exception as e:
        print(f"Error generating for {rec.get('name')}: {e}")
        raise e






    print(app.url_map)
    port = int(os.environ.get("PORT", 5003))

    # Register Cleanup on Exit
    import atexit
    import signal

    def cleanup_temp_files(signum=None, frame=None):
        print("Cleaning up temporary files...")
        temp_dir = os.path.join(app.root_path, 'temp_runs')
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Deleted {temp_dir}")
            except Exception as e:
                print(f"Error cleaning up: {e}")
        if signum is not None:
             sys.exit(0)

    # Register for normal exit and signals
    atexit.register(cleanup_temp_files)
    signal.signal(signal.SIGINT, cleanup_temp_files)
    signal.signal(signal.SIGTERM, cleanup_temp_files)

    app.run(host='0.0.0.0', port=port)

