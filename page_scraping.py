import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import wikipedia as wp

with open('team_sites.json', 'r') as my_file:
    team_sites = json.load(my_file)


""" def get_team_page(team, database): #Fix?
    page_name = database[team]
    page = wp.page("'"+ page_name + "'", auto_suggest=True)
    links = page.links
    for link in links:
        if ('List' and 'coaches') in link:
                return link
    else:
            return 'No coach table found for ' + team
                    
print(get_team_page('Buffalo', team_sites))                    

team_coach_pages = {}
for team in team_sites:
    team_coach_pages[team] =  get_team_page(team, team_sites) """

with open('team_coach_pages.json', 'r') as my_file:
    coach_list_pages = json.load(my_file)

main_page_df = pd.DataFrame(coach_list_pages.items(), columns=['Team', 'Coaching List Page'])
coach_list_df = pd.DataFrame(team_sites.items(), columns=['Team', 'Main Page'])
df = pd.merge(coach_list_df, main_page_df, on='Team')
print(df)

df_json = df.to_json()
with open('team_database.json', 'w') as my_file:
    json.dump(df_json, my_file, indent=4)

with open('team_database.json', 'r') as my_file:
    team_database = json.load(my_file)

df_test = pd.read_json(team_database)
print(df_test)





