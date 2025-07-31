import fitz  # PyMuPDF


def pdf_to_text_pymupdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


# Extract text
pdf_text = pdf_to_text_pymupdf(
    "/home/al/projects/creds/pdf2text/2022_Fadli_Zon_LHKPN.pdf"
)

# Save as .txt
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(pdf_text)

# Save as .md
with open("output.md", "w", encoding="utf-8") as f:
    f.write(pdf_text)
