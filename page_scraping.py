import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json

with open('team_sites.json', 'r') as my_file:
    team_sites = json.load(my_file)

print(team_sites['Air Force'])
#def get_team_page(team, database):
    
