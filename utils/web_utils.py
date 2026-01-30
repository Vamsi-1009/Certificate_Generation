import os
import config

def generate_verification_html(student_data):
    """Generates a professional verification landing page for each student."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Certificate Verification - {student_data['roll_no']}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border-top: 10px solid #0056B3; }}
            .status {{ color: #28a745; font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
            .details {{ text-align: left; margin-top: 20px; line-height: 1.6; color: #333; }}
            .kiet-logo {{ color: #0056B3; font-weight: bold; font-size: 28px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="kiet-logo">KIET, Kakinada</div>
            <div class="status">✅ VERIFIED CERTIFICATE</div>
            <hr>
            <div class="details">
                <p><strong>Student Name:</strong> {student_data['name']}</p>
                <p><strong>Roll Number:</strong> {student_data['roll_no']}</p>
                <p><strong>Workshop:</strong> {config.WORKSHOP_TOPIC}</p>
                <p><strong>Issue Date:</strong> {config.ISSUE_DATE}</p>
                <p><strong>Issuing Authority:</strong> {config.AUTHORITY}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    file_path = os.path.join(config.PATHS["OUTPUT_WEB"], f"{student_data['roll_no']}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return file_path
