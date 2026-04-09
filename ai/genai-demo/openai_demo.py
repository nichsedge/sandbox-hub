# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "openai>=2.31.0",
# ]
# ///
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-nano", input="python code to scrape indonesia LHKPN"
)

print(response.output_text)
