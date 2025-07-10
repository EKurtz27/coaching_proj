import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go


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

def position_encoding(reference_df):
    """
    Adds an encoded position value to each coach position.

    Args:
        reference_df (pd.DataFrame): A pandas dataframe, generated from the On3_coaching_parsing CSV. Will look for column "Position".

    Returns:
        None: Adds a new column to the provided dataframe that groups coaches based on influence over play development and the on-field product.
            1 Represents the most influence (head coaches), 5 represents a lower influence (specifically over development and playcalling/scheme).
            This allows for easy sorting of coach influence over teams in further research.

    Note:
        The encoded value for each possible position is listed above (or through keyword searching 'level#_coach'). Positions were identified by listing the unique values from the
        'Position' column in the CSV file generated from On3_coaching_parsing. If any position is not listed, a terminal print will occur. The new position can be easily added
        to one of the current lists above. These lists can also be altered depending on the researcher's view of coaching hierarchies.
    """
    
    def encode_position(pos):
        if pos in level1_coach:
            return 1
        elif pos in level2_coach:
            return 2
        elif pos in level3_coach:
            return 3
        elif pos in level4_coach:
            return 4
        elif pos in level5_coach:
            return 5
        else:
            print(f"The coaching position {pos} is not yet listed")
            return np.nan

    reference_df["Encoded Position"] = reference_df["Position"].apply(encode_position)

def create_nx_graph(coach_jobs_df):    
    """
    Creates a NetworkX graph of coaching connections, adds relevant data to edges (see below).

    Args:
        coach_jobs_df (pd.DataFrame): A pandas DataFrame generated from On3_coaching_parsing and updated with the function 'position_encoding'.

    Returns:
        coaching_graph (nx.MultiDiGraph): A directed NetworkX graph that allows for parallel edges (ex: coaches who work together at different schools). \n
        Adds the following data to each edge:
        {'data':  {
            'relationship': '{coach1's position}' to '{coach2's position}' on '{shared team}', 
            'encoded_connection': (coach1's encoded position, coach2's encoded position),
            'years_of_connection': [list of shared years], 
            'team_of_connection': 'Shared team', 
            'mentor_status': 'Equal Standing, Mentor, or Not a Mentor', 
            'source_position': 'Coach1's position', 
            'target_position': 'Coach2's position', 
            'visualization_tracker': 1 or 0
        }}}

    Behavior:
        - Groups coaching jobs (rows of the DataFrame) by team before iterating through each grouping to find year matches between coaches
        - When a match is found, it is checked against a duplicate tracker
        - If it is not a duplicate, the above information is added to a dictionary, which is then added as edge attributes to the nx graph
    """
    coaching_graph = nx.MultiDiGraph()

    position_encoding(coach_jobs_df)

    grouped_coaches = coach_jobs_df.groupby(by=["Team"])

    def parse_seasons(val):
        """
        Parses the input value representing seasons into a list of integers.

        Args:
            val (Any): The value to parse. Can be NaN, a list, or a string representation of a list or comma-separated integers.

        Returns:
            list: A list of integers representing seasons. Returns an empty list if input is NaN or cannot be parsed.

        Behavior:
            - If val is NaN, returns an empty list.
            - If val is already a list, returns it as is.
            - If val is a string, attempts to parse it as a Python literal (e.g., '[1, 2, 3]').
              If parsing fails, splits the string by commas and returns a list of integers found.
            - For any other type, returns an empty list.
        """

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
    source_position = {}
    target_position = {}
    visualization_tracker = {} # Having an edge for each direction is important for searching, but not vizualization. Reduces vizualized edges by half
    
    duplicate_tracker = set()
    for category, coach_grouping in grouped_coaches:
        for idx1, coach in coach_grouping.iterrows():
            for idx2, other_coach in coach_grouping.iterrows(): # This double loop method generates bidirectional connections automatically
                if idx1 == idx2:
                    continue
                else:
                    overlap_years = tuple(sorted(set(parse_seasons(coach['Seasons at Position'])) & set(parse_seasons(other_coach['Seasons at Position']))))
                    duplicate_check = (coach['Name'], other_coach['Name'], coach['Team'], overlap_years) # Ensures no double counting while allowing coaches to work together at the same school over diff. time periods
                    if overlap_years and duplicate_check not in duplicate_tracker:
                        edge_key = coaching_graph.add_edge(
                            coach["Name"],
                            other_coach["Name"],
                            relationship=f"{coach['Position']} to {other_coach['Position']} on {coach['Team']}"
                        )

                        duplicate_tracker.add(duplicate_check)

                        # Adds all possibly relevant data to dictionaries, to be passed to the nx graph later
                        encoded_connections[(coach['Name'], other_coach['Name'], edge_key)] = (coach['Encoded Position'], other_coach['Encoded Position'])
                        years_of_edges[(coach['Name'], other_coach['Name'], edge_key)] = list(set(parse_seasons(coach['Seasons at Position'])) & set(parse_seasons(other_coach['Seasons at Position'])))
                        teams_of_edges[(coach['Name'], other_coach['Name'], edge_key)] = coach['Team']
                        indiv_mentor_status = "Not a Mentor"  # Was the coach at the end of the edge a mentor to the coach at the start of the edge
                        if other_coach['Encoded Position'] < coach['Encoded Position']:
                            indiv_mentor_status = "Mentor" # The coach was a distinct mentor
                        if other_coach['Encoded Position'] == coach['Encoded Position']:
                            indiv_mentor_status = "Equal Standing" # The coaches were on equal footing, but might've had influence on each other
                        mentor_status[(coach['Name'], other_coach['Name'], edge_key)] = indiv_mentor_status
                        source_position[(coach['Name'], other_coach['Name'], edge_key)] = coach['Position']
                        target_position[(coach['Name'], other_coach['Name'], edge_key)] = other_coach['Position']
                        if idx1 > idx2:
                            visualization_tracker[(coach['Name'], other_coach['Name'], edge_key)] = 0
                        if idx1 < idx2: 
                            visualization_tracker[(coach['Name'], other_coach['Name'], edge_key)] = 1
    # Passing data to the nx graph edges
    nx.set_edge_attributes(coaching_graph, encoded_connections, "encoded_connection")
    nx.set_edge_attributes(coaching_graph, years_of_edges, "years_of_connection")
    nx.set_edge_attributes(coaching_graph, teams_of_edges, "team_of_connection")
    nx.set_edge_attributes(coaching_graph, mentor_status, "mentor_status")
    nx.set_edge_attributes(coaching_graph, source_position, "source_position")
    nx.set_edge_attributes(coaching_graph, target_position, "target_position")
    nx.set_edge_attributes(coaching_graph, visualization_tracker, "visualization_tracker")

    return coaching_graph


