import os
import json
import argparse
import base64
import cairosvg
import qrcode
from io import BytesIO
from PIL import Image
import concurrent.futures
import time
import re

# Logic duplicated from app.py to ensure standalone execution without Flask context issues on Windows

def load_text_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def get_wrapped_name_svg(name):
    """Wrap name for ID card into SVG tspans with dynamic font size."""
    # Clean non-ascii (English only request)
    name = re.sub(r'[^\x00-\x7F]+', '', name).strip()
    
    words = name.split()
    if not words: return "", 50
    full_name_len = len(name)
    
    # IMPROVED: Prefer single line if possible up to 20 chars
    if full_name_len <= 20:
        fontsize = 45 if full_name_len <= 15 else 35
        return f'<tspan x="300" dy="1.2em">{name}</tspan>', fontsize

    # Case 2: Medium name (2 lines) - split evenly-ish
    if full_name_len <= 35: # Increased from 30
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
            return f'<tspan x="300" dy="1.2em">{name}</tspan>', 30
    
    # Long name fallback
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
    
    if len(lines) <= 1:
         return f'<tspan x="300" dy="1.2em">{lines[0]}</tspan>', 35
    elif len(lines) == 2:
         return f'<tspan x="300" dy="0">{lines[0]}</tspan><tspan x="300" dy="1.2em">{lines[1]}</tspan>', 35
    else:
         svg_lines = []
         svg_lines.append(f'<tspan x="300" dy="-0.5em">{lines[0]}</tspan>')
         for l in lines[1:3]:
             svg_lines.append(f'<tspan x="300" dy="1.1em">{l}</tspan>')
         return "".join(svg_lines), 30

def get_qr_base64(name, roll, date, cert_id, domain_url):
    """Generate QR code base64 with validation URL."""
    # Validation URL
    validation_url = f"{domain_url}/validate/{cert_id}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(validation_url)
    qr.make(fit=True)

    img_buffer = BytesIO()
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img.save(img_buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"

def generate_single_certificate(rec, svg_template, sig_b64, img_out_dir, domain):
    try:
        raw_name = str(rec.get('name', 'Unknown'))
        # ENFORCE ENGLISH ONLY (Remove non-ascii)
        name = re.sub(r'[^\x00-\x7F]+', '', raw_name).strip().upper()
        if not name: name = "UNKNOWN"
        
        roll = str(rec.get('roll', 'N/A')).upper()
        date_val = str(rec.get('date', '08-02-2026')) 
        
        # Calculate Main Name Font Size
        name_len = len(name)
        if name_len <= 15: main_fontsize = 160
        elif name_len <= 20: main_fontsize = 140
        elif name_len <= 30: main_fontsize = 110
        elif name_len <= 40: main_fontsize = 90
        else: main_fontsize = 70
        
        cert_id = f"AIK{roll}"
        qr_b64 = get_qr_base64(name, roll, date_val, cert_id, domain)
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
            id_name_fontsize=id_name_fontsize,
            main_name_fontsize=main_fontsize,
            date=date_val
        )
        
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
        safe_roll = re.sub(r'[^a-zA-Z0-9_\-]', '_', roll)
        filename = f"{safe_roll}_{safe_name}.png"
        
        out_path = os.path.join(img_out_dir, filename)
        with open(out_path, 'wb') as f:
            f.write(png_data)
        return True
    except Exception as e:
        print(f"Error generating for {rec.get('name')}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Batch Certificate Generator')
    parser.add_argument('--run_dir', required=True, help='Path to run directory')
    parser.add_argument('--domain', required=True, help='Domain for QR code')
    parser.add_argument('--template', required=True, help='Path to SVG template')
    parser.add_argument('--signature', required=True, help='Path to Signature PNG')
    
    args = parser.parse_args()
    
    records_path = os.path.join(args.run_dir, 'records.json')
    img_out_dir = os.path.join(args.run_dir, 'certificates')
    os.makedirs(img_out_dir, exist_ok=True)
    
    with open(records_path, 'r') as f:
        records = json.load(f)
        
    with open(args.template, 'r', encoding='utf-8') as f:
        svg_template = f.read()
        
    with open(args.signature, "rb") as f:
        sig_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        
    print(f"Starting batch generation for {len(records)} records...")
    
    # Process Pool for GDI safety/speed
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for rec in records:
            futures.append(executor.submit(
                generate_single_certificate,
                rec,
                svg_template,
                sig_b64,
                img_out_dir,
                args.domain
            ))
            
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                completed += 1
            if completed % 10 == 0:
                print(f"Generated {completed}/{len(records)}")

if __name__ == "__main__":
    main()
