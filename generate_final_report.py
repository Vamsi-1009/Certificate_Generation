import os
import pandas as pd
import config

def run_report():
    df = pd.read_csv(config.PATHS["CSV"])
    total_students = len(df)
    
    generated_pdfs = len(os.listdir(config.PATHS["OUTPUT_PDF"]))
    generated_imgs = len(os.listdir(config.PATHS["OUTPUT_JPG"]))
    
    print("="*40)
    print("🎓 KIET CERTIFICATE GENERATION REPORT")
    print("="*40)
    print(f"Total Students in CSV: {total_students}")
    print(f"PDFs Generated:        {generated_pdfs}")
    print(f"Images Generated:     {generated_imgs}")
    print("-"*40)
    
    if total_students == generated_pdfs:
        print("✅ SUCCESS: All certificates produced perfectly.")
    else:
        print("⚠️ WARNING: Mismatch detected. Check logs.")
    print("="*40)

if __name__ == "__main__":
    run_report()