def plotly_graph(encoded_df):
    """
    Generates and displays an interactive network graph using Plotly based on the provided encoded DataFrame.
    The function performs the following steps:
    1. Constructs a NetworkX graph from the input DataFrame using `create_nx_graph`.
    2. Computes node positions using the ForceAtlas2 layout algorithm.
    3. Draws edges between nodes, with optional filtering based on the 'vizualization_tracker' attribute.
    4. Adds edge markers at midpoints for enhanced hover tooltips, displaying relationship details such as years, team, and mentor status.
    5. Visualizes nodes, coloring them by the number of connections (degree), and includes a colorbar for reference.
    6. Configures the Plotly figure layout, including title, legend, axis formatting, and annotations.
    Parameters:
        encoded_df (pd.DataFrame): A DataFrame containing encoded information about nodes and edges, 
                                   including attributes such as 'relationship', 'years_of_connection', 
                                   'team_of_connection', 'mentor_status', and 'vizualization_tracker'.
    Returns:
        None. Displays the interactive Plotly network graph in the default browser or notebook output.
    """
    coaching_graph = create_nx_graph(encoded_df)

    pos = nx.forceatlas2_layout(coaching_graph, scaling_ratio = 5)                

    edge_x = []
    edge_y = []
    edge_text = []
    for edge in coaching_graph.edges(data=True):
        if edge[2].get('vizualization_tracker') == 1:   
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
        years = edge[2].get('years_of_connection', [])
        team = edge[2].get('team_of_connection', '')
        mentor = edge[2].get('mentor_status', '')
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
                            text= "<br>NetworkX Graph of College coaching connections, powered by Plotly",
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


if __name__ == "__main__":
    input_file_name = input("Please enter the path to the CSV file you wish to read: ").strip()
    with open(f"{input_file_name}", "r") as coach_jobs_csv:
        coach_jobs_df = pd.read_csv(coach_jobs_csv)
    position_encoding(coach_jobs_df)
    plotly_graph(coach_jobs_df)


