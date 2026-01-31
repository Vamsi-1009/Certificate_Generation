import qrcode
import os
import config
import socket

def get_local_ip():
    try:
        # This gets the actual local IP of your machine on the WiFi
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def generate_student_qr(student_data):
    local_ip = get_local_ip()
    # The URL must point to the web_pages folder relative to the server root
    verify_url = f"http://{local_ip}:8000/generated_certificates/web_pages/{student_data['roll_no']}.html"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(config.PATHS["OUTPUT_QR"], f"{student_data['roll_no']}_qr.png")
    img.save(qr_path)
    return qr_path
