import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import random

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

def position_encoding(reference_df):
    def encode_position(pos):
        if pos in level1_coach:
            return 1
        elif pos in level2_coach:
            return 2
        elif pos in level3_coach:
            return 3
        elif pos in level4_coach:
            return 4
        else:
            return np.nan

    reference_df["Encoded Position"] = reference_df["Position"].apply(encode_position)
coaching_graph = nx.DiGraph()

input_file_name = input("Please enter the path to the CSV file you wish to read: ").strip()

with open(f"{input_file_name}", "r") as coach_jobs_csv:
    coach_jobs = pd.read_csv(coach_jobs_csv)

position_encoding(coach_jobs)

grouped_coaches = coach_jobs.groupby(by=["Starting Season", "Team"])

def parse_seasons(val):
    import ast
    if pd.isna(val):
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except Exception:
            return [int(x) for x in val.split(',') if x.strip().isdigit()]
    return []

encoded_connections = {}
years_of_edges = {}
teams_of_edges = {}
mentor_status = {}
for category, coach_grouping in grouped_coaches:
    for idx1, coach in coach_grouping.iterrows():
        for idx2, other_coach in coach_grouping.iterrows(): # This double loop method generates bidirectional connections automatically
            if idx1 == idx2:
                continue
            else:
                coaching_graph.add_edge(
                    coach["Name"],
                    other_coach["Name"],
                    relationship=f"{coach['Position']} to {other_coach['Position']}"
                )
                encoded_connections[(coach['Name'], other_coach['Name'])] = (coach['Encoded Position'], other_coach['Encoded Position'])
                years_of_edges[(coach['Name'], other_coach['Name'])] = list(set(parse_seasons(coach['Seasons at Position'])) & set(parse_seasons(other_coach['Seasons at Position'])))
                teams_of_edges[(coach['Name'], other_coach['Name'])] = coach['Team']
                indiv_mentor_status = "Not a Mentor"  # Was the coach at the end of the edge a mentor to the coach at the start of the edge (0 = No)
                if other_coach['Encoded Position'] < coach['Encoded Position']:
                    indiv_mentor_status = "Mentor" # The coach was a distinct mentor
                if other_coach['Encoded Position'] == coach['Encoded Position']:
                    indiv_mentor_status = "Equal Standing" # The coaches were on equal footing, but might've had influence on each other
                mentor_status[(coach['Name'], other_coach['Name'])] = indiv_mentor_status


pos = nx.spring_layout(coaching_graph)

nx.set_edge_attributes(coaching_graph, encoded_connections, "Encoded Connection")
nx.set_edge_attributes(coaching_graph, years_of_edges, "Years of Connection")
nx.set_edge_attributes(coaching_graph, teams_of_edges, "Team of Connection")
nx.set_edge_attributes(coaching_graph, mentor_status, "Mentor Status")
             

edge_x = []
edge_y = []
edge_text = []
for edge in coaching_graph.edges(data=True):
    coach1 = edge[0]
    coach2 = edge[1]
    
    coach1_posx, coach1_posy = pos[coach1]
    coach2_posx, coach2_posy = pos[coach2]

    edge_x.append(coach1_posx)
    edge_x.append(coach2_posx)
    edge_x.append(None)

    edge_y.append(coach1_posy)
    edge_y.append(coach2_posy)
    edge_y.append(None)

    rel = edge[2].get('relationship', '')
    edge_text.append(rel)
    edge_text.append(rel)
    edge_text.append('')

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=.5, color='#888'),
    hoverinfo='none'  # Hover for information option generated below
)

# Add markers at edge midpoints for better hover hitboxes
edge_marker_x = []
edge_marker_y = []
edge_marker_text = []

for edge in coaching_graph.edges(data=True):
    coach1 = edge[0]
    coach2 = edge[1]
    rel_raw = edge[2].get('relationship', '')
    years = edge[2].get('Years of Connection', [])
    team = edge[2].get('Team of Connection', '')
    mentor = edge[2].get('Mentor Status', '')
    rel = f'{coach1} to {coach2}: {rel_raw}'
    hover_str = (
        f"{coach1} to {coach2}: {rel_raw}<br>"
        f"Years: {years}<br>"
        f"Team: {team}<br>"
        f"Mentor Status: {mentor}"
    )

    x1, y1 = pos[coach1]
    x2, y2 = pos[coach2]
    edge_marker_x.append((x1 + x2) / 2)
    edge_marker_y.append((y1 + y2) / 2)
    edge_marker_text.append(hover_str)

edge_marker_trace = go.Scatter(
    x=edge_marker_x,
    y=edge_marker_y,
    mode='markers',
    marker=dict(size=4, color='red', opacity=0.8),
    hoverinfo='text',
    text=edge_marker_text,
    showlegend=False
)

node_x = []
node_y = []
node_text = []
node_adjacencies= []
for node in coaching_graph.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(node)
    node_adjacencies.append(len(list(coaching_graph.adj[node])))

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    hoverinfo='text',
    text=node_text,
    marker=dict(
        showscale=True,
        # colorscale options
        #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
        #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
        #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
        colorscale='YlGnBu',
        reversescale=True,
        color=node_adjacencies,
        size=10,
        colorbar=dict(
            thickness=15,
            title=dict(
              text='Node Connections',
              side='right'
            ),
            xanchor='left',
        ),
        line_width=2))

fig = go.Figure(data=[edge_trace, edge_marker_trace, node_trace],
                layout=go.Layout(
                    title=dict(
                        text= "<br>Network graph made with Python",
                        font=dict(
                            size=16
                        )
                    ),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                    text="Python code: <a href='https://plotly.com/python/network-graphs/'> https://plotly.com/python/network-graphs/</a>",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )

fig.show()



print(f"Number of edges: {coaching_graph.number_of_edges()}")
print(f"Number of nodes: {coaching_graph.number_of_nodes()}")


