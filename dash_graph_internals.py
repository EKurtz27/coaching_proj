if __name__ == '__main__':
    print("Error: you are running a file of function definitions, please run 'dash_graph.py' to generate the webpage")

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
                'id': 'coach_name', (id is a required attribute for nodes and edges)
                'coach_name': 'coach_name'
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

    with open('data/visualization_elements_dump.json') as f:
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

def handle_all_selection(current_combos: list, possible_values: list, constant_value, team_or_year: str) -> list:
    """
    Handles iterating through lists to create all new combinations when user selects 'All'. 
    Removes combinations containing 'All' 
    """
    if team_or_year == 'team':
        current_combos.extend([(t, constant_value) for t in possible_values[1:]])
        current_combos = [combo for combo in current_combos if "All" not in combo] # Remove initial All

    if team_or_year == 'year':
        current_combos.extend([(constant_value, y) for y in possible_values[1:]])
        current_combos = [combo for combo in current_combos if "All" not in combo] # Remove initial All

    return current_combos

def generate_legend_and_highlights(combo_list: list, cytoscape_elements: list):
    """
    Iterates through combinations, finding relevant edges and nodes. Generates a legend for all combinations

    Args:
        combo_list (list): list of all submitted combinations of (team, year) to be analyzed
        cytoscape_elements (list): list of elements from the main cytoscape (all possible data) 
        to be searched through for valid edges and nodes
    
    Returns:
        new_elements_list: list of all of the relevant elements (nodes and edges) found, for cytoscape visualization
        highlight_styles (list): list of additional selector arguments to be passed to the stylesheet.
        This is what allows for nodes and edges to change colors
        legend_items (list): list of html Span objects that display the color legend for the provided combinations

    Behavior:
        - For each combination:
            - Finds relevant nodes and edges from the main elements list, adds them to new element list for visualization
            - Adds these to intermediate lists
            - Adds these intermediate lists as a value to a dict with (team, year) as the key
        - With all relevant information stored in the dict, iterates through the dict values and:
            - Generates a HSL color for the combination using :func:`generate_color`
            - Creates an html Span object to add to the color legend
            - Highlights each node and edge by adding selector arguments to `highlight_styles`, includes the created HSL color
            - Generates a legend item to be displayed that correlated each combination to its color
            - Checks if there are any overlapping edges in the network:
                - If so, logs the overlapping edges in a set (to prevent duplication)
        - Iterates through all the overlapping edge groups and applies the bezier curve style to stop overlapping
        - Adds all legend items to a html Div that controls display and wrapping functions

    """
    from dash import html
    from itertools import chain
    from copy import deepcopy

    all_highlighted_edges = {}
    all_highlighted_nodes = {}
    new_elements_list = []
    new_elements_id_counter = len(cytoscape_elements) + 2
    for team, year in combo_list:
        team_highlighted_edges = set()
        team_highlighted_nodes = set()
        # Find connected nodes
        for el in cytoscape_elements:
            data = el.get('data', {})
            # Search through edges
            if data.get('team_of_connection') == team and (int(year) in data.get('years_of_connection')):
                team_highlighted_nodes.add(data.get('source'))
                team_highlighted_nodes.add(data.get('target'))
                edge_copy = deepcopy(el) # Deepcopy to be able to change id (allow parallel edges to exist for same job over multiple years)
                edge_copy_data = edge_copy.get('data', {})
                edge_copy_data['id'] = f"edge-{new_elements_id_counter}"
                new_elements_id_counter += 1
                team_highlighted_edges.add(( edge_copy_data.get('id'), edge_copy_data.get('source'), edge_copy_data.get('target') ))
                new_elements_list.append(edge_copy)

        if team_highlighted_edges:
            all_highlighted_edges[(team, year)] = team_highlighted_edges
            all_highlighted_nodes[(team, year)] = team_highlighted_nodes

    for coach_name in chain(*all_highlighted_nodes.values()):
        for el in cytoscape_elements:
            data = el.get('data', {})
            if data.get('coach_name') == coach_name:
                node_copy = deepcopy(el)
                new_elements_list.append(node_copy) # Consider adding a class attribute here, then doing color by class (would require a deep copy)

    total_combos = len(all_highlighted_edges.keys())
    indiv_legend_items = []
    highlight_styles = []
    all_parallel_edges = set()

    sorted_combos = sorted(
    all_highlighted_edges.keys(),
    key=lambda combo: int(combo[1]), reverse=True # combo = (team, year)
    )

    for idx, combo in enumerate(sorted_combos): # This logic handles 'All' selections w/o making a color for teams w/o valid edges
        color = generate_color(idx, total_combos)
        team, year = combo
        edge_info_list = all_highlighted_edges[combo]
        

        indiv_legend_items.append(
            html.Div([
                html.Span(style={
                    'display': 'inline-block',
                    'width': '20px',
                    'height': '20px',
                    'backgroundColor': color,
                    'marginRight': '10px',
                    'border': '1px solid #333',
                    'verticalAlign': 'middle'
                }),
                html.Span(f"{team} - {year}", style={'verticalAlign': 'middle'})
            ], style={
                'marginRight': '20px',
                'marginBottom': '10px'})
        )

        # Highlight nodes
        for coach_name in all_highlighted_nodes[combo]:
            highlight_styles.append({
                'selector': f'node[id = "{coach_name}"]',
                'style': {f'background-color': 'white', 'border-width': 1, 'border-color': 'black', 'opacity': 1}
            })
        
        for edge_info in edge_info_list:
            edge_id, source_coach, target_coach = edge_info
            # Highlight edges
            highlight_styles.append({
                'selector': f'[id = "{edge_id}"]',
                'style': {'line-color': color, 'opacity': 1},
            })
            parallel_edges = []
            parallel_edges.append(edge_id)
            # Search all other edges
            for edge_info in chain(*all_highlighted_edges.values()):
                edge_id2, source_coach2, target_coach2 = edge_info
                if edge_id == edge_id2:
                    continue
                elif ((source_coach == source_coach2 and target_coach == target_coach2)
                    or (source_coach == target_coach2 and target_coach == source_coach2)):  # If edges would overlap  
                    parallel_edges.append(edge_id2)
                    parallel_edges.sort()
                    
            parallel_edges = tuple(parallel_edges)
            if len(parallel_edges) >= 2:
                all_parallel_edges.add(parallel_edges)
            
    for grouped_parallel_edges in all_parallel_edges:
        selector = ', '.join(f'[id = "{edge_id}"]' for edge_id in grouped_parallel_edges) # Apply style that stops overlapping
        highlight_styles.append({
            'selector': selector,
            'style': {'curve-style': 'bezier'}
        })

    legend_items = html.Div(indiv_legend_items, style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'alignItems': 'center'
    })
  
    return new_elements_list, highlight_styles, legend_items

