import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PATHS = {
    # This must point to your high-quality AI Karyashala JPG/PNG
    "TEMPLATE": os.path.join(BASE_DIR, "templates", "certificate_template.jpg"),
    "CSV": os.path.join(BASE_DIR, "student_data", "students.csv"),
    "PHOTOS": os.path.join(BASE_DIR, "student_data", "photos"),
    "OUTPUT_JPG": os.path.join(BASE_DIR, "generated_certificates", "images"),
    "OUTPUT_PDF": os.path.join(BASE_DIR, "generated_certificates", "pdf"),
    "OUTPUT_QR": os.path.join(BASE_DIR, "generated_certificates", "qr_codes"),
    "OUTPUT_WEB": os.path.join(BASE_DIR, "generated_certificates", "web_pages")
}

CERT_SIZE = (3508, 2480) 

# These coordinates are calibrated for your specific "Anjali Reddy" template
POSITIONS = {
    "STUDENT_NAME": (2150, 1080),    # Large name in the center
    "ID_NAME": (265, 2180),          # Small name on the blue ID card
    "ID_PHOTO": (220, 1720),         # Photo inside the ID card frame
    "ID_QR": (800, 2250),            # QR code on the ID card
}

# Fixes the AttributeError: 'POS_ID_CARD'
POS_ID_CARD = (100, 450) 

COLORS = {
    "TEXT_NAVY": (26, 54, 104),
    "WHITE": (255, 255, 255)
}
