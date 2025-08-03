from pypdf import PdfReader, PdfWriter

# Input and output file paths
input_pdf_path = "SOA_23AA43507_JUL2025.PDF"
output_pdf_path = "dec_SOA_23AA43507_JUL2025.PDF"
password = "19052001"

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