def find_encoded_levels_on_staff(main_elements: list, team: str, year: int) -> list:
    """
    Finds all encoded positions on the current staff. Handles the staff not having continous values
    (ex: 1,2,5) by allowing comparison by index location instead of raw value

    Args:
        main_elements (list): elements from the main cytoscape
        team (str): team selected for analysis
        year (int): year selected for analysis

    Returns:
        encoded_pos_list (list): a sorted list of all encoded positions on the staff

    Behavior:
        - Search through main cytoscape elements to find relevant edges
        - Pull out encoded positions from the edge data and add to a set
        - Turn the set into a list and sort it
    """
    encoded_pos_list = set()
    for el in main_elements:
        data = el.get('data', {})
        if data.get('team_of_connection') == team and (year in data.get('years_of_connection')):
            encoded_pos1, encoded_pos2 = data.get('encoded_connection')
            encoded_pos_list.add(encoded_pos1)
            encoded_pos_list.add(encoded_pos2)
    
    encoded_pos_list = sorted(list(encoded_pos_list))
    return encoded_pos_list

def create_bfs_graph_structure(cytoscape_elements: list, encoded_pos_list: list, team: str, year: int) -> list:
    """
    Creates a list of elements that allows the BFS layout style to correctly show a coaching staff 
    hierarchy tree in the subgraph.

    Args:
        cytoscape_elements (list): A list of all elements from the main cytoscape (all possible data)
        encoded_pos_list (list): A list of all available encoded positions on the current staff. \
            For more information see :func:`find_encoded_levels_on_staff`
        team (str): team being analyzed
        year (int): year being analyzed

    Returns
        sub_graph_elements (list): A list of elements that allow the graph to form properly
        most_senior_coaches (str): Namea of the most senior coaches available in teh data set, \
        passed to the layout of the cytoscape to correctly set the BFS root(s)

    Behavior:
        - Iterates through all elements, first checking if the edge data is for the same team and year
            - If so, tries to see if the coach's encoded position is the most senior possible ( min(encoded_pos_list) )
            - If the coaches are an index distance of 1 from each other (ex: 2 and 4 in a list of [1,2,4]),
            adds this edge to valid edges. This is what lets a BFS form the hierarchical structure desired
        - For each valid edge:
            - Iterates through all elements to find nodes that match edge source and target (tracks and skips duplicates)
            - Copies data from main element list
            - Adds new information to the copy, a longer to be displayed in the subgraph
            - Adds this copy to the valid nodes list
        - Combines valid_nodes and valid_edges
    """
    valid_nodes = []
    valid_edges = []
    highest_encoded_pos = min(encoded_pos_list)
    most_senior_coaches = []

    for el in cytoscape_elements:
        data = el.get('data', {})
        if data.get('team_of_connection') == team and (year in data.get('years_of_connection')):
            source_encoded_pos, target_encoded_pos = data.get('encoded_connection')
            if source_encoded_pos == highest_encoded_pos:
                most_senior_coaches.append(data.get('source'))
            if target_encoded_pos == highest_encoded_pos:
                most_senior_coaches.append(data.get('target'))
            if (encoded_pos_list.index(target_encoded_pos) - 1 == encoded_pos_list.index(source_encoded_pos) or 
                encoded_pos_list.index(target_encoded_pos) + 1 == encoded_pos_list.index(source_encoded_pos)):
                valid_edges.append(el)
    
    processed_coaches = []
    for edge in valid_edges:
        edge_data = edge.get('data', {})
        source_name = edge_data.get('source')
        target_name = edge_data.get('target')
        for el in cytoscape_elements:
            el_data = el.get('data', {})
            # For source node
            if el_data.get('coach_name') == source_name and el_data.get('coach_name'): #not in processed_coaches:
                node_copy = el.copy()
                copy_data = node_copy.get('data', {})
                copy_data['subgraph_label'] = f"{copy_data.get('coach_name', "")}: {edge_data.get('source_position')}"
                processed_coaches.append(el_data.get('coach_name'))
                valid_nodes.append(el)
                
            # For target node
            if el_data.get('coach_name') == target_name and el_data.get('coach_name'): #not in processed_coaches:
                node_copy = el.copy()
                copy_data = node_copy.get('data', {})
                copy_data['subgraph_label'] = f"{copy_data.get('coach_name', "")}: {edge_data.get('target_position')}"
                processed_coaches.append(el_data.get('coach_name'))
                valid_nodes.append(el)
    sub_graph_elements = valid_nodes + valid_edges  

    return sub_graph_elements, most_senior_coaches

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

unselected_stylesheet = [
    {'selector': 'node', 'style': {
        'label': 'data(coach_name)',
        'height': 10,
        'width': 10,
        'font-size': 5,
        'opacity': 0
    }},
    {'selector': 'edge', 'style': {
        'line-color': '#aaa',
        'curve-style': 'bezier',
        'width': 1,
        'opacity': 0
    }}
]

subgraph_default_stylesheet=[
    {'selector': 'node', 'style': {
        'label': 'data(subgraph_label)',
        'size': 30,
        'font-size': 15,
        'opacity': 1,
        'background-color': "#eb6864",
        'border-color': 'black'
    }},

    {'selector': 'edge', 'style': {
        'line-color': '#aaa',
        'curve-style': 'bezier',
        'width': 1,
        'opacity': .5
    }}
]