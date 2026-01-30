# KIET Certificate Generator

Automated industrial-grade system for generating workshop certificates with integrated ID card visuals and QR verification.

## 🚀 Setup Instructions
1. **Activate Environment**: `source venv/Scripts/activate`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Verify Setup**: `python verify_setup.py`

## 🛠️ Usage
1. Place student photos in `student_data/photos/` (Filename must match CSV entry).
2. Run Template Generator: `python templates/create_main_template.py`
3. Run Generator: `python certificate_generator.py`

## 📁 Output
- **JPG/PDF**: Found in `generated_certificates/images/` and `pdf/`.
- **Verification**: HTML pages in `generated_certificates/web_pages/`.
