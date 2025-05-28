import networkx as nx
import pandas as pd
import matplotlib as plt

# Need to research network x for best implementation

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

def position_encoding (reference_df):
    reference_df["Encoded Position"] = []
    for coach_job in reference_df:
        if coach_job['Position'] in level1_coach:
            coach_job['Encoded Position'] = 1
        elif coach_job['Position'] in level2_coach:
            coach_job['Encoded Position'] = 2
        elif coach_job['Position'] in level3_coach:
            coach_job['Encoded Position'] = 3
        elif coach_job['Position'] in level4_coach:
            coach_job['Encoded Position'] = 4


coaching_graph = nx.Graph()

input_file_name = input("Please enter the path to the CSV file you wish to read: ").strip()

with open(f"{input_file_name}", "r") as coach_jobs_csv:
    coach_jobs = pd.read_csv(coach_jobs_csv)

all_positions = coach_jobs['Position'].unique()
print(all_positions)

grouped_coaches = coach_jobs.groupby(by=["Season (Year)", "Team"])


for category, coach_grouping in grouped_coaches:
    for idx1, coach in coach_grouping.iterrows():
        for idx2, other_coach in coach_grouping.iterrows(): # This double loop method generates bidirectional connections automatically
            if idx1 == idx2:
                continue
            else:
                coaching_graph.add_edge(coach["Name"], other_coach["Name"], {'relationship': f"{coach['Position']} to {other_coach['Position']}", 
                                                                             'encoded_relationship': f"{coach['Encoded Position']} to {other_coach['Encoded Position']}"})
                


nx.draw(coaching_graph)
plt.savefig("test.png")