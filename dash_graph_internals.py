if __name__ == '__main__':
    print("Error: you are running a useless file, please run 'dash_graph.py' to generate the webpage")

def nx_to_cytoscape(G):
    """
    Parses a NetworkX graph into nodes and edges usable for a Dash cytoscape graph

    Args:
        G (nx.MultiDiGraph): A directed NetworkX graph that allows for parallel edges.
        For details on G, see 'create_nx_graph' in 'basic_graph_generation.py'

    Returns:
        elements (list): A list of elements to be read into a cytoscape. Starts with all node values,
        then includes all edge information. 

        Node values include the following information::
            {'data': {
                'coach_name': 'coach name',
                'test': 'test'
            }}
            
        Edge values include the following information::
            {'data': {
                'id': 'edge-{enumerated number}', 
                'description': 'coach1's name -> coach2's name', 
                'source': 'coach1's name',
                'target': 'coach2's name', 
                'encoded_connection': [coach1's encoded position, coach2's encoded position], 
                'years_of_connection': [list of shared years], 
                'team_of_connection': 'shared team', 
                'mentor_status': 'Mentor, Equal Standing, or Not a Mentor', 
                'source_position': 'coach1's position', 
                'target_position': 'coach2's position', 
                'visualization_tracker': 0 or 1
            }}

    Behavior:
        - Adds nodes to element list first by iterating through G.nodes
        - Adds edges to element list by iterating through enumerate(G.edges(data=True))
            - Adds both additional information and information from nx graph to the edge data
    
    """
    elements = []

    for node in G.nodes:
        elements.append({'data': {'id': str(node), 'coach_name': str(node)}})

    for idx, (source, target, data) in enumerate(G.edges(data=True)):
        # Only include edges where visualization_tracker == 1
        if data.get('visualization_tracker', 0) == 1:
            edge_data = {
                'id': f'edge-{idx}',
                'description': f'{source} -> {target}',
                'source': str(source),
                'target': str(target),
                **{k: v for k, v in data.items() if k != 'relationship'}
            }
            elements.append({'data': edge_data})

    return elements

def generate_color(index, total):
    """Generates colors evenly spaced around the color wheel"""
    hue = int(360 * index / total)
    return f"hsl({hue}, 70%, 50%)"

def get_id_of_triggered(callback_context: dict) -> str:
    """
    Extracts and returns the component ID of the triggered input from a Dash callback context.

    Args:
        callback_context (dict): The Dash callback context, typically dash.callback_context, 
            containing information about which input triggered the callback.

    Returns:
        str: The component ID of the triggered input.

    Raises:
        IndexError: If no input has triggered the callback (i.e., triggered list is empty).
        KeyError: If 'prop_id' key is missing in the triggered dictionary.
    """
    return callback_context.triggered[0]['prop_id'].split('.')[0]

def parse_csv_file(input_file, filename: str):
    """
    Parses a base64-encoded CSV file, extracts team and season information, and generates a network graph.

    Args:
        input_file (str): The base64-encoded contents of the uploaded file, typically in the format "data:<type>;base64,<content>".
        filename (str): The name of the uploaded file, used to check if it is a CSV.

    Returns:
        tuple: A tuple containing:
            - list: Cytoscape-compatible elements representing the generated network graph (empty list if not a CSV or on error).
            - list: List of unique team names, with 'All' as the first element (empty list if not a CSV or on error).
            - list: List of unique years/seasons at position, with 'All' as the first element (empty list if not a CSV or on error).

    Notes:
        - Expects the CSV to have at least 'Team' and 'Seasons at Position' columns.
        - Handles errors gracefully by returning empty lists and printing the exception.
    """
    import base64
    import io
    import pandas as pd
    from basic_graph_generation import create_nx_graph
    content_type, content_string = input_file.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            team_list = ['All'] + sorted(df['Team'].unique().tolist(), reverse=True)
            years_list = set()
            for _, row in df.iterrows():
                years_worked = row['Seasons at Position']
                if isinstance(years_worked, list):
                    years_list.update(years_worked)
                elif years_worked:
                    years_list.add(years_worked)
            years_list = ['All'] + sorted(years_list, reverse=True)
            G = create_nx_graph(df)
            elements = nx_to_cytoscape(G)
            return elements, team_list, years_list
        else:
            return [], [], []
    except Exception as e:
        print(e)
        return [], [], []

def parse_json_file():
    """
    Parses the 'visualization_elements_dump.json' file and extracts unique teams and years.
    Reads a JSON file containing visualization elements, then iterates through each element to collect unique team names and years of connection. Returns the list of elements, a sorted list of teams (with 'All' as the first entry), and a sorted list of years (with 'All' as the first entry).
    Returns:
        tuple: A tuple containing:
            - elements (list): The list of elements loaded from the JSON file.
            - teams_list (list): A list of unique team names, sorted alphabetically, with 'All' as the first entry.
            - years_list (list): A list of unique years, sorted in descending order, with 'All' as the first entry.
    """
    import json

    with open('visualization_elements_dump.json') as f:
        elements = json.load(f)
        teams = set()
        years = set()
        for el in elements:
            data = el.get('data', {})
            team = data.get('team_of_connection')
            years_of_connection = data.get('years_of_connection')
            if team:
                teams.add(team)
            if isinstance(years_of_connection, list):
                years.update(years_of_connection)
            elif years_of_connection:
                years.add(years_of_connection)
        teams_list = ['All'] + sorted(teams, reverse=False)
        years_list = ['All'] + sorted(years, reverse=True)

    return elements, teams_list, years_list

