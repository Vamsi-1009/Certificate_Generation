import zipfile
import os
import config
from datetime import datetime

def package_for_delivery():
    """Zips all PDFs and HTML pages into a single production-ready archive."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    zip_filename = f"KIET_Certs_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add PDFs
        for root, _, files in os.walk(config.PATHS["OUTPUT_PDF"]):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.join("PDFs", file))
        
        # Add Web Pages
        for root, _, files in os.walk(config.PATHS["OUTPUT_WEB"]):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.join("Verification_Pages", file))
                
    print(f"📦 Production package created: {zip_filename}")

if __name__ == "__main__":
    package_for_delivery()
