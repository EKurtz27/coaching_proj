# Basic script to scrape the Wikipedia pages for NCAA Division I FBS football programs
# Includes manual correction of certain pages
# Exports to team_sites.csv, already uploaded to the respository. This code is provided for transparency
import wikipedia as wp
import pandas as pd


# Fetch the Wikipedia page content
page = wp.page("List of NCAA Division I FBS football programs")
read_page = pd.read_html(page.html())
cfb_geninfo = read_page[0]
schools = cfb_geninfo['School'].tolist()
team_sites = []
for school in schools:
    search_result = wp.search(school + " football", results=1)
    team_tuple = (school, search_result[0])
    team_sites.append(team_tuple)

#misidentified schools: Charlotte: Charlotte FC, Houston: Houston Texans, Miami(FL): 2001 Miami Hurricanes football team
#misid cont: Ohio: Ohio State Buckeyes football, Washington: Washington Commanders
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


df = pd.DataFrame(team_sites, columns=['School', 'Wiki Page'])
df.to_csv('team_sites.csv', index=False)
