from basic_graph_generation import create_nx_graph
import networkx as nx            
import dash_cytoscape as cyto    
import dash                      
from dash import dcc, html, callback_context
import itertools

import base64
import io
import pandas as pd
from dash.dependencies import Input, Output, State, ALL
import json


cyto.load_extra_layouts

def nx_to_cytoscape(G):
    elements = []
    print(len(G.nodes))
    print(len(G.edges))
    for node in G.nodes:
        elements.append({'data': {'id': str(node), 'label': str(node)}})

    for idx, (source, target, data) in enumerate(G.edges(data=True)):
        # Only include edges where visualization_tracker == 1
        # if data.get('visualization_tracker', 0) == 1:
            edge_data = {
                'id': f'edge-{idx}',
                'description': f'{source} -> {target}',
                'source': str(source),
                'target': str(target),
                **data
            }
            elements.append({'data': edge_data})
    print(elements[2000])


    # Test code
    # After building elements
    node_ids = {el['data']['id'] for el in elements if 'id' in el['data']}
    for el in elements:
        if 'source' in el['data']:
            if el['data']['source'] not in node_ids:
                print(f"Missing node for source: {el['data']['source']}")
        if 'target' in el['data']:
            if el['data']['target'] not in node_ids:
                print(f"Missing node for target: {el['data']['target']}")
    return elements

def generate_color(index, total):
    # Generates a color evenly spaced around the color wheel
    hue = int(360 * index / total)
    return f"hsl({hue}, 70%, 50%)"

default_stylesheet=[
    {'selector': 'node', 'style': {
        'label': 'data(label)',
        'height': 10,
        'width': 10,
        'font-size': 5,
        'opacity': 1
        }},

    {'selector': 'edge', 'style': {
        'line-color': '#aaa',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'width': 1,
        'opacity': .1
    }}
]

app = dash.Dash('Test Run')

app.layout = html.Div([
    dcc.ConfirmDialog(
        id='empty-parameter-warning',
        message="Please select at least one combination of CFB team and year."
    ),
    dcc.ConfirmDialog(
        id='all-all-warning',
        message="We are unable to accommodate an 'All', 'All' parameter selection." \
        "Please select a narrower range of parameters"
    ),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select a CSV File')
        ]),
        style={
            'width': '98%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    html.Button("Load graph from JSON updated 6/26/25", id="JSON-direct-load-button", n_clicks=0),
    cyto.Cytoscape(
        id='main_graph',
        elements=[],  # Start empty
        layout={'name': 'circle'
                },

        stylesheet=[
            {'selector': 'node', 'style': {
                'label': 'data(label)',
                'height': 10,
                'width': 10,
                'font-size': 5,
                'opacity': 1
                }},

            {'selector': 'edge', 'style': {
                'line-color': '#aaa',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'width': 1,
                'opacity': .1
            }}
        ],
        style={'width': '100%', 'height': '600px'}
    ),
    dcc.Dropdown(
        options= [],
        multi= False,
        placeholder= 'Select some teams',
        id='team_select'
    ),
    dcc.Dropdown(
        options= [],
        multi= True,
        placeholder= 'Select some years',
        id='year_select'
    ),
    
    html.Pre(id="team_year_combo_display", style= {
        'border': 'thin lightgrey solid', 
        'overflowX': 'scroll'
    }),

    html.Button("Submit Team & Year Combination", id='team_year_combo_button', n_clicks=0),
    dcc.Store(id='team_year_combo_store', storage_type='session'),
    html.Button("Update Parameters", id='update_button', n_clicks=0),
    html.Button("Clear Parameters", id='clear_params', n_clicks=0),
    html.Div(id='legend-container'),
    html.Div(className='row', children=[
        html.Div([
            dcc.Markdown("""
                **Click Data**
                
                Mouse over values in the graph
            """),
            html.Pre(id='coach-name-click', style= {
                'border': 'thin lightgrey solid',
                'overflowX': 'scroll'
            }),
            html.Div(id='coach-teams-buttons'),
        ], className='three columns')
    ]),
    cyto.Cytoscape(
        id='sub_graph',
        elements=[],  # Start empty
        layout={'name': 'breadthfirst',
                #'sort': 'encoded_position'
                },

        stylesheet=[
            {'selector': 'node', 'style': {
                'label': 'data(label)',
                'height': 10,
                'width': 10,
                'font-size': 5,
                'opacity': 1
                }},

            {'selector': 'edge', 'style': {
                'line-color': '#aaa',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'width': 1,
                'opacity': 1
            }}
        ],
        style={'width': '100%', 'height': '600px'}
    )
])

