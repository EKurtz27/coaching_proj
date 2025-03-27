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

main_sites_dict = dict(team_sites)
print(main_sites_dict)

def get_team_page(team, database):
    page_name = database[team]
    page = wp.page("'"+ page_name + "'", auto_suggest=True)
    links = page.links
    for link in links:
        if ('List' and 'coaches') in link:
                return link
    else:
            return 'No coach table found for ' + team
                                      

team_coach_pages = {}
for team in main_sites_dict.keys():
    team_coach_pages[team] =  get_team_page(team, main_sites_dict)
print(team_coach_pages)
main_page_df = pd.DataFrame(main_sites_dict.items(), columns=['Team', 'Main Page'])
coach_list_df = pd.DataFrame(team_coach_pages.items(), columns=['Team', 'Coaching List Page'])
df = pd.merge(main_page_df, coach_list_df, on='Team')
print(df)

df_json = df.to_json()
with open('team_database.json', 'w') as my_file:
    json.dump(df_json, my_file, indent=4)

with open('team_database.json', 'r') as my_file:
    team_database = json.load(my_file)

df_test = pd.read_json(team_database)
print(df_test)
