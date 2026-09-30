# pip install spacy

# python -m spacy download xx_ent_wiki_sm

# python -m spacy download en_core_web_sm

import pandas as pd

df = pd.DataFrame()

import requests
from bs4 import BeautifulSoup

# Make a request to the webpage
url = "https://nasional.kompas.com/read/2017/11/07/18102221/di-sidang-mk-peneliti-lipi-nilai-ahmadiyah-tak-bisa-dianggap-sesat?page=all"  # Replace with the actual URL
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.content, "html.parser")

# Initialize an empty dictionary
scraped_data = {}

scraped_data["title"] = soup.find(class_="read__title").text
scraped_data["topic_subtitle"] = soup.select_one(".topicSubtitle ul li a").text
scraped_data["read_time"] = soup.select_one(".read__time")
scraped_data["writers"] = [h6.text for h6 in soup.select(".credit-title-name")]
scraped_data["read_content"] = "\n".join(
    p.text for p in soup.select(".read__content p")
)

# Convert the dictionary to a Pandas DataFrame
df = pd.DataFrame([scraped_data])

df.to_csv("scraped_data.csv", index=False)

import spacy

# Load the Indonesian model for spaCy
nlp = spacy.load("xx_ent_wiki_sm")  # This is the small Indonesian model

# Assuming 'read_content' is the variable containing the scraped content
doc = nlp(scraped_data["read_content"])

# Extract entities
entities = [(ent.text, ent.label_) for ent in doc.ents]

s = set()
for entity in entities:
    s.add(entity[0] + "|" + entity[1])

for i in s:
    print(i)

import urllib.parse

import requests
from bs4 import BeautifulSoup

# Define the base URL and search parameters
scraped_data = []


# Function to scrape a single page
def scrape_page(query, page):
    base_url = "https://search.kompas.com/search/"
    safe_string = urllib.parse.quote_plus(query)
    params = {
        "q": safe_string,
        "submit": "Submit",
        "gsc.tab": "0",
        "gsc.q": query.replace(" ", "%20"),
        "gsc.sort": "date",
        "gsc.page": page,
    }

    print(params)
    response = requests.get(base_url, params=params)
    soup = BeautifulSoup(response.content, "html.parser")

    print(soup.get_text)

    # Print the list of hrefs
    # print(hrefs)


# Process the first page
org = "Front Pembela Islam (FPI)"
scrape_page(org, 1)

from bs4 import BeautifulSoup
import requests

url = "https://indeks.kompas.com/?site=all&date=2023-11-03&page=1"
req = requests.get(url)

# print(req.text)

soup = BeautifulSoup(req.text, "lxml")

a = soup.find_all("a", {"class": "article__link"})

kumpulan_link = []
kumpulan_paragraf = []

for link in a:
    kumpulan_link.append(link["href"])

for link in kumpulan_link:
    halaman = requests.get(link)
    soup_baru = BeautifulSoup(halaman.text, "lxml")
    paragraf = soup_baru.find_all("p")
    for kalimat in paragraf:
        kumpulan_paragraf.append(kalimat.text)

with open("paragraf.txt", "a") as f:
    for paragraf in kumpulan_paragraf:
        print("penulisan berhasil")
        f.writelines(paragraf + "\n")

import pandas as pd

df = pd.read_csv("organization.csv")

for index, row in df.iterrows():
    # Access each column in the row using row['column_name']
    print(row["organization_name"])
