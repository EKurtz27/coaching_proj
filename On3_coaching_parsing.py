# Step 1: Pull the 'slug' for each coach to quickly load their respective webpage later
# Pulls directly from the On3 API
import requests
import json
from datetime import datetime

url = "https://api.on3.com/public/rdb/v1/coaches/salaries"
params = {
    "sportKey": "1", 
    "year": "2025",
    "orderBy": "school",
    "direction": "ASC",
    "page": "1" # Initial page number doesn't matter, as the code will run through all available pages
}

def pull_coach_slugs(url, params, output_file_name):
    """
    Uses the On3 API to pull the 'slug' for each coach, allowing for fast lookup of each coach's
    page for BeautifulSoup parsing. Flags coaches with incomplete data for further manual review.
    Reduces duplicates by checking if a coach is already in the dataset (in that year or prior years).

    Saves the output as a JSON file with the format:
    Year { [Coach 1, Coach 2, etc] }, where each coach has the structure {Name, Slug} 
    Year correlates with the most recent year the coach was actively listed in the On3 database
    """

    response = requests.get(url, params = params)



    all_years_data = {}

    for year in range(datetime.now().year, 2021, -1):
        params['year'] = year
        params['page'] = 1
        response = requests.get(url, params = params) # Get data for that year to know how many pages to check

        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Request failed on year {year}")
            continue

        year_coach_data = []


        page_count = data['pagination']['pageCount']
        #print(f"Page count for year {year} is {page_count}") [debug option]
        for page in range(page_count):
            page += 1
            params['page'] = page

            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                coaches = data['list']
                for coach in coaches:
                    values_to_check = [
                        coach.get('fullName'),
                        coach.get('slug')
                    ]
                    if any(value is None for value in values_to_check):
                        print(f"Error reading coach {coach['fullName']} for year {year}") # Track data that must be manually checked 
                        continue

                    if coach['slug'] in [coach_info['Slug'] for coach_info in year_coach_data]:
                        #print(f"Coach {coach['fullName']}'s URL was already found once this year!") 
                        continue

                    for prev_year_data in all_years_data.values():
                        if coach['slug'] in [coach_info['Slug'] for coach_info in prev_year_data]:
                          #print(f"Coach {coach['fullName']}'s URL is already in file, skipping")
                          continue
                    coach_info = {
                      'Name': coach['fullName'],
                      'Slug': coach['slug']
                    }

                    year_coach_data.append(coach_info) # Add each coach to the list of coaches for that year
        print(f"Number of coaches found in {year}: {len(year_coach_data)}")
        all_years_data[year] = year_coach_data # Add that year to the larger dictionary


    json_output = json.dumps(all_years_data, indent=4)
    with open(f'data/{output_file_name}.json', 'w') as f:
      f.write(json_output)

# Step 2: use the slugs to parse each coach's full coaching history from the On3 page using BeautifulSoup

from bs4 import BeautifulSoup
import re

