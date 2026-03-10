import pdfplumber
import pandas as pd

# Define the file path
pdf_path = "95f8c4c8bc_848269e900.pdf"
output_csv = "extracted_tables.csv"

all_data = []

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        # Extract tables from the current page
        tables = page.extract_tables()

        for table in tables:
            # Convert the list of lists into a DataFrame
            df = pd.DataFrame(table)

            # Clean up the data: remove None values or empty strings
            df = df.fillna("")

            # Append to our list of all data found
            all_data.append(df)
            print(f"Extracted table from page {i}")

# Combine all extracted tables into one CSV
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv(output_csv, index=False, header=False)
    print(f"Successfully saved all tables to {output_csv}")
else:
    print("No tables were found in the document.")
