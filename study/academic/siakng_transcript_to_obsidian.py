# !pip install tabulate

import pandas as pd
import re

# Paste your full raw data into this variable (ensure you keep the triple quotes)
raw_text = """No.	Course Code	Curriculum	Course Name	Class	SKS	IRS Status	Final Grade	Letter Grade	Detail
Academic Year 2019/2020 Term 1
1.	CSGE601020	01.00.12.01-2016	Programming Foundations 1	DDP1-F	4	Approved	92.50	A	detail
2.	UIST601111	01.00.12.01-2016	Physics	FisDas-G (angk 2019)	3	Approved	80.39	A-	detail
3.	UIST601014	06.00.12.01-2016	Basic Mathematics 1	Matdas 1 - B	3	Approved	87.66	A	detail
4.	CSGE601010	01.00.12.01-2016	Discrete Mathematics 1	MD 1 - A	3	Approved	Empty	A-	detail
5.	UIGE600002	06.00.12.01-2016	Integrated Personality Dev. Skills B	MPKT B Kelas C	6	Approved	80.10	A-	detail
Academic Year 2019/2020 Term 2
6.	CSGE601021	01.00.12.01-2018	Programming Foundations 2	DDP 2 - G	4	Approved	83.04	A-	detail
7.	CSGE601011	01.00.12.01-2018	Discrete Mathematics 2	MD 2 - F	3	Approved	83.68	A-	detail
8.	UIGE600003	06.00.12.01-2016	English	MPK Bahasa Inggris-C	3	Approved	Empty	A-	detail
9.	UIGE600020	12.00.07.01-2018	Art Appreciation of Film	E	1	Approved	85.20	A	detail
10.	UIGE600001	08.00.12.01-2016	Integrated Personality Dev. Skills A	MPKT-A (Kelas K)	6	Approved	82.90	A-	detail
11.	CSIM601280	06.00.12.01-2016	Principles of Information Systems	PPSI-B	3	Approved	76.78	B+	detail
12.	CSGE602013	06.00.12.01-2016	Statistics & Probability	Statprob-C	3	Approved	59.12	C+	detail
Academic Year 2020/2021 Term 1
13.	CSIM602160	06.00.12.01-2018	Business Administration	AdBis-B	3	Approved	82.21	A-	detail
14.	CSIM601251	06.00.12.01-2018	Introduction to Computer Architecture	DDAK-C	4	Approved	87.17	A	detail
15.	UIGE600010	06.00.12.01-2018	Islamic Religious Instruction	Agama Islam-B (2019)	2	Approved	83.75	A-	detail
16.	CSGE602022	01.00.12.01-2018	Web Design & Programming	PPW-C	3	Approved	87.47	A	detail
17.	CSIM602161	06.00.12.01-2018	Principles of Management	PPM-B	3	Approved	Empty	A-	detail
18.	CSGE602040	06.00.12.01-2018	Data Structures and Algorithms	SDA-C	4	Approved	85.99	A	detail
Academic Year 2020/2021 Term 2
19.	CSGE602012	06.00.12.01-2020	Linear Algebra	Aljabar Linier C	3	Approved	82.97	A-	detail
20.	CSGE602070	06.00.12.01-2020	Database	Basis Data C	4	Approved	75.53	B+	detail
21.	CSGE603291	06.00.12.01-2018	Research Methodology & Scientific Writing	MPPI E	3	Approved	80.64	A-	detail
22.	CSIM602263	06.00.12.01-2020	Accounting & Enterprise Information System	SIPA C	4	Approved	83.19	A-	detail
23.	CSGE602024	06.00.12.01-2020	Human Computer Interaction	Sistem Interaksi E	3	Approved	85.76	A	detail
24.	CSIM602155	06.00.12.01-2020	Operating System for Information System	SOSI B	3	Approved	82.79	A-	detail
Academic Year 2021/2022 Term 1
25.	CSIM603183	06.00.12.01-2020	IS Analysis and Design	Anaperancis-B	3	Approved	78.42	B+	detail
26.	CSIM603026	06.00.12.01-2020	Enterprise Application Programming	APAP-A	3	Approved	94.27	A	detail
27.	CSIM603154	06.00.12.01-2020	Data Communication Networks	Jarkomdat-C	3	Approved	90.46	A	detail
28.	CSGE603130	01.00.12.01-2020	Introduction to AI & Data Science	KASDD C	4	Approved	79.83	A-	detail
29.	CSIM601191	06.00.12.01-2020	Business and Technical Communication	Kombistek D	3	Approved	83.02	A-	detail
30.	CSIM602281	06.00.12.01-2020	Information Technology Project Management	ManPro TI-C	3	Approved	83.02	A-	detail
31.	CSIM603116	06.00.12.01-2020	Applied Statistics	Statistika Terapan A	3	Approved	93.09	A	detail
Academic Year 2021/2022 Term 2
32.	CSIE604284	06.00.12.01-2020	Social Media Analytics	Anmedsos	3	Approved	Empty	A	detail
33.	CSIE604275	06.00.12.01-2020	Enterprise Application Integration	EAI	3	Approved	86.73	A	detail
34.	CSIE604276	06.00.12.01-2020	IT Infrastructure Management	MITI	3	Approved	88.39	A	detail
35.	CSIE604378	06.00.12.01-2020	IT Service Management	MLTI A	3	Approved	84.41	A-	detail
36.	CSIM603182	06.00.12.01-2020	Information System Management	MSI A	3	Approved	88.74	A	detail
37.	CSIE604271	06.00.12.01-2020	Data Mining & Business Intelligence	PDIB	3	Approved	82.16	A-	detail
38.	CSIM603229	06.00.12.01-2020	Information Systems Development Project	Propensi A	6	Approved	87.59	A	detail
Academic Year 2022/2023 Term 1
39.	CSGE604099	06.00.12.01-2020	Final Project	Tugas Akhir	6	Approved	Empty	A	detail
Academic Year 2022/2023 Term 2
40.	CSCE604098	01.00.12.01-2020	Internships	KP & MBKM B	4	Approved	Empty	A	detail
41.	CSGE614093	01.00.12.01-2020	Computer & Society	Komas A	3	Approved	81.20	A-	detail
"""