def generate_coaching_database_json(input_file_name, json_output_name):
    """
    Converts the slugs in the previously generated JSON file into a raw master database of coaching positions, in JSON format.
    Returns a JSON file saving each coaches position as a JSON object containing:
    { Name, Team, Position, Start Year, End Year, Seasons with Team }, however this data is raw and contains duplicates.

    Each coach's full coaching history is parsed using BeautifulSoup on the Coaching History table from each coach's On3 page.
    Each position a coach has served in is saved seperately, meaning most coaches have multiple JSON objects for each of their stops on their career.

    Of note: Coaches whose tenure is listed as 'XXXX - present' are given an end date of the current year. To compensate for the current year's season not being over
    (ex: the 2025 season will not be completed until 2026), all coaching tenures that do not have the 'present' label are given an extra season.

    This means a new coach with a tenure of '2024 - present' is interpreted as '2024 - 2025', and therefore has completed 1 season with the team, because
    the 2025 season has not yet happened. Conversely, a coach with a tenure of '2016-2018' completed the 2016, 17, and 18 seasons, so a season is added to compensate
    for 2016-2018 equaling 2.
    """
    with open(f'{input_file_name}.json', 'r') as f:
        json_data = json.load(f)

    coaching_megalist = []

    for year in json_data:
        for coach in json_data[year]:
            coach_on3_url = f'https://www.on3.com/db/coach/{coach['Slug']}/'

            page = requests.get(coach_on3_url)
            contents = page.content

            soup = BeautifulSoup(contents, features="html.parser")
            all_jobs = soup.find_all('div', class_ = 'CoachHistory_historyListWrapper__i5n8y')
            #print(f"{coach}'s Coaching History:"")
            for job in all_jobs:
                team = job.find('h5', class_ = 'MuiTypography-root MuiTypography-h5 CoachHistory_teamName__2E139 css-6od08f-MuiTypography-root').text
                position = job.find('span', class_ = 'MuiTypography-root MuiTypography-caption CoachHistory_position__QN_5S css-d163s0-MuiTypography-root').text
                years_raw = job.find('span', class_ = 'MuiTypography-root MuiTypography-caption CoachHistory_year__yMj7Z css-d163s0-MuiTypography-root')
                regex_result = re.search(r"(\d+) - (\d+|\w+)", years_raw.get_text()) 
                start_year = int(regex_result.group(1))
                end_year = regex_result.group(2)
                currently_employed = False
                if end_year == 'present':
                    end_year = datetime.now().year
                    currently_employed = True # Discounts current season in calculation of number of seasons with team
                else: 
                    end_year = int(end_year)

                if currently_employed == True:
                    seasons_with_team = end_year - start_year
                else: 
                    seasons_with_team = end_year - start_year + 1
                #print(f"{team}, {position}, from {start_year} to {end_year}, that's {seasons_with_team} seasons, employment at job equals {currently_employed}")
                # Print debugger to check if the parsing is accurate
                job_json = {
                    'Name': coach['Name'],
                    'Team': team,
                    'Position': position,
                    'Start Year': start_year,
                    'End Year': end_year,
                    'Seasons with Team': seasons_with_team
                }
                coaching_megalist.append(job_json)


    with open(f'data/{json_output_name}.json', 'w') as raw_data_file:
        json.dump(coaching_megalist, raw_data_file, indent=4)


# Step 3: clean the JSON file by comparing JSON objects and recreating a clean list

def clean_duplicates_json(json_file_input, cleaned_file_name):
    """
    Cleans a the JSON file of coaching positions by creating a new list of JSON objects without duplicates and then writing a new file. 
    """

    with open(f'{json_file_input}.json', 'r') as raw_data_file:
        raw_data = json.load(raw_data_file)

    cleaned_list = []

    for coach_job_json in raw_data:
        if coach_job_json not in cleaned_list:
            cleaned_list.append(coach_job_json)

    with open(f'data/{cleaned_file_name}.json', 'w') as cleaned_data_file:
        json.dump(cleaned_list, cleaned_data_file, indent=4)

import pandas as pd

def cleaned_json_to_csv(cleaned_json_file, csv_file_name):  
    """

    """
    df = pd.read_json(f'{cleaned_json_file}.json')
    coaching_database_reordered = df.loc[:, ['Start Year', 'End Year', 'Team', 'Name', 'Position', 'Seasons with Team']].drop('End Year', axis = 1)



    coaching_database = coaching_database_reordered.sort_values(by=['Start Year', 'Team'], ascending=False)
    coaching_database.to_csv(f'data/{csv_file_name}.csv', index = False)

# Function Calls

url = "https://api.on3.com/public/rdb/v1/coaches/salaries"
params = {
    "sportKey": "1", 
    "year": "2025",
    "orderBy": "school",
    "direction": "ASC",
    "page": "1" # Initial page number doesn't matter, as the code will run through all available pages
}

pull_coach_slugs(url, params, 'coach_slugs')

generate_coaching_database_json('coach_slugs', 'coach_jobs_raw')

clean_duplicates_json('coach_jobs_raw', 'coach_jobs_clean')

cleaned_json_to_csv('coach_jobs_clean', 'clean_sorted_coach_jobs')





