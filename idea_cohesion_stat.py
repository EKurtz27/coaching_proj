import pandas as pd
import numpy as np
import math

level1_coach = ['Head Coach']
level2_coach = ['Offensive Coordinator', 'Special Teams Coordinator', 'Co-Special Teams Coordinator', 'Defensive Coordinator', 'Associate Head Coach', 
                'Recruiting Coordinator', 'Co-Offensive Coordinator', 'Co-Recruiting Coordinator', 'Assistant Head Coach', 'Co-Defensive Coordinator']
level3_coach = ['Running Game Coordinator', 'Passing Game Coordinator', 'Offensive Assistant Coach', 'Assistant Coach (Defense)', 'Assistant Coach (Offense)', 
                'Assistant Coach', 'Defensive Assistant Coach', 'Assistant Coach (Special Teams)', 'Assistant Defensive Coordinator', 'Assistant Special Teams Coordinator', 
                'Assistant Recruiting Coordinator', 'Assistant Offensive Coordinator', 'Strength and Conditioning Coach', 'Head Strength and Conditioning Coach']
level4_coach = ['Defensive Ends Coach', 'Offensive Line Coach', 'Defensive Tackles Coach', 'Running Backs Coach', 'Outside Linebackers Coach', 'Cornerbacks Coach', 
                'Tight Ends Coach',  'Wide Receivers Coach', 'Safeties Coach', 'Inside Linebackers Coach', 'Defensive Line Coach', 'Special Teams Coach', 'Quarterbacks Coach', 
                'Defensive Backs Coach', 'Linebackers Coach', 'Secondary Coach', 'Nickels', 'Offensive Tackles Coach', 'Inside Receivers Coach', 'Offensive Guards Coach', 
                'Co-Quarterbacks Coach', 'Co-Running Backs Coach']
level5_coach = ['Director of Player Development', 'Defensive Analyst', 'Offensive Analyst', 'Director of High School Relations', 'Quality Control Coach',
                 'Player Personnel Analyst', 'Graduate Assistant', 'Director of Player Personnel', 'Assistant Strength and Conditioning Coach', 
                 'Assistant Passing Game Coordinator', 'Director of Operations', 'Video Coordinator']

coach_position_hierarchy = [level1_coach, level2_coach, level3_coach, level4_coach, level5_coach]

def cohesion_stat(coach_name, coach_pos, dist_score: int, years_between, curr_job_years, direct_path):
    # Diff_index: the more 'different' the ideas, the higher the value
    # Division by "years_between": the more years between, 
    # the more likely to reach an equalibrium of ideas between coaches
    # Division by current job years: more years working together, more similar perspectives become
    num_nan = 0
    if dist_score == float('inf'):
        dist_score = 7
        num_nan += 1
    if curr_job_years == 0:
        curr_job_years = 1
    if years_between == 0 or math.isnan(years_between):
        years_between = 1
    diff_index = (dist_score / (years_between * curr_job_years))
    if direct_path == True:
        # If path goes directly to head coach, assume slight increase in similarity
        diff_index = diff_index * 0.75
    
    found = False
    for i, pos_list in enumerate(coach_position_hierarchy):
        if coach_pos in pos_list:
            # Need to fix, need to flip ordering
            coach_impact_level = (len(coach_position_hierarchy)) - i
            found = True
            break
    if found == False:
        print(f"{coach_name} has position not encoded. Defaulted to 1. Please update coding scheme")
        coach_impact_level = 1
    
    return (diff_index * coach_impact_level, num_nan)

    
for year in range(2020, 2026):
    
    stats_df = pd.read_csv(f"data/LCAs/{year}_distances.csv")
    stats_dict = {}
    nans_dict = {}

    grouped_teams = stats_df.groupby("Team")
    for team, group_df in grouped_teams:
        if len(group_df) >= 3:
            stats = []
            total_nans = 0
            for i, row in group_df.iterrows():
                stat, nans = cohesion_stat(
                    row['Queried Coach'],
                    row["Queried Coach Position"], 
                    row["Combined Distance"],
                    row["Years Between Mentorship"],
                    row["Years Working Current Position"],
                    row["Direct Path"])
                stats.append(stat)
                total_nans += nans
            average_score = sum(stats) / len(stats)
            stats_dict[team] = average_score
            nans_dict[team] = total_nans
            
    stats_df = pd.DataFrame({
        "Team": list(stats_dict.keys()),
        "AverageScore": list(stats_dict.values()),
        "Missing Values": list(nans_dict.values())
    })
    stats_df = stats_df.sort_values(by='AverageScore', ascending=False)
    stats_df.to_csv(f"data/cohesion_stats/{year}.csv", index=False)
    values = np.array(list(stats_dict.values()))
    print(f"{year} Statistics")
    print(f"Values: {len(values)}")
    print(f"Mean: {np.mean(values)}")
    print(f"Standard deviation: {np.std(values)}")
    print(f"Min: {min(values)}")
    print(f"25th Percentile: {np.percentile(values, 25)}")
    print(f"Median: {np.percentile(values, 50)}")
    print(f"75th Percentile: {np.percentile(values, 75)}")
    print(f"max: {max(values)}")
    print("")




