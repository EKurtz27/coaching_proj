import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

team_sites = pd.read_csv('team_sites.csv')
test = list(team_sites)
print(test)