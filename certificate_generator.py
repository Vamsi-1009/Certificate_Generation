import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import config
from utils.qr_utils import generate_student_qr
from utils.image_utils import prepare_student_photo, add_lanyard_effect
from utils.web_utils import generate_verification_html

class KIETGenerator:
    def __init__(self):
        # Load fonts - Defaulting to Arial/system fonts
        try:
            self.font_bold = ImageFont.truetype("arialbd.ttf", 100)
            self.font_reg = ImageFont.truetype("arial.ttf", 50)
        except:
            self.font_bold = ImageFont.load_default()
            self.font_reg = ImageFont.load_default()

    def generate_single(self, student):
        # 1. Load Template
        cert = Image.open(config.PATHS["TEMPLATE"]).convert("RGBA")
        
        # 2. Add Lanyard Effect
        cert = add_lanyard_effect(cert, config.POS_ID_CARD)
        
        draw = ImageDraw.Draw(cert)

        # 3. Add Text (Right Side)
        draw.text(config.POSITIONS["NAME"], student['name'].upper(), fill=config.COLORS['KIET_BLUE'], font=self.font_bold)
        draw.text(config.POSITIONS["TOPIC"], config.WORKSHOP_TOPIC, fill=config.COLORS['TEXT_BLACK'], font=self.font_reg)

        # 4. Add Student Photo (Left Side)
        photo_path = os.path.join(config.PATHS["PHOTOS"], student['photo_filename'])
        photo = prepare_student_photo(photo_path)
        cert.paste(photo, config.POSITIONS["PHOTO"], photo)

        # 5. Add QR Code
        qr_path = generate_student_qr(student)
        qr_img = Image.open(qr_path).convert("RGBA").resize((350, 350))
        cert.paste(qr_img, config.POSITIONS["QR"], qr_img)

        # 6. Save JPG
        final_cert = cert.convert("RGB")
        jpg_path = os.path.join(config.PATHS["OUTPUT_JPG"], f"{student['roll_no']}.jpg")
        final_cert.save(jpg_path, quality=95)

        # 7. Generate PDF
        pdf_path = os.path.join(config.PATHS["OUTPUT_PDF"], f"{student['roll_no']}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=config.CERT_SIZE)
        c.drawImage(jpg_path, 0, 0, width=config.CERT_SIZE[0], height=config.CERT_SIZE[1])
        c.save()

    def run_batch(self):
        df = pd.read_csv(config.PATHS["CSV"])
        print(f"Processing {len(df)} certificates...")
        for _, row in df.iterrows():
            self.generate_single(row)
            generate_verification_html(row)
            print(f"Done: {row['roll_no']}")

if __name__ == "__main__":
    gen = KIETGenerator()
    gen.run_batch()