@app.callback(
    Output('main_graph', 'elements'),
    Output('team_select', 'options'),
    Output('year_select', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    Input('JSON-direct-load-button', 'n_clicks'),
)
def generate_graph(contents, filename, json_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return [], [], []
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'upload-data' and contents is not None:
        # CSV logic
        content_type, content_string = contents.split(',')
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
                return nx_to_cytoscape(G), team_list, years_list
            else:
                return [], [], []
        except Exception as e:
            print(e)
            return [], [], []
    elif trigger_id == 'JSON-direct-load-button':
        # JSON logic
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
        
        # Test code
        # After building elements
        print(elements[2000])
        
        return elements, teams_list, years_list
    else:
        return [], [], []

@app.callback(
    Output('team_year_combo_display', 'children'),
    Output('team_year_combo_store', 'data'),
    Output('main_graph', 'layout'),
    Output('main_graph', 'stylesheet'),
    Output('empty-parameter-warning', 'displayed'),
    Output('legend-container', 'children'),
    Output('all-all-warning', 'displayed'),
    Input('team_year_combo_button', 'n_clicks'),
    Input('update_button', 'n_clicks'),
    Input('clear_params', 'n_clicks'),
    State('team_year_combo_store', 'data'),
    State('team_select', 'value'),
    State('year_select', 'value'),
    State('main_graph', 'elements'),
    State('team_select', 'options'),
    State('year_select', 'options')
)
def update_main_graph(
    combo_n_clicks, update_n_clicks, clear_n_clicks,
    current_selections, team_selection, year_selections,
    elements, team_options, year_options
):
    unselected_stylesheet = [
        {'selector': 'node', 'style': {
            'label': 'data(label)',
            'height': 10,
            'width': 10,
            'font-size': 5,
            'opacity': 0
        }},
        {'selector': 'edge', 'style': {
            'line-color': '#aaa',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'width': 1,
            'opacity': 0
        }}
    ]
    
    ctx = dash.callback_context
    if not ctx.triggered:
        # return all outputs as dash.no_update or empty
        return "", [], dash.no_update, dash.no_update, False, None, False

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle clear
    if trigger_id == "clear_params":
        return "", [], {'name': 'circle'}, default_stylesheet, False, None, False

    # Handle combo button
    if trigger_id == "team_year_combo_button":
        if combo_n_clicks == 0 or team_selection is None or year_selections is None:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, None, False
        if not isinstance(team_selection, list):
            team_selection = [team_selection]
        if not isinstance(year_selections, list):
            year_selections = [year_selections]
        new_team_year_combos = list(itertools.product(team_selection, year_selections))
        if current_selections is None:
            current_selections = []
        # Convert everything to tuples, dcc.storage unpacks tuples when converting to JSON
        current_selections = [tuple(x) for x in current_selections]
        new_team_year_combos = [tuple(x) for x in new_team_year_combos]
        team_year_combos = list(set(current_selections + new_team_year_combos))
        combo_strings = [f"{team} - {year}" for team, year in team_year_combos]
        return ", ".join(combo_strings), team_year_combos, dash.no_update, dash.no_update, False, None, False

    # Handle update button (your update_graph logic here)
    if trigger_id == "update_button":
        highlight_styles = []

        if current_selections == []:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, dash.no_update, False
        
        combinations = current_selections
        for combo in current_selections:
            team, year = combo
            if team == "All" and year == "All":
                return dash.no_update, dash.no_update, False, None, False, dash.no_update, True
            elif team == "All":
                combinations.extend([(t, year) for t in team_options[1:]])
                combinations = [combo for combo in combinations if "All" not in combo]
            elif year == "All":
                combinations.extend([(team, y) for y in year_options[1:]])
                combinations = [combo for combo in combinations if "All" not in combo]

        combinations = [tuple(x) for x in combinations] # Re-tuple again when pulling from storage
        combinations = list(set(combinations))
        total = len(combinations)

        legend_items = []
        for i, team_tuple in enumerate(combinations):
            color = generate_color(i, total)
            highlighted_edges = set()
            highlighted_nodes = set()
            team, year = team_tuple
            
            # Find connected nodes
            for el in elements:
                data = el.get('data', {})
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
            for node_id in highlighted_nodes:
                highlight_styles.append({
                    'selector': f'node[id = "{node_id}"]',
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

        legend = html.Div(legend_items, style={'padding': '10px', 'border': '1px solid #ccc', 'display': 'inline-block'})
        layout = {'name': 'random'}
        
        return dash.no_update, dash.no_update, layout, unselected_stylesheet + highlight_styles, False, legend, False
    
    else:
        return dash.no_update, dash.no_update, False, None, False, dash.no_update, False

@app.callback(
    Output('coach-name-click', 'children'),
    Output('coach-teams-buttons', 'children'),
    Input('main_graph', 'tapNodeData'),
    Input('main_graph', 'elements')
)
def display_click_data(clickData, elements):
    if clickData and 'label' in clickData:
        years_coached = []
        coached_info = []
        for el in elements:
            data = el.get('data', {})
            # Check if the clicked coach is involved in this edge
            if data.get('source', "") == clickData['label'] or data.get('target', "") == clickData['label']:
                # Determine role
                is_source = data.get('source', "") == clickData['label']
                is_target = data.get('target', "") == clickData['label']
                team = data.get('team_of_connection')
                for year in data.get('years_of_connection', []):
                    if year not in years_coached:
                        years_coached.append(year)
                        if is_source:
                            sentence = f"{clickData['label']} coached for {team} as the {data['source_position']} in {year}"
                            coached_info.append((sentence, team, year))
                        if is_target:
                            sentence = f"{clickData['label']} coached for {team} as the {data['target_position']} in {year}"
                            coached_info.append((sentence, team, year))
        coached_info.sort(key=lambda tup: tup[2], reverse=True)

        coached_buttons = [
            html.Button(sentence, 
                        id={'type': 'coach-btn', 'action': 'year-coach-tree', 'coach': clickData['label'], 'team': team, 'year': year}
                        )
                        for sentence, team, year in coached_info
        ]
            
        return f"You clicked {clickData['label']}", coached_buttons
    else:
        return "Click a node", []
    
@app.callback(
    Output('sub_graph', 'elements'),
    Output('sub_graph', 'layout'),
    Input({'type': 'coach-btn', 'action': ALL, 'coach': ALL, 'team': ALL, 'year': ALL}, 'n_clicks'),
    State({'type': 'coach-btn', 'action': ALL, 'coach': ALL, 'team': ALL, 'year': ALL}, 'id'),
    State('main_graph', 'elements')
)
def handle_coach_button_click(n_clicks_list, ids, main_graph_elements):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    for n_clicks, btn_id in zip(n_clicks_list, ids):
        if n_clicks:
            print("Message Heard!")
            year = btn_id['year']
            team = btn_id['team']
            coach = btn_id['coach']
            valid_edges = []
            valid_nodes = []
            
            # First need to collect all encoded positions (solves issue of staff not having all levels listed)
            encoded_pos_on_staff = set()
            for el in main_graph_elements:
                data = el.get('data', {})
                if data.get('team_of_connection') == team and (year in data.get('years_of_connection')):
                    encoded_pos1, encoded_pos2 = data.get('encoded_connection')
                    encoded_pos_on_staff.add(encoded_pos1)
                    encoded_pos_on_staff.add(encoded_pos2)
            
            encoded_pos_on_staff = sorted(list(encoded_pos_on_staff))
            print(encoded_pos_on_staff)

            for el in main_graph_elements:
                data = el.get('data', {})
                if data.get('team_of_connection') == team and (year in data.get('years_of_connection')):
                    source_encoded_pos, target_encoded_pos = data.get('encoded_connection')
                    print(f"Source enc: {source_encoded_pos}")
                    print(f"Target enc: {target_encoded_pos}")
                    if source_encoded_pos == 1:
                        head_coach = data.get('source')
                    if target_encoded_pos == 1:
                        head_coach = data.get('target')
                    if (encoded_pos_on_staff.index(target_encoded_pos) - 1 == encoded_pos_on_staff.index(source_encoded_pos) or 
                        encoded_pos_on_staff.index(target_encoded_pos) + 1 == encoded_pos_on_staff.index(source_encoded_pos)):
                        valid_edges.append(el)
                        print('Found valid edge')
            
            processed_coaches = []
            for edge in valid_edges:
                edge_data = edge.get('data', {})
                source_name = edge_data.get('source')
                target_name = edge_data.get('target')
                for el in main_graph_elements:
                    el_data = el.get('data', {})
                    # For source node
                    if el_data.get('label') == source_name and el_data.get('label') not in processed_coaches:
                        # If you want to add extra information here, use shallow copies to modify node info without
                        # hurting main graph
                        processed_coaches.append(el_data.get('label'))
                        valid_nodes.append(el)
                        
                    # For target node
                    if el_data.get('label') == target_name and el_data.get('label') not in processed_coaches:
                        processed_coaches.append(el_data.get('label'))
                        valid_nodes.append(el)
            sub_graph_elements = valid_nodes + valid_edges             

            layout = {
                'name': 'breadthfirst',
                'roots': f'[id = "{head_coach}"]'
            }
        
            
            return sub_graph_elements, layout
    return dash.no_update

if __name__ == '__main__':
    app.run(debug=True)