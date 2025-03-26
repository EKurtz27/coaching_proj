import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

team_sites = pd.read_json('team_sites.json')
team_sites = team_sites.to_dict()
print(team_sites['Air Force']['Air Force Falcons football'])

#def get_team_page(team, database):
    
