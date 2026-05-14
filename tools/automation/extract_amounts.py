# /// script
# dependencies = ["pdfplumber"]
# ///

import pdfplumber
import re
import os
import json
import glob

def extract_amount_transfer(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            # Check for "Amount Transfer" or "Net Pay"
            # Some formats use "Amount Transfer", others use "Net Pay"
            match = re.search(r"(?:Amount Transfer|Net Pay)\s+([\d,.]+)", text)
            if match:
                return match.group(1).strip()
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    return None

def main():
    directory = "scratch"
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    
    results = []
    for pdf_file in sorted(pdf_files):
        print(f"Processing {pdf_file}...")
        amount = extract_amount_transfer(pdf_file)
        
        # Extract date from filename (YYYYMMDD or YYYY-MM-DD)
        filename = os.path.basename(pdf_file)
        # Try YYYY-MM-DD first
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
        if date_match:
            date_str = date_match.group(1)
        else:
            # Try 8-digit date, likely starting with '20' for recent years
            date_match = re.search(r"(20\d{6})", filename)
            if date_match:
                # Convert YYYYMMDD to YYYY-MM-DD
                d = date_match.group(1)
                date_str = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            else:
                date_str = "unknown"
        
        if amount:
            # Clean amount: remove commas and convert to int
            clean_amount = int(amount.replace(",", ""))
            results.append({
                "filename": filename,
                "date": date_str,
                "amount_transfer": clean_amount
            })
        else:
            print(f"Could not find Amount Transfer in {pdf_file}")

    # Sort results by date
    results.sort(key=lambda x: x["date"])

    output_file = os.path.join(directory, "amounts.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"\nExtraction complete. Results saved to {output_file}")
    print(json.dumps(results, indent=4))

if __name__ == "__main__":
    main()
