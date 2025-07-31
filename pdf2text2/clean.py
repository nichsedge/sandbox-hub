import re
import json
from datetime import datetime


def parse_wealth_declaration(filename):
    """
    Parse Indonesian wealth declaration document (LHKPN) from text file
    and convert to structured format
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()

    # Initialize structured data
    structured_data = {
        "document_info": {},
        "personal_data": {},
        "assets": {
            "land_and_buildings": [],
            "transportation_and_machinery": [],
            "other_movable_assets": 0,
            "securities": 0,
            "cash_and_equivalents": 0,
            "other_assets": 0,
        },
        "liabilities": 0,
        "net_worth": 0,
        "summary": {},
    }

    # Parse document header
    header_match = re.search(
        r"LAPORAN HARTA KEKAYAAN PENYELENGGARA NEGARA\s*\(([^)]+)\)", content
    )
    if header_match:
        structured_data["document_info"]["submission_info"] = header_match.group(1)

    # Extract basic info
    bidang_match = re.search(r"BIDANG\s*:\s*(.+)", content)
    if bidang_match:
        structured_data["document_info"]["field"] = bidang_match.group(1).strip()

    lembaga_match = re.search(r"LEMBAGA\s*:\s*(.+)", content)
    if lembaga_match:
        structured_data["document_info"]["institution"] = lembaga_match.group(1).strip()

    unit_match = re.search(r"UNIT KERJA\s*:\s*(.+)", content)
    if unit_match:
        structured_data["document_info"]["work_unit"] = unit_match.group(1).strip()

    # Parse personal data
    nama_match = re.search(r"Nama\s*:\s*(.+)", content)
    if nama_match:
        structured_data["personal_data"]["name"] = nama_match.group(1).strip()

    jabatan_match = re.search(r"Jabatan\s*:\s*(.+)", content)
    if jabatan_match:
        structured_data["personal_data"]["position"] = jabatan_match.group(1).strip()

    nhk_match = re.search(r"NHK\s*:\s*(.+)", content)
    if nhk_match:
        structured_data["personal_data"]["nhk"] = nhk_match.group(1).strip()

    # Parse land and buildings
    land_section = re.search(
        r"A\.\s*TANAH DAN BANGUNAN\s*Rp\.\s*([\d.,]+)(.*?)B\.\s*ALAT TRANSPORTASI",
        content,
        re.DOTALL,
    )
    if land_section:
        total_land = land_section.group(1).replace(".", "").replace(",", "")
        structured_data["assets"]["land_and_buildings_total"] = int(total_land)

        # Parse individual land entries
        land_entries = re.findall(
            r"(\d+)\.\s*Tanah(?:\s+dan\s+Bangunan)?\s+Seluas\s+([\d,]+)\s*m2(?:/(\d+)\s*m2)?\s+di\s+KAB\s*/\s*KOTA\s+(.+?),\s*(.+?)\s+Rp\.\s*([\d.,]+)",
            land_section.group(2),
        )

        for entry in land_entries:
            land_item = {
                "id": int(entry[0]),
                "land_area": int(entry[1].replace(",", "")),
                "building_area": int(entry[2]) if entry[2] else 0,
                "location": entry[3].strip(),
                "acquisition_method": entry[4].strip(),
                "value": int(entry[5].replace(".", "").replace(",", "")),
            }
            structured_data["assets"]["land_and_buildings"].append(land_item)

    # Parse transportation and machinery
    transport_section = re.search(
        r"B\.\s*ALAT TRANSPORTASI DAN MESIN\s*Rp\.\s*([\d.,]+)(.*?)C\.\s*HARTA BERGERAK",
        content,
        re.DOTALL,
    )
    if transport_section:
        total_transport = transport_section.group(1).replace(".", "").replace(",", "")
        structured_data["assets"]["transportation_total"] = int(total_transport)

        # Parse individual transport entries
        transport_entries = re.findall(
            r"(\d+)\.\s*(MOBIL|MOTOR),\s*(.+?)\s+Tahun\s+(\d+),\s*(.+?)\s+Rp\.\s*([\d.,]+)",
            transport_section.group(2),
        )

        structured_data["assets"]["transportation_and_machinery"] = []
        for entry in transport_entries:
            transport_item = {
                "id": int(entry[0]),
                "type": entry[1],
                "description": entry[2].strip(),
                "year": int(entry[3]),
                "acquisition_method": entry[4].strip(),
                "value": int(entry[5].replace(".", "").replace(",", "")),
            }
            structured_data["assets"]["transportation_and_machinery"].append(
                transport_item
            )

    # Parse other asset categories
    other_movable_match = re.search(
        r"C\.\s*HARTA BERGERAK LAINNYA\s*Rp\.\s*([\d.,]+)", content
    )
    if other_movable_match:
        structured_data["assets"]["other_movable_assets"] = int(
            other_movable_match.group(1).replace(".", "").replace(",", "")
        )

    securities_match = re.search(r"D\.\s*SURAT BERHARGA\s*Rp\.\s*([\d.,]+)", content)
    if securities_match:
        structured_data["assets"]["securities"] = int(
            securities_match.group(1).replace(".", "").replace(",", "")
        )

    cash_match = re.search(r"E\.\s*KAS DAN SETARA KAS\s*Rp\.\s*([\d.,]+)", content)
    if cash_match:
        structured_data["assets"]["cash_and_equivalents"] = int(
            cash_match.group(1).replace(".", "").replace(",", "")
        )

    # Parse liabilities
    liabilities_match = re.search(r"III\.\s*HUTANG\s*Rp\.\s*([\d.,]+)", content)
    if liabilities_match:
        structured_data["liabilities"] = int(
            liabilities_match.group(1).replace(".", "").replace(",", "")
        )

    # Parse net worth
    net_worth_match = re.search(
        r"IV\.\s*TOTAL HARTA KEKAYAAN.*?Rp\.\s*([\d.,]+)", content
    )
    if net_worth_match:
        structured_data["net_worth"] = int(
            net_worth_match.group(1).replace(".", "").replace(",", "")
        )

    # Calculate subtotal
    subtotal_match = re.search(r"Sub Total\s*Rp\.\s*([\d.,]+)", content)
    if subtotal_match:
        structured_data["summary"]["subtotal"] = int(
            subtotal_match.group(1).replace(".", "").replace(",", "")
        )

    return structured_data


def format_currency(amount):
    """Format number as Indonesian Rupiah"""
    return f"Rp {amount:,}".replace(",", ".")


def generate_summary_report(data):
    """Generate a human-readable summary report"""
    report = []
    report.append("=" * 60)
    report.append("LAPORAN HARTA KEKAYAAN PENYELENGGARA NEGARA")
    report.append("=" * 60)

    # Personal Information
    report.append(f"\nDATA PRIBADI:")
    report.append(f"Nama: {data['personal_data'].get('name', 'N/A')}")
    report.append(f"Jabatan: {data['personal_data'].get('position', 'N/A')}")
    report.append(f"NHK: {data['personal_data'].get('nhk', 'N/A')}")

    # Asset Summary
    report.append(f"\nRINGKASAN HARTA:")
    land_total = data["assets"].get("land_and_buildings_total", 0)
    transport_total = data["assets"].get("transportation_total", 0)

    report.append(f"Tanah dan Bangunan: {format_currency(land_total)}")
    report.append(f"Alat Transportasi: {format_currency(transport_total)}")
    report.append(
        f"Harta Bergerak Lainnya: {format_currency(data['assets']['other_movable_assets'])}"
    )
    report.append(f"Surat Berharga: {format_currency(data['assets']['securities'])}")
    report.append(
        f"Kas dan Setara Kas: {format_currency(data['assets']['cash_and_equivalents'])}"
    )

    subtotal = data["summary"].get("subtotal", 0)
    report.append(f"\nSub Total: {format_currency(subtotal)}")
    report.append(f"Hutang: {format_currency(data['liabilities'])}")
    report.append(f"TOTAL HARTA KEKAYAAN: {format_currency(data['net_worth'])}")

    # Top properties by value
    if data["assets"]["land_and_buildings"]:
        report.append(f"\nPROPERTI DENGAN NILAI TERTINGGI:")
        sorted_properties = sorted(
            data["assets"]["land_and_buildings"], key=lambda x: x["value"], reverse=True
        )[:5]
        for i, prop in enumerate(sorted_properties, 1):
            report.append(f"{i}. {prop['location']} - {format_currency(prop['value'])}")

    return "\n".join(report)


def main():
    # Parse the document
    filename = "output.txt"
    try:
        structured_data = parse_wealth_declaration(filename)

        # Save structured data as JSON
        with open("structured_wealth_data.json", "w", encoding="utf-8") as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)

        # Generate and save summary report
        summary_report = generate_summary_report(structured_data)
        with open("wealth_summary_report.txt", "w", encoding="utf-8") as f:
            f.write(summary_report)

        print("✅ Parsing completed successfully!")
        print(f"📊 Structured data saved to: structured_wealth_data.json")
        print(f"📋 Summary report saved to: wealth_summary_report.txt")
        print(f"\n📈 Net Worth: {format_currency(structured_data['net_worth'])}")
        print(
            f"🏠 Number of properties: {len(structured_data['assets']['land_and_buildings'])}"
        )
        print(
            f"🚗 Number of vehicles: {len(structured_data['assets']['transportation_and_machinery'])}"
        )

        # Display summary
        print("\n" + "=" * 50)
        print("SUMMARY PREVIEW:")
        print("=" * 50)
        print(summary_report)

    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
        print("Please make sure the file exists in the current directory.")
    except Exception as e:
        print(f"❌ Error parsing document: {str(e)}")


if __name__ == "__main__":
    main()
