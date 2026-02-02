from flask import Flask, render_template, request
import pandas as pd
import uuid
import qrcode
import base64
import cairosvg
import os
from io import BytesIO

app = Flask(__name__)

# Your Professional SVG Template
SVG_TEMPLATE = """
<svg width="1200" height="850" viewBox="0 0 1200 850" xmlns="http://www.w3.org/2000/svg">
    <rect width="1200" height="850" fill="#ffffff"/>
    <rect x="20" y="20" width="1160" height="810" fill="none" stroke="#2c3e7b" stroke-width="12"/>
    <rect x="40" y="40" width="1120" height="770" fill="none" stroke="#d4af37" stroke-width="4"/>
    <rect x="0" y="0" width="300" height="850" fill="#2c3e7b"/>
    <circle cx="150" cy="150" r="80" fill="#ffffff" opacity="0.1"/>
    <rect x="75" y="250" width="150" height="180" rx="10" fill="#ffffff"/>
    <image x="80" y="255" width="140" height="170" href="{photo_base64}" preserveAspectRatio="xMidYMid slice"/>
    <text x="150" y="470" text-anchor="middle" font-size="18" fill="#ffffff" font-family="Arial" font-weight="bold">{name}</text>
    <text x="150" y="495" text-anchor="middle" font-size="14" fill="#cbd5e1" font-family="Arial">{roll_no}</text>
    <text x="750" y="150" text-anchor="middle" font-size="50" fill="#2c3e7b" font-family="Georgia" font-weight="bold">CERTIFICATE</text>
    <text x="750" y="210" text-anchor="middle" font-size="20" fill="#d4af37" font-family="Arial" letter-spacing="5">OF PARTICIPATION</text>
    <text x="750" y="320" text-anchor="middle" font-size="24" fill="#64748b" font-family="Arial">This is to certify that</text>
    <text x="750" y="380" text-anchor="middle" font-size="42" fill="#2c3e7b" font-family="Georgia" font-weight="bold">{name}</text>
    <text x="750" y="460" text-anchor="middle" font-size="20" fill="#334155" font-family="Arial">has successfully completed the</text>
    <text x="750" y="500" text-anchor="middle" font-size="26" fill="#2c3e7b" font-family="Arial" font-weight="bold">AI Karyashala Bootcamp</text>
    <text x="750" y="540" text-anchor="middle" font-size="18" fill="#64748b" font-family="Arial">Organized by KIET College, Kakinada</text>
    <line x1="450" y1="680" x2="650" y2="680" stroke="#334155" stroke-width="1"/>
    <text x="550" y="710" text-anchor="middle" font-size="16" fill="#334155" font-family="Arial">Date: {date}</text>
    <line x1="850" y1="680" x2="1050" y2="680" stroke="#334155" stroke-width="1"/>
    <text x="950" y="710" text-anchor="middle" font-size="16" fill="#334155" font-family="Arial">Authorized Signatory</text>
    <rect x="110" y="650" width="80" height="80" fill="white" rx="5"/>
    <image x="115" y="655" width="70" height="70" href="{qr_base64}"/>
    <text x="150" y="750" text-anchor="middle" font-size="10" fill="#cbd5e1" font-family="Arial">ID: {cert_id}</text>
</svg>
"""

def get_qr_base64(cert_id, name):
    info = f"Verified: {name}\nID: {cert_id}"
    qr = qrcode.make(info)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    name = request.form.get('name', '').upper()
    roll = request.form.get('roll_no', '')
    date = request.form.get('date', '')
    photo_file = request.files.get('photo')
    
    cert_id = f"AK-{uuid.uuid4().hex[:8].upper()}"
    qr_b64 = get_qr_base64(cert_id, name)
    photo_b64 = f"data:image/png;base64,{base64.b64encode(photo_file.read()).decode()}" if photo_file else ""

    svg_data = SVG_TEMPLATE.format(name=name, roll_no=roll, date=date, photo_base64=photo_b64, qr_base64=qr_b64, cert_id=cert_id)
    png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
    b64_img = base64.b64encode(png_data).decode()
    
    certs = [{'name': name, 'roll': roll, 'image': f"data:image/png;base64,{b64_img}"}]
    return render_template('results.html', certificates=certs)

@app.route('/bulk_generate', methods=['POST'])
def bulk_generate():
    file = request.files.get('csv_file')
    if not file: return "No file", 400
    df = pd.read_csv(file)
    certificates = []
    for _, row in df.iterrows():
        cert_id = f"AK-{uuid.uuid4().hex[:8].upper()}"
        name, roll, date = str(row['name']).upper(), str(row['roll_no']), str(row['date'])
        qr_b64 = get_qr_base64(cert_id, name)
        svg_data = SVG_TEMPLATE.format(name=name, roll_no=roll, date=date, photo_base64="", qr_base64=qr_b64, cert_id=cert_id)
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        certificates.append({
            'name': name, 'roll': roll, 
            'image': f"data:image/png;base64,{base64.b64encode(png_data).decode()}"
        })
    return render_template('results.html', certificates=certificates)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
