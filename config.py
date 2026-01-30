import os

# Base Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path Configuration
PATHS = {
    "TEMPLATE": os.path.join(BASE_DIR, "templates", "certificate_template.jpg"),
    "CSV": os.path.join(BASE_DIR, "student_data", "students.csv"),
    "PHOTOS": os.path.join(BASE_DIR, "student_data", "photos"),
    "OUTPUT_JPG": os.path.join(BASE_DIR, "generated_certificates", "images"),
    "OUTPUT_PDF": os.path.join(BASE_DIR, "generated_certificates", "pdf"),
    "OUTPUT_QR": os.path.join(BASE_DIR, "generated_certificates", "qr_codes"),
    "OUTPUT_WEB": os.path.join(BASE_DIR, "generated_certificates", "web_pages"),
    "LOG_FILE": os.path.join(BASE_DIR, "logs", "generator.log")
}

# Certificate Settings
CERT_SIZE = (3508, 2480) 
WORKSHOP_TOPIC = "Advanced Python & AI Workshop"
ISSUE_DATE = "December 2024"
AUTHORITY = "KIET Administration"

# Visuals
COLORS = {
    "KIET_BLUE": (0, 86, 179),
    "GOLD": (218, 165, 32),
    "TEXT_BLACK": (30, 30, 30),
    "WHITE": (255, 255, 255)
}

# Layout Positions (x, y)
POSITIONS = {
    "NAME": (1800, 900),
    "TOPIC": (1800, 1150),
    "PHOTO": (450, 700),
    "QR": (500, 1250),
    "ROLL_NO": (550, 1150)
}

# Added missing POS_ID_CARD coordinate for the lanyard effect
POS_ID_CARD = (200, 450)
