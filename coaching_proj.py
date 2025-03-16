from bs4 import BeautifulSoup
import requests
import wikipedia as wp
import pandas as pd

# Fetch the Wikipedia page content
page = wp.page("List of NCAA Division I FBS football programs")
read_page = pd.read_html(page.html())
cfb_geninfo = read_page[0]
schools = cfb_geninfo['School'].tolist()
print(schools)
