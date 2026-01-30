import qrcode
import os
import config

def generate_student_qr(student_data):
    # Data to encode: Roll No, Name, and a verification placeholder
    qr_payload = (
        f"CertID: {student_data['roll_no']}\n"
        f"Student: {student_data['name']}\n"
        f"Workshop: {config.WORKSHOP_TOPIC}\n"
        f"Verified: http://kiet.edu/verify/{student_data['roll_no']}"
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(config.PATHS["OUTPUT_QR"], f"{student_data['roll_no']}_qr.png")
    img.save(qr_path)
    return qr_path
