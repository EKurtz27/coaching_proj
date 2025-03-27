# Basic script to scrape the Wikipedia pages for NCAA Division I FBS football programs
# Includes manual correction of certain pages
# Exports to team_sites.csv, already uploaded to the respository. This code is provided for transparency
import wikipedia as wp
import pandas as pd
import json

# Fetch the Wikipedia page content
page = wp.page("List of NCAA Division I FBS football programs")
read_page = pd.read_html(page.html())
cfb_geninfo = read_page[0]
schools = cfb_geninfo['School'].tolist()
team_sites = []
for school in schools: # Merge school and wikipage result for easy conversion to dictionary
    search_result = wp.search(school + " football", results=1)
    team_tuple = (school, search_result[0])
    team_sites.append(team_tuple)

# misidentified schools: Charlotte: Charlotte FC, Houston: Houston Texans, Miami(FL): 2001 Miami Hurricanes football team
# misid cont: Ohio: Ohio State Buckeyes football, Washington: Washington Commanders
for i, item in enumerate(team_sites):
    if item[0] == "Charlotte":
        team_sites[i] = ("Charlotte 49ers", "Charlotte 49ers football")
    if item[0] == "Houston":
        team_sites[i] = ("Houston Cougars", "Houston Cougars football")
    if item[0] == "Miami (FL)":
        team_sites[i] = ("Miami Hurricanes", "Miami Hurricanes football")
    if item[0] == "Ohio":
        team_sites[i] = ("Ohio Bobcats", "Ohio Bobcats football")
    if item[0] == "Washington":
        team_sites[i] = ("Washington Huskies", "Washington Huskies football")

sites_dict = dict(team_sites)

with open('team_sites.json', 'w') as f:
    json.dump(sites_dict, f, indent=4)

with open('team_sites.json', 'r') as my_file:
    team_sites = json.load(my_file)


def get_team_page(team, database): #Fix?
    page_name = database[team]
    page = wp.page("'"+ page_name + "'", auto_suggest=True)
    links = page.links
    for link in links:
        if ('List' and 'coaches') in link:
                return link
    else:
            return 'No coach table found for ' + team
                                      

team_coach_pages = {}
for team in team_sites:
    team_coach_pages[team] =  get_team_page(team, team_sites)

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
