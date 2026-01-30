import os
import pandas as pd
from config import PATHS

def run_setup():
    print("--- KIET System Verification ---")
    
    # 1. Ensure all directories exist
    for key, path in PATHS.items():
        # If it's a file path, get the directory; otherwise use the path as is
        folder = os.path.dirname(path) if "." in os.path.basename(path) else path
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            print(f"Verified/Created: {folder}")

    # 2. Create Sample CSV for testing
    if not os.path.exists(PATHS["CSV"]):
        data = {
            "roll_no": ["KIET2024001", "KIET2024002"],
            "name": ["Rahul Sharma", "Priya Patel"],
            "branch": ["CSE", "ECE"],
            "year": ["3rd", "2nd"],
            "email": ["rahul@kiet.edu", "priya@kiet.edu"],
            "photo_filename": ["rahul.jpg", "priya.jpg"]
        }
        pd.DataFrame(data).to_csv(PATHS["CSV"], index=False)
        print("✅ Sample CSV created in student_data/students.csv")

if __name__ == "__main__":
    run_setup()
