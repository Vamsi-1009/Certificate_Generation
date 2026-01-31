import os
import config

def generate_dashboard():
    """Generates a professional frontend dashboard to view all certificates."""
    image_folder = config.PATHS["OUTPUT_JPG"]
    web_folder = config.PATHS["OUTPUT_WEB"]
    
    # Get relative paths for the HTML file to work locally
    # Note: This assumes the dashboard is saved in the project root
    images = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KIET Certificate Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }}
            .navbar {{ background-color: {config.COLORS['KIET_BLUE'] if isinstance(config.COLORS['KIET_BLUE'], str) else '#0056b3'}; color: white; }}
            .cert-card {{ transition: transform 0.3s; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 12px; overflow: hidden; }}
            .cert-card:hover {{ transform: translateY(-10px); }}
            .btn-view {{ background-color: {config.COLORS['GOLD'] if isinstance(config.COLORS['GOLD'], str) else '#daa520'}; color: white; border: none; }}
            .btn-view:hover {{ background-color: #b8860b; color: white; }}
            .hero-section {{ background: linear-gradient(rgba(0,86,179,0.8), rgba(0,86,179,0.8)), url('https://www.kiet.edu/images/logo.png'); background-size: cover; color: white; padding: 60px 0; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="hero-section">
            <h1 class="display-4 fw-bold">KIET Certificate Gallery</h1>
            <p class="lead">View and verify all generated workshop certificates</p>
        </div>

        <div class="container my-5">
            <div class="row g-4">
    """

    for img in images:
        student_id = img.replace('.jpg', '')
        img_path = os.path.join("generated_certificates/images", img)
        verify_path = os.path.join("generated_certificates/web_pages", f"{student_id}.html")
        
        html_content += f"""
                <div class="col-md-4">
                    <div class="card cert-card h-100">
                        <img src="{img_path}" class="card-img-top" alt="Certificate">
                        <div class="card-body text-center">
                            <h5 class="card-title">Roll No: {student_id}</h5>
                            <div class="d-grid gap-2">
                                <a href="{img_path}" target="_blank" class="btn btn-outline-primary btn-sm">View Full Image</a>
                                <a href="{verify_path}" target="_blank" class="btn btn-view btn-sm">Verify Details</a>
                            </div>
                        </div>
                    </div>
                </div>
        """

    html_content += """
            </div>
        </div>
        <footer class="text-center py-4 text-muted">
            &copy; 2026 KIET Kakinada - Certificate Generation System
        </footer>
    </body>
    </html>
    """

    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✨ Frontend Dashboard generated: dashboard.html")

if __name__ == "__main__":
    generate_dashboard()
