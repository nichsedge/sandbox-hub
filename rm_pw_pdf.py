from pypdf import PdfReader, PdfWriter

import os
from dotenv import load_dotenv

load_dotenv()

# Input and output file paths
input_pdf_path = os.getenv("INPUT_PDF_PATH")
output_pdf_path = os.getenv("OUTPUT_PDF_PATH")
password = os.getenv("PASSWORD")

# Open the encrypted PDF
reader = PdfReader(input_pdf_path)

# Decrypt the PDF
if reader.is_encrypted:
    reader.decrypt(password)

# Create a new PDF writer
writer = PdfWriter()

# Add all pages to the writer
for page in reader.pages:
    writer.add_page(page)

# Write to a new file without password
with open(output_pdf_path, "wb") as f:
    writer.write(f)

print("Password removed successfully.")
