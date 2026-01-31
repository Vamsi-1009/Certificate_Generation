import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import config
from utils.qr_utils import generate_student_qr
from utils.web_utils import generate_verification_html

class KIETGenerator:
    def __init__(self):
        # Load high-quality fonts to match your attractive UI
        try:
            # Main Certificate Name (Centered on right)
            self.font_bold = ImageFont.truetype("arialbd.ttf", 120) 
            # Small Name on ID Card Badge
            self.font_id = ImageFont.truetype("arial.ttf", 45)
        except:
            self.font_bold = ImageFont.load_default()
            self.font_id = ImageFont.load_default()

    def generate_single(self, student):
        # 1. Open your provided template as the background
        # This ensures the certificate looks exactly as you designed it
        cert = Image.open(config.PATHS["TEMPLATE"]).convert("RGBA")
        draw = ImageDraw.Draw(cert)

        # 2. Add Main Certificate Name (Centered on the right side)
        # We use anchor="mm" to keep the name perfectly centered
        draw.text(config.POSITIONS["STUDENT_NAME"], student['name'].upper(), 
                  fill=config.COLORS['TEXT_NAVY'], font=self.font_bold, anchor="mm")

        # 3. ID Card Section (Left Sidebar)
        
        # Add Small Name to the bottom of the blue ID badge
        draw.text(config.POSITIONS["ID_NAME"], student['name'], 
                  fill=config.COLORS['WHITE'], font=self.font_id)

        # Add Rectangular Student Photo into the ID card frame
        photo_path = os.path.join(config.PATHS["PHOTOS"], student['photo_filename'])
        if os.path.exists(photo_path):
            # Resized to fit the specific box in your template
            photo = Image.open(photo_path).convert("RGBA").resize((430, 520))
            cert.paste(photo, config.POSITIONS["ID_PHOTO"], photo)

        # Add Verification QR Code onto the ID card
        qr_path = generate_student_qr(student)
        qr_img = Image.open(qr_path).convert("RGBA").resize((220, 220))
        cert.paste(qr_img, config.POSITIONS["ID_QR"], qr_img)

        # 4. Save JPG Output
        final_cert = cert.convert("RGB")
        jpg_path = os.path.join(config.PATHS["OUTPUT_JPG"], f"{student['roll_no']}.jpg")
        final_cert.save(jpg_path, quality=95)

        # 5. Save PDF Output
        pdf_path = os.path.join(config.PATHS["OUTPUT_PDF"], f"{student['roll_no']}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=config.CERT_SIZE)
        c.drawImage(jpg_path, 0, 0, width=config.CERT_SIZE[0], height=config.CERT_SIZE[1])
        c.save()

    def run_batch(self):
        if not os.path.exists(config.PATHS["CSV"]):
            print(f"Error: CSV not found at {config.PATHS['CSV']}")
            return

        df = pd.read_csv(config.PATHS["CSV"])
        print(f"🚀 Processing {len(df)} certificates for {config.AUTHORITY}...")
        
        for _, row in df.iterrows():
            try:
                self.generate_single(row)
                generate_verification_html(row)
                print(f"✅ Generated: {row['roll_no']} - {row['name']}")
            except Exception as e:
                print(f"❌ Failed {row['roll_no']}: {e}")

if __name__ == "__main__":
    gen = KIETGenerator()
    gen.run_batch()
