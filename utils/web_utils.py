import os
import config

def generate_verification_html(student_data):
    """Generates a professional verification page displaying the certificate."""
    # Paths relative to the server root (Certificate_Generation folder)
    img_src = f"/generated_certificates/images/{student_data['roll_no']}.jpg"
    pdf_href = f"/generated_certificates/pdf/{student_data['roll_no']}.pdf"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Certificate - {student_data['name']}</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; }}
            .container {{ background: white; max-width: 800px; width: 100%; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; }}
            .header {{ color: #0056B3; margin-bottom: 20px; }}
            .certificate-preview {{ width: 100%; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); }}
            .btn-download {{ display: inline-block; padding: 12px 25px; background-color: #DAA520; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; transition: 0.3s; }}
            .btn-download:hover {{ background-color: #B8860B; }}
            .details {{ text-align: left; background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">KIET Certificate Verification</h1>
            <div class="details">
                <p><strong>Student:</strong> {student_data['name']}</p>
                <p><strong>Roll No:</strong> {student_data['roll_no']}</p>
                <p><strong>Status:</strong> ✅ Authenticated</p>
            </div>
            
            <h3>Certificate Preview</h3>
            <img src="{{img_src}}" class="certificate-preview" alt="Certificate Image">
            
            <br>
            <a href="{{pdf_href}}" class="btn-download" download>Download Official PDF</a>
        </div>
    </body>
    </html>
    """
    
    file_path = os.path.join(config.PATHS["OUTPUT_WEB"], f"{student_data['roll_no']}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return file_path
