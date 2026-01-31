# KIET Certificate & ID Card Generator

An automated system for generating professional workshop certificates featuring an integrated ID card sidebar and QR verification.

## 🛠️ Tech Stack
* **Backend**: Python (Pillow, Pandas, ReportLab)
* **Verification**: QR Codes + Local HTML Server
* **Frontend**: Bootstrap 5 Dashboard

## 🚀 Quick Start
1. Place student photos in `student_data/photos/`
2. Update student data in `student_data/students.csv`
3. Run: `./run_project.sh`
4. View Results: Open `dashboard.html` in any browser.

## 🔍 Verification
To test QR codes, run `python -m http.server 8000` and scan the QR on the certificate using a phone on the same Wi-Fi.
