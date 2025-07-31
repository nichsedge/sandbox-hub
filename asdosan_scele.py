from bs4 import BeautifulSoup as bs

html_page = """
INSPECT ELEMENT
"""

soup_page = bs(html_page, "html.parser")
quotes = soup_page.findAll("div", {"class": "author"})

lst = []
for q in quotes:
    # print(q)
    fav_quote = q.findAll("a")
    # a = fav_quote[0].split(" ")
    lst += fav_quote[0].text.split(" ")
    # aquote = fav_quote[0].text.strip()

    # fav_author = quote.findAll("p", {"class": "author"})
    # author = fav_author[0].text.strip()
print(lst)

import pandas as pd
import numpy as np

x = pd.read_csv("input.csv")
print(x)

arr_new = []
for i in x["npm"]:
    if str(i) in lst:
        appendo = [i, 1]
    else:
        appendo = [i, 0]

    arr_new.append(appendo)


df2 = pd.DataFrame(np.array(arr_new), columns=["npm", "kerja"])

df2.to_excel("output.xls")