# Extract each academic year block
academic_years = re.split(r"Academic Year .*? Term \d+", raw_text)[1:]
terms = re.findall(r"Academic Year .*? Term \d+", raw_text)

# Prepare to collect structured data
data = []

# Split and parse each line in the year-term blocks
for term, block in zip(terms, academic_years):
    term = term.strip()
    lines = block.strip().split("\n")
    for line in lines:
        parts = line.split("\t")
        if len(parts) == 10:
            (
                number,
                course_code,
                curriculum,
                course_name,
                class_name,
                sks,
                irs_status,
                final_grade,
                letter_grade,
                _,
            ) = parts
            data.append(
                {
                    "Term": term,
                    "No": number.strip("."),
                    "Course Code": course_code,
                    "Curriculum": curriculum,
                    "Course Name": course_name,
                    "Class": class_name,
                    "SKS": int(sks),
                    "IRS Status": irs_status,
                    "Final Grade": final_grade if final_grade != "Empty" else None,
                    "Letter Grade": letter_grade,
                }
            )

# Create a DataFrame
df = pd.DataFrame(data)

# Save to CSV or Markdown (for Obsidian)
df.to_csv("structured_transcript.csv", index=False)
df.to_markdown("structured_transcript.md", index=False)

df.columns

import os
import pandas as pd
from datetime import datetime
import re

# Load CSV
df = pd.read_csv("structured_transcript.csv")


# Helper function to convert term to date
def term_to_date(term_str):
    match = re.search(r"Academic Year (\d{4})/(\d{4}) Term (\d)", term_str)
    if match:
        start_year, end_year, term = match.groups()
        year = int(start_year) if term == "1" else int(end_year)
        month = 8 if term == "1" else 2
        return datetime(year, month, 1).strftime("%Y-%m-%d")
    return "2000-01-01"


# Output directory
output_dir = "obsidian_courses"
os.makedirs(output_dir, exist_ok=True)

# Generate markdown files
for _, row in df.iterrows():
    course_name = row["Course Name"].replace("/", "-").replace(":", "").strip()
    filename = f"{course_name}.md"
    filepath = os.path.join(output_dir, filename)

    # Write markdown file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f'alias: "{row["Course Code"]}"\n')
        f.write(f"date: {term_to_date(row['Term'])}\n")
        f.write("---\n\n")
        f.write(f"# {row['Course Name']}\n\n")
        f.write(f"- **Course Code**: {row['Course Code']}\n")
        f.write(f"- **Curriculum**: {row['Curriculum']}\n")
        f.write(f"- **Class**: {row['Class']}\n")
        f.write(f"- **SKS**: {row['SKS']}\n")
        f.write(f"- **IRS Status**: {row['IRS Status']}\n")
        f.write(f"- **Final Grade**: {row['Final Grade'] or 'N/A'}\n")
        f.write(f"- **Letter Grade**: {row['Letter Grade']}\n")

import pandas as pd

# Load structured transcript
df = pd.read_csv("structured_transcript.csv")

# Create a new Markdown file
with open("All Courses.md", "w", encoding="utf-8") as f:
    f.write("# 📚 All Courses\n\n")
    grouped = df.groupby("Term")

    for term, courses in grouped:
        f.write(f"## {term}\n\n")
        for _, row in courses.iterrows():
            course_name = row["Course Name"].replace("/", "-").replace(":", "").strip()
            f.write(f"- [[{course_name}]]\n")
        f.write("\n")
