import psycopg2
from flask import Flask, render_template, request, send_file
import pandas as pd
import uuid
import qrcode
import base64
import cairosvg
import os
import zipfile
from io import BytesIO

app = Flask(__name__)

# Render uses /tmp for temporary file processing during runtime
BATCH_DEST = '/tmp/batches'
os.makedirs(BATCH_DEST, exist_ok=True)

# This grabs the connection string from your Render Environment Variables
DB_URI = os.environ.get('postgresql://postgres:KIET12schooloftheyear@db.vpzcsgbwyjpvitwudohk.supabase.co:5432/postgres')

# The Landscape SVG Template
SVG_TEMPLATE = """
<svg width="1200" height="850" viewBox="0 0 1200 850" xmlns="http://www.w3.org/2000/svg">
    <rect width="1200" height="850" fill="#f8fbff"/>
    <rect x="30" y="30" width="1140" height="790" rx="18" fill="none" stroke="#4a6cf7" stroke-width="8"/>
    
    <rect x="90" y="200" width="230" height="380" rx="16" fill="#2742c4"/>
    <rect x="150" y="305" width="110" height="135" fill="#ffffff" rx="8"/> 
    <image x="150" y="305" width="110" height="135" href="{photo_base64}"/>
    <text x="205" y="465" text-anchor="middle" font-size="14" fill="#ffffff" font-family="Arial">{name}</text>
    <image x="255" y="515" width="45" height="45" href="{qr_base64}"/>
    <text x="130" y="550" font-size="10" fill="#ffffff" font-family="Arial">Name / Roll No.</text>

    <text x="720" y="140" text-anchor="middle" font-size="44" fill="#2c3e7b" font-family="Georgia">CERTIFICATE OF PARTICIPATION</text>
    <text x="720" y="330" text-anchor="middle" font-size="32" fill="#3b4cca" font-weight="bold" font-family="Georgia">{name}</text>
    <text x="720" y="400" text-anchor="middle" font-size="18" fill="#333" font-family="Arial">has participated in the AI Karyashala Bootcamp</text>
    <text x="720" y="430" text-anchor="middle" font-size="18" fill="#333" font-family="Arial">conducted at KIET College, Kakinada</text>
    
    <text x="720" y="560" text-anchor="middle" font-size="14" fill="#555" font-family="Arial">Cert ID: {cert_id} | Roll: {roll_no}</text>
    <text x="380" y="650" font-size="18" fill="#333" font-family="Arial">Date: {date}</text>
    <text x="780" y="650" font-size="18" fill="#333" font-family="Arial">Coordinator / Trainer: _________</text>
</svg>
"""

def get_qr_base64(cert_id):
    # Dynamically detects your Render URL for the QR code
    domain = request.host_url.rstrip('/')
    url = f"{domain}/verify/{cert_id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    name = request.form.get('name').upper()
    roll = request.form.get('roll_no')
    date = request.form.get('date')
    photo_file = request.files['photo']
    
    cert_id = f"AK-{uuid.uuid4().hex[:8].upper()}"
    qr_b64 = get_qr_base64(cert_id)
    photo_b64 = f"data:image/png;base64,{base64.b64encode(photo_file.read()).decode()}" if photo_file else ""

    svg_data = SVG_TEMPLATE.format(name=name, roll_no=roll, date=date, photo_base64=photo_b64, qr_base64=qr_b64, cert_id=cert_id)
    
    pdf_path = os.path.join(BATCH_DEST, f"{cert_id}.pdf")
    cairosvg.svg2pdf(bytestring=svg_data.encode('utf-8'), write_to=pdf_path)
    return send_file(pdf_path, as_attachment=True)

@app.route('/bulk_generate', methods=['POST'])
def bulk_generate():
    file = request.files['csv_file']
    df = pd.read_csv(file)
    batch_id = uuid.uuid4().hex[:6]
    folder_path = os.path.join(BATCH_DEST, batch_id)
    os.makedirs(folder_path, exist_ok=True)
    
    # FIX: Connect using the DB_URI from Render Environment Variables
    conn = psycopg2.connect(os.environ.get('postgresql://postgres:KIET12schooloftheyear@db.vpzcsgbwyjpvitwudohk.supabase.co:5432/postgres')
    '))
    cur = conn.cursor()

    for _, row in df.iterrows():
        cert_id = f"AK-{uuid.uuid4().hex[:8].upper()}"
        name, roll, date = str(row['name']).upper(), str(row['roll_no']), str(row['date'])

        cur.execute("INSERT INTO certificates (cert_id, name, roll_no, issue_date) VALUES (%s, %s, %s, %s)",
                    (cert_id, name, roll, date))

        qr_b64 = get_qr_base64(cert_id)
        svg_data = SVG_TEMPLATE.format(name=name, roll_no=roll, date=date, photo_base64="", qr_base64=qr_b64, cert_id=cert_id)
        
        cairosvg.svg2pdf(bytestring=svg_data.encode('utf-8'), write_to=os.path.join(folder_path, f"{roll}.pdf"))

    conn.commit()
    cur.close()
    conn.close()

    zip_path = f"{folder_path}.zip"
    with zipfile.ZipFile(zip_path, 'w') as z:
        for f in os.listdir(folder_path):
            z.write(os.path.join(folder_path, f), f)

    return send_file(zip_path, as_attachment=True)

@app.route('/verify/<cert_id>')
def verify(cert_id):
    # FIX: Connect using the DB_URI
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute("SELECT name, roll_no, issue_date FROM certificates WHERE cert_id=%s", (cert_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    if res: return render_template('verify.html', name=res[0], roll=res[1], date=res[2])
    return "Verification Link Expired or Invalid", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
