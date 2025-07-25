# Dash graph generation imports 
from dash_graph_internals import *          
import dash_cytoscape as cyto    
import dash                      
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import itertools
import json


app = dash.Dash('Coaching Connections Exploration Dashboard', external_stylesheets=[dbc.themes.JOURNAL])

app.layout = html.Div([
    
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
            'margin': '20px'
        },
        multiple=False
    ),
    dbc.Row([ 
        dbc.Col(dbc.Button("Load graph from JSON File", id="JSON-direct-load-button", n_clicks=0, color="info"), 
                width={'size': 'auto'}
            ),
        dbc.Col(
            dbc.Switch(
                id="full_graph_toggle",
                label="Load full initial network? (Recommended off for slower machines)",
                value=False,
            ), width={'size': 'auto'}
        ),    
    ], justify='center'
    ),

    dbc.Row([ 
        dbc.Col(html.H2("Coaching Connections Network", style= {
                'padding-inline': '20px'})
        )
    ]),

    dbc.Alert(
        "Please select at least one combination of CFB team and year.",
        id='empty-parameter-warning',
        is_open=False,
        dismissable=True    
    ),
    dbc.Alert(
        "We are unable to accommodate an 'All', 'All' parameter selection." \
        "Please select a narrower range of parameters",
        id='all-all-warning',
        is_open=False,
        dismissable=True    
    ),

    dbc.Row([
        dbc.Col(
            html.Div(
                cyto.Cytoscape(
                    id='main_graph',
                    elements=[],  # Start empty
                    layout={'name': 'circle'
                            },

                    stylesheet= default_stylesheet,
                    style={'width': '100%', 'height': '600px'}
                ), style={'padding':'20px'}
            ),
        ),
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Dropdown(
                options= [],
                multi= False,
                placeholder= 'Select a team to analyze',
                id='team_select'
            ), 
            width={'size': 4, 'offset': 1}
        ),
        dbc.Col(dcc.Dropdown(
                options= [],
                multi= True,
                placeholder= 'Select years to analyze for that team',
                id='year_select'
            ),
            width={'size': 4, 'offset': 2}
        )
    ],
    ),
    
    dbc.Row([dbc.Col(html.H6(""))]), # Helps spacing, gutters are another option

    dbc.Row([ dbc.Col(html.H5('Selected Team - Year Combinations:'), 
                width={'size': 'auto', 'offset': 1})
    ],
    ),

    dbc.Row([
        dbc.Col(html.Pre(
            id="team_year_combo_display", style= {
            'border': 'thin lightgrey solid', 
            'overflowX': 'auto',
            'whiteSpace': 'pre-wrap'
            }),
            width={'size': 10, 'offset': 1}
        )
    ],
    ),

    dbc.Row([
        dbc.Col(dbc.Button("Submit Team & Year Combination", id='team_year_combo_button', n_clicks=0, color="primary"),
                width={'size': 4, 'offset': 0}
        ),
        dbc.Col(dbc.Button("Update Parameters", id='update_button', n_clicks=0, color="primary"),
                width={'size': 3, 'offset': 0}
        ),
        dbc.Col(dbc.Button("Clear Parameters", id='clear_params', n_clicks=0),
                width={'size': 2, 'offset': 0}
        ),
    ], justify='center'
    ),
    dcc.Store(id='team_year_combo_store', storage_type='session'),
    
    dbc.Row([
        dbc.Col(
            html.P("Due to an unresolved Dash issue, please press 'Update Parameters' a second time after the first update \
            to fully update the graph", style={'fontStyle': 'italic'}),
            width={'size': 'auto', 'offset': 0}
        )
    ], justify='center'
    ),

    dbc.Row([dbc.Col(html.Div(id='legend-container'), width={'size': 'auto'}), 
        ], justify='center'
    ),

    dbc.Row([
        dbc.Col(html.H5('Coaching History'), width={'size': 'auto', 'offset': 1}),
    ],),
    
    dbc.Row([
        dbc.Col(html.P("Click on a coach's node to view their full coaching history"), 
                width={'size': 'auto', 'offset': 1}),
    ],),

    dbc.Row([
        dbc.Col(html.H6(id='coach-name-click', style= {
                'border': 'thin lightgrey solid',
                'whiteSpace': 'normal',
                'padding': '10px'
            }), width={'size': 'auto', 'offset': 1}),
    ],),

    dbc.Row([
        dbc.Col(html.Div(id='coach-teams-buttons', style={
            'columnCount': 2,
            'columnGap': '10px',
            'justifyContent': 'center'
        }),
                width={'size': 12}),
    ], justify='center'
    ),

    dbc.Row([ 
            dbc.Col(html.H3(id='staff-header', style={
                    'padding-inline': '20px'})
            )
        ]),

    cyto.Cytoscape(
        id='sub_graph',
        elements=[],  # Start empty
        layout={'name': 'breadthfirst',
                },

        stylesheet= subgraph_default_stylesheet,
        style={'width': '100%', 'height': '600px'}
    )
])