def gather_coaching_positions(elements: list, coach: str) -> list:
    """
    Creates list of all years a coach has been employed, includes information on each job.

    Args:
        elements (list): List of all nodes and edges of the Dash cytoscape. Further information in 'nx_to_cytoscape'.
        coach (str): The coach the function gathers employment data for

    Returns:
        coached_info (list(tuple)): List of all years the coach has coached, sorted by year in descending order.
        Each tuple contains the sentence to be displayed, the team coached for, and the year of the position.

    Behavior:
        - Searches elements for edges that contain the coach
        - When function gets a hit, adds all years in that edge to a list to prevent double counting of years
        - Determines if the coach is the 'source' or 'target' of the edge
            - Assigns either the 'source_position' or 'target_position' to the coach when constructing the display sentence
        - Generates the tuple of (display sentence, team, year)
        - Adds the tuple to a list to be returned
        - Sorts the list by the 3rd element in the tuple (year) in descending order
    """
    years_coached = []
    coached_info = []
    for el in elements:
        data = el.get('data', {})
        # Check if the clicked coach is involved in this edge
        if data.get('source', "") == coach or data.get('target', "") == coach:
            # Determine role
            is_source = data.get('source', "") == coach
            is_target = data.get('target', "") == coach
            team = data.get('team_of_connection')
            for year in data.get('years_of_connection', []):
                # Only need to hit on one edge per year
                if year not in years_coached:
                    years_coached.append(year)
                    if is_source:
                        sentence = f"{coach} coached for {team} as the {data['source_position']} in {year}"
                        coached_info.append((sentence, team, year))
                    if is_target:
                        sentence = f"{coach} coached for {team} as the {data['target_position']} in {year}"
                        coached_info.append((sentence, team, year))
    # Sort all years the coach has been employed by year (3rd item in each tuple)
    coached_info.sort(key=lambda tup: tup[2], reverse=True)

    return coached_info

def handle_all_selection(possible_values: list, constant_value, team_or_year: str) -> list:
    """
    Handles iterating through lists to create all new combinations when user selects 'All'. 
    Removes combinations containing 'All' 
    """
    if team_or_year == 'team':
        tupled_current_combos.extend([(t, constant_value) for t in possible_values[1:]])
        tupled_current_combos = [combo for combo in tupled_current_combos if "All" not in combo] # Remove initial All

    if team_or_year == 'year':
        tupled_current_combos.extend([(constant_value, y) for y in possible_values[1:]])
        tupled_current_combos = [combo for combo in tupled_current_combos if "All" not in combo] # Remove initial All

    return tupled_current_combos

def generate_legend_items(combo_list: list, cytoscape_elements: list):
    from dash import html
    
    legend_items = []
    highlight_styles = []
    total_combos = len(combo_list)
    for i, team_tuple in enumerate(combo_list):
        color = generate_color(i, total_combos)
        highlighted_edges = set()
        highlighted_nodes = set()
        team, year = team_tuple
        
        # Find connected nodes
        for el in cytoscape_elements:
            data = el.get('data', {})
            # Search through edges
            if data.get('team_of_connection') == team and (year in data.get('years_of_connection')):
                highlighted_edges.add(data.get('id'))
                highlighted_nodes.add(data.get('source'))
                highlighted_nodes.add(data.get('target'))
        # Highlight edges
        for edge_id in highlighted_edges:
            highlight_styles.append({
            'selector': f'[id = "{edge_id}"]',
            'style': {'line-color': color, 'opacity': 1},
        })
        # Highlight nodes
        for coach_name in highlighted_nodes:
            highlight_styles.append({
                'selector': f'node[id = "{coach_name}"]',
                'style': {f'background-color': color, 'border-width': 1, 'border-color': 'black', 'opacity': 1}
            })

        legend_items.append(
            html.Div([
                html.Span(style={
                    'display': 'inline-block',
                    'width': '20px',
                    'height': '20px',
                    'backgroundColor': color,
                    'marginRight': '10px',
                    'border': '1px solid #333'
                }),
                f"{team} - {year}"
            ], style={'marginBottom': '5px'})
        )

default_stylesheet=[
    {'selector': 'node', 'style': {
        'label': 'data(coach_name)',
        'height': 10,
        'width': 10,
        'font-size': 5,
        'opacity': 1
        }},

    {'selector': 'edge', 'style': {
        'line-color': '#aaa',
        'curve-style': 'bezier',
        'width': 1,
        'opacity': .1
    }}
]

subgraph_default_stylesheet=[
    {'selector': 'node', 'style': {
        'label': 'data(subgraph_label)',
        'height': 10,
        'width': 10,
        'font-size': 5,
        'opacity': 1
    }},

    {'selector': 'edge', 'style': {
        'line-color': '#aaa',
        'curve-style': 'bezier',
        'width': 1,
        'opacity': 1
    }}
]