@app.callback(
    Output('main_graph', 'elements'),
    Output('team_select', 'options'),
    Output('year_select', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('full_graph_toggle', 'value'),
    Input('JSON-direct-load-button', 'n_clicks'),
)
def generate_graph(contents, filename, full_graph_toggle, _json_clicks):
    """
    Generates graph from either an uploaded CSV file or from a local JSON file, 
    depending on user action. May or not load initial network visualization based on user toggle.

    Args:
        contents (file contents): Data uploaded to the html.A 'Select a CSV File', will be decoded
        filename (str): File name of file uploaded to the html.A
        _json_clicks (int): Part of how Dash tracks when buttons have been clicked, unused but needed

    Returns:
        elements (list): List of JSON objects representing nodes and edges, 
        given and read to create the main cytoscape graph
        teams_list (list): List of all unique teams found, given to the team selection dropdown
        years_list (list): List of all unique years found, given to the year selection dropdown
    """
    ctx = callback_context
    if not ctx.triggered:
        return [], [], []
    trigger_id = get_id_of_triggered(ctx)

    if trigger_id == 'upload-data' and contents is not None:
        # CSV logic
        elements, teams_list, years_list = parse_csv_file(contents, filename)
        if full_graph_toggle == False:
            return [], teams_list, years_list
        
        return elements, teams_list, years_list
    
    elif trigger_id == 'JSON-direct-load-button':
        # JSON logic
        elements, teams_list, years_list = parse_json_file()
        if full_graph_toggle == False:
            return [], teams_list, years_list
        
        return elements, teams_list, years_list
    
    else:
        return [], [], []

@app.callback(
    Output('team_year_combo_display', 'children'),
    Output('team_year_combo_store', 'data'),
    Output('main_graph', 'layout'),
    Output('main_graph', 'stylesheet'),
    Output('main_graph', 'elements', allow_duplicate=True),
    Output('empty-parameter-warning', 'is_open'),
    Output('legend-container', 'children'),
    Output('all-all-warning', 'is_open'),
    Input('team_year_combo_button', 'n_clicks'),
    Input('update_button', 'n_clicks'),
    Input('clear_params', 'n_clicks'),
    State('team_year_combo_store', 'data'),
    State('team_select', 'value'),
    State('year_select', 'value'),
    State('main_graph', 'elements'),
    State('team_select', 'options'),
    State('year_select', 'options'),
    State('full_graph_toggle', 'value'),
    prevent_initial_call=True
) # Rework clear params to work with full graph toggle
def update_main_graph(
    combo_n_clicks, _update_n_clicks, _clear_n_clicks,
    current_selected_combos, team_selection, year_selections,
    current_elements, team_options, year_options, full_graph_toggle
):   
    """
    Logic to handle all versions of updating the main graph interface, including adding
    new (team, year) combinations, updating the graph based on selected combinations, and
    clearing all parameters to reset the graph.

    Args:
        combo_n_clicks (int): How many times the 'Add combination' button has been selected. \
            Required for callback_context tracking
        _update_n_clicks (int): How many times the 'Update Parameters' button has been selected. \
            Required for callback_context tracking
        _clear_n_clicks: How many times the 'Clear Parameters' button has been selected. \
            Required for callback_context tracking
        current_selected_combos (list): List of currently selected combinations pulled from \
            'team_year_combo_store'
        team_selection (str): Current team selected in the team select dropdown
        year_selections (list or str): Years currently being selected in the year select dropdown
        elements (list): Elements from the main cytoscape graph (nodes + edges as JSON objects)
        team_options (list): All values from the team selection dropdown. Needed to handle 'All' selection
        year_options (list): All values from the year selection dropdown. Needed to handle 'All' selection

    Returns
        Tuple[str, list, dict, dict, bool, list, bool]: A tuple containing:
            - team_year_combo_display (str): String to be printed in html.Pre object of the same name. Lists all selected combinations
            - team_year_combo_data (list): List of tuples to be stored in 'team_year_combo_store' and later pulled
            - layout: Layout arguments to be passed to the main cytoscape graph
            - stylesheet: Stylesheet arguments to be passed to the main cytoscape graph
            - display_empty_param_warning (bool): Whether the empty parameter warning (dcc.ConfirmDialog) shoud be displayed
            - legend: The color legend to be contained within 'legend-container'
            - all_all_warning_display (bool): Whether the warning (dcc.ConfirmDialog) for selecting 'All' and 'All' should be displayed

    ### Behavior

    Clear Parameter Behavior:
        Clear display and storage data, return to circle layout and default stylesheet, clear legend
    
    Adding Combinations Behavior:
        - If information is incomplete, don't update anything
        - Else, turn selections into lists and iterate to produce combinations
        - Combine new combinations with combinations in data storage
        - Return updated display and data storage, no update to other returns

    Update Button Behavior:
        - Pull stored combinations, retuple for consistency
        - Iterate through combinations
            - Special behavior for 'All' selections, creates additional new combinations
        - Generates selector arguments for the stylesheet and legend with 
        :func:`dash_graph_internals.generate_legend_and_highlights`
    """
    ctx = dash.callback_context
    
    full_elements_list, _, _ = parse_json_file()
    
    if not ctx.triggered:
        # return all outputs as dash.no_update or empty
        team_year_combo_display = ""
        team_year_combo_data = []
        layout = dash.no_update
        stylesheet = dash.no_update
        new_elements = current_elements
        display_empty_param_warning = False
        legend = None
        all_all_warning_display = False
        
        return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
            new_elements, display_empty_param_warning, legend, all_all_warning_display

    trigger_id = get_id_of_triggered(ctx)

    # Handle clear
    if trigger_id == "clear_params":
        if full_graph_toggle == False:
            team_year_combo_display = ""
            team_year_combo_data = []
            layout = {'name': 'circle'}
            stylesheet = default_stylesheet
            new_elements = []
            display_empty_param_warning = False
            legend = None
            all_all_warning_display = False

            return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
            new_elements, display_empty_param_warning, legend, all_all_warning_display

        team_year_combo_display = ""
        team_year_combo_data = []
        layout = {'name': 'circle'}
        stylesheet = default_stylesheet
        new_elements = full_elements_list
        display_empty_param_warning = False
        legend = None
        all_all_warning_display = False
        
        return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
            new_elements, display_empty_param_warning, legend, all_all_warning_display

    # Handle triggering 'adding combinations' button
    if trigger_id == "team_year_combo_button":
        # If information is incomplete
        if combo_n_clicks == 0 or team_selection is None or year_selections is None:
            team_year_combo_display = dash.no_update
            team_year_combo_data = dash.no_update
            layout = dash.no_update
            stylesheet = dash.no_update
            new_elements = current_elements
            display_empty_param_warning = False
            legend = None
            all_all_warning_display = False
            
            return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
            new_elements, display_empty_param_warning, legend, all_all_warning_display
        
        # Turn single values into lists for consistent iteration
        if not isinstance(team_selection, list):
            team_selection = [team_selection] 
        if not isinstance(year_selections, list):
            year_selections = [year_selections]
        new_team_year_combos = list(itertools.product(team_selection, year_selections))
        
        if current_selected_combos is None:
            current_selected_combos = []
        # Convert everything to tuples for consistency
        # dcc.storage unpacks tuples when converting to JSON
        current_selected_combos = [tuple(x) for x in current_selected_combos]
        new_team_year_combos = [tuple(x) for x in new_team_year_combos]
        team_year_combos = list(set(current_selected_combos + new_team_year_combos))
        combo_strings = [f"{team} - {year}" for team, year in team_year_combos]
        
        team_year_combo_display = ", ".join(combo_strings)
        team_year_combo_data = team_year_combos
        layout = dash.no_update
        stylesheet = dash.no_update
        new_elements = current_elements
        display_empty_param_warning = False
        legend = None
        all_all_warning_display = False
        return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
            new_elements, display_empty_param_warning, legend, all_all_warning_display

    # Handle update button
    if trigger_id == "update_button":

        if current_selected_combos == []:
            team_year_combo_display = dash.no_update
            team_year_combo_data = dash.no_update
            layout = dash.no_update
            stylesheet = dash.no_update
            new_elements = current_elements
            display_empty_param_warning = True
            legend = dash.no_update
            all_all_warning_display = False

            return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
                new_elements, display_empty_param_warning, legend, all_all_warning_display
        
        # Re-tuple again when pulling from storage for consistency
        tupled_current_combos = [tuple(x) for x in current_selected_combos] 

        for combo in tupled_current_combos:
            team, year = combo
            if team == "All" and year == "All":
                team_year_combo_display = dash.no_update
                team_year_combo_data = dash.no_update
                layout = dash.no_update
                stylesheet = dash.no_update
                new_elements = current_elements
                display_empty_param_warning = False
                legend = dash.no_update
                all_all_warning_display = True
                
                return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
                    display_empty_param_warning, legend, all_all_warning_display
            
            elif team == "All":
                tupled_current_combos = handle_all_selection(tupled_current_combos, team_options, year, team_or_year="team")
            
            elif year == "All":
                tupled_current_combos = handle_all_selection(tupled_current_combos, year_options, team, team_or_year="year")

        final_combo_list = list(set(tupled_current_combos))

        new_elements, highlight_styles, legend_items = generate_legend_and_highlights(final_combo_list, full_elements_list)

        team_year_combo_display = dash.no_update
        team_year_combo_data = dash.no_update
        layout = {'name': 'circle', 
                  'animate': True}
        stylesheet = unselected_stylesheet + highlight_styles
        new_elements = new_elements
        display_empty_param_warning = False
        legend = html.Div(legend_items, 
                          style={'padding': '10px', 'border': '1px solid #ccc', 'display': 'inline-block'})
        all_all_warning_display = False
        
        import uuid


        return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
                new_elements, display_empty_param_warning, legend, all_all_warning_display
    
    else:
        team_year_combo_display = dash.no_update
        team_year_combo_data = dash.no_update
        layout = dash.no_update
        stylesheet = dash.no_update
        new_elements = current_elements
        display_empty_param_warning = False
        legend = dash.no_update
        all_all_warning_display = False
        
        return team_year_combo_display, team_year_combo_data, layout, stylesheet, \
        new_elements, display_empty_param_warning, legend, all_all_warning_display

@app.callback(
    Output('coach-name-click', 'children'),
    Output('coach-teams-buttons', 'children'),
    Input('main_graph', 'tapNodeData'),
    prevent_initial_call=True
)
def display_click_data(clickData):
    """
    Reads when a user clicks a node, displays who they clicked and buttons for each year the coach was employed

    Args:
        clickData (dict): Dash sends the data of the clicked node this way
        full_elements_list (list): List of all elements in the main cytoscape
    
    Returns
        - Sentence of which coach was clicked to be displayed
        - Buttons for each year in the coaches employment history, generated by \
            :func:`dash_graph_internals.gather_coaching_positions`

    Behavior:
        - Reads clicked coach's name
        - Gathers their employment history with :func:`dash_graph_internals.gather_coaching_positions`
        - Uses the employment history to generate buttons for each year
    """
    full_elements_list, _, _ = parse_json_file()
    
    if clickData and 'id' in clickData: # id check ensures user clicked a node, not an edge
        clicked_coach = clickData['coach_name']
        coach_employment_history = gather_coaching_positions(full_elements_list, clicked_coach)

        coached_buttons = [
            dbc.Button(sentence, 
                        id={'type': 'coach-btn', 'action': 'year-coach-tree', 'coach': clicked_coach, 'team': team, 'year': year},
                        color='info',
                        style={
                            'marginBottom': '10px',
                            'display': 'block',      
                            'marginLeft': 'auto',  
                            'marginRight': 'auto',
                        }
                    )
                        for sentence, team, year in coach_employment_history
        ]
            
        return f"You clicked {clicked_coach}", coached_buttons
    
    else:
        return "Click a node", []
    
@app.callback(
    Output('sub_graph', 'elements'),
    Output('sub_graph', 'layout'),
    Output('sub_graph', 'stylesheet'),
    Output('staff-header', 'children'),
    Input({'type': 'coach-btn', 'action': ALL, 'coach': ALL, 'team': ALL, 'year': ALL}, 'n_clicks'),
    State({'type': 'coach-btn', 'action': ALL, 'coach': ALL, 'team': ALL, 'year': ALL}, 'id'),
    prevent_initial_call=True
)
def handle_coach_button_click(n_clicks_list, ids): # Error, not updating on second click
    """
    Triggers when one of the buttons created by :func:`display_click_data` is clicked, \
    loads subgraph that visualized the coaching staff hierarchy for that team that season

    Args:
        n_clicks_list (list): List Dash uses to track the clicks on all created \
            buttons of class `coach-btn`
        ids (list): The ids of all the coach buttons
        full_elements_list (list): List of all elements from the main cytoscape graph

    Returns
        - subgraph_elements (list): List of edges and nodes that make up subgraph, created by \
        :func:`dash_graph_internals.created_bfs_graph_structure`
        - subgraph_layout (dict): Arguments to add to the basic layout, defines the root as the analyzed \
        staff's head coach
        - subgraph_stylesheet (dict): Default stylesheet for subgraphs defined in `dash_graph_internals` \
        plus an additional argument to highlight the coach the user initially selected for readability

    Behavior:
        - When a button is clicked, Dash sends an update to n_clicks_list
        - This is tracked and paired to the relevant id, which allows the code to pull needed information
        - The unique encoded positions on the staff are found with \
            :func:`dash_graph_internals.find_endcoded_levels_on_staff` (see definition for why this is needed)
        - This list is passed to :func:`create_bfs_graph_structure` to generate the subgraph elements \
            and identify the head coach
        - The relevant subgraph_layout and subgraph_stylesheets are created based on the head coach and \
            clicked coach data
    """
    full_elements_list, _, _ = parse_json_file()
    
    ctx = dash.callback_context
    if not ctx.triggered or all((n is None or n == 0) for n in n_clicks_list):
        subgraph_elements = dash.no_update
        subgraph_layout = dash.no_update
        subgraph_stylesheet = dash.no_update

        return subgraph_elements, subgraph_layout, subgraph_stylesheet, ""

    triggered_prop_id = get_id_of_triggered(ctx)
    try:
        triggered_id_json = json.loads(triggered_prop_id)
    except Exception:
        return dash.no_update, dash.no_update, dash.no_update, ""


    for btn_id in ids:
        if btn_id == triggered_id_json:
            year = btn_id['year']
            team = btn_id['team']
            coach = btn_id['coach']

            # First need to collect all encoded positions (solves issue of staff not having all levels listed)
            encoded_pos_on_staff = find_encoded_levels_on_staff(full_elements_list, team, year)

            subgraph_elements, graph_roots = create_bfs_graph_structure(full_elements_list, encoded_pos_on_staff, team, year)         

            subgraph_layout = {
                'name': 'breadthfirst',
                'roots': ", ".join(f'[id = "{coach_name}"]' for coach_name in graph_roots)
            }
        
            hightlight_clicked_coach = [{
                'selector': f'node[id = "{coach}"]',
                    'style': {f'background-color': '#336699', 'border-width': 1, 'border-color': 'black', 'opacity': 1}
            }]
            
            subgraph_stylesheet = subgraph_default_stylesheet + hightlight_clicked_coach
            staff_header = f"Staff Hierarchy for {team} in {year}"

            return subgraph_elements, subgraph_layout, subgraph_stylesheet, staff_header
    return dash.no_update, dash.no_update, dash.no_update, ""

if __name__ == '__main__':
    app.run()