import dash
from dash import html, Input, Output, State, callback, no_update, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.express as px
import numpy as np
import communities
from data_processing import (
    get_min_year,
    get_max_year,
    get_unique_occupations,
    get_figures_for_year,
    get_figure_data,
    get_all_article_names,
    get_birth_year,
)
from layout import create_app_layout, map_to_year
import warnings
import ast
import os
import time
import pandas as pd

warnings.filterwarnings('ignore')

# Initialize the Dash app with Bootstrap stylesheet
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Fetch data directly from the database
min_year = get_min_year()  # Fetch minimum year from DB
max_year = get_max_year()  # Fetch current year as max year
unique_occupations = get_unique_occupations()  # Fetch unique occupations from DB

# Create the app layout
app.layout = create_app_layout(unique_occupations, min_year, max_year)

# Initialize the FigureGroupFinder
figure_finder = communities.FigureGroupFinder(None)

# Random number generator with a fixed seed
rng = np.random.default_rng(seed=42)

def get_app_title(selected_occupation, article_name, year):
    if article_name is not None and selected_occupation == "All":
        selected_occupation = selected_occupation.capitalize()
        app_title = f"Figures Related to {article_name} Alive in {year}"
    elif article_name is not None and selected_occupation != "All":
        app_title = f"Figures Related to {article_name} Alive in {year} with the Occupation {selected_occupation}"
    elif article_name is None and selected_occupation != "All":
        app_title = f"Figures Alive in {year} with the Occupation {selected_occupation}"
    else:
        app_title = f"Important Figures Alive in {year}"
    return app_title

# Callback to update the map, app title, and loading overlay
@callback(
    [Output('world-map', 'figure'),
     Output('app-title', 'children'),
     Output('loading-overlay', 'style')],
    [Input('year-slider', 'value'),
     Input('occupation-dropdown', 'value'),
     Input('filtered-links', 'children'),
     Input('group-dropdown', 'value'),
     Input('world-map', 'clickData'),
     Input('wikipedia-link', 'children')],
    [State('world-map', 'relayoutData')]
)
def update_map(slider_value, selected_occupation, filtered_links, group_option, click_data, article_name, relayoutData):
    import time
    start_time = time.time()
    
    # Show loading overlay
    loading_style = {
        "position": "absolute",
        "top": 0,
        "left": 0,
        "width": "100%",
        "height": "100%",
        "backgroundColor": "rgba(255, 255, 255, 0.5)",
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "zIndex": 1000,
    }

    selected_year = map_to_year(slider_value, min_year, max_year)

    # Fetch data from the database
    df_filtered = get_figures_for_year(selected_year, selected_occupation, filtered_links)

    # Ensure correct data types
    df_filtered['birth'] = df_filtered['birth'].astype(str)
    df_filtered['death'] = df_filtered['death'].fillna('').astype(str)
    df_filtered['latitude'] = pd.to_numeric(df_filtered['latitude'], errors='coerce')
    df_filtered['longitude'] = pd.to_numeric(df_filtered['longitude'], errors='coerce')
    df_filtered['color_value'] = pd.to_numeric(df_filtered['color_value'], errors='coerce')

    # Create the map
    fig = px.scatter_mapbox(
        df_filtered,
        lat='latitude',
        lon='longitude',
        hover_name='article_name',
        hover_data=None,  # Disable default hover data
        color='color_value',
        color_continuous_scale=[
            [0.0, "#6495ED"],
            [0.5, "#FFD700"],
            [1.0, "#FF0000"]
        ],
        labels={'color_value': 'Historical<br>Significance'},
        zoom=1.5,
    )

    # Update hover template and customdata
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br><br>" +
                      "Birth: %{customdata[0]}<br>" +
                      "Death: %{customdata[1]}" +
                      "<extra></extra>",
        customdata=df_filtered[['birth', 'death']].values
    )

    # Preserve the viewport state
    if relayoutData and 'mapbox.center' in relayoutData:
        center = relayoutData['mapbox.center']
        zoom = relayoutData['mapbox.zoom']
    else:
        center = {"lat": 30, "lon": 15}
        zoom = 1.5

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=center,
            zoom=zoom
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(
            title=dict(
                text='<span style="color: #333;">Importance</span>',
                side='right',
                font=dict(
                    family='Montserrat',
                    size=12,
                )
            ),
            len=0.5,
            yanchor='middle',
            y=0.5,
            xanchor='right',
            x=1.0,
            thickness=15
        )
    )

    # Set the app title
    if article_name == "Select any Dot":
        article_name = None
    app_title = get_app_title(selected_occupation, article_name, selected_year)

    # Hide loading overlay
    loading_style["display"] = "none"

    total_time = time.time() - start_time
    print(f"Total time for update_map callback: {total_time}s")

    return fig, app_title, loading_style

# Callback to update click data and related information
@callback(
    [Output('wikipedia-link', 'href'),
     Output('wikipedia-link', 'children'),
     Output('description-display', 'children'),
     Output('filtered-links', 'children'),
     Output('world-map', 'clickData', allow_duplicate=True)],
    [Input('world-map', 'clickData'),
     Input('map-container', 'n_clicks'),
     Input('group-dropdown', 'value')],
    [State('world-map', 'clickData')],
    prevent_initial_call=True
)
def update_click_data(click_data, n_clicks, group_option, current_click_data):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'map-container' or click_data is None:
        return None, "Select any Dot", "", None, None

    article_name = click_data['points'][0]['hovertext']
    
    # Fetch data about the figure from the database
    figure_data = get_figure_data(article_name)
    if not figure_data:
        raise PreventUpdate

    rank = figure_data['rank']
    wiki_link = figure_data['wikipedia_link']
    description = figure_data['description']
    main_id = figure_data['page_id']

    figure_finder.main_id = main_id

    if group_option == 'neighbors':
        related_ids = figure_finder.get_neighbors()
    elif group_option == 'louvain':
        related_ids = figure_finder.get_cluster_members()
    else:
        related_ids = []

    article_display_text = article_name
    full_display_text = f"{description} (ranked: {rank}{ordinal_suffix(rank)})"
    
    return wiki_link, article_display_text, full_display_text, str(related_ids), None

# Callback to toggle the modal visibility and populate its content
@callback(
    Output('modal', 'style'),
    Output('list-container', 'children'),
    Input('open-modal-button', 'n_clicks'),
    Input('close-modal-button', 'n_clicks'),
    State('modal', 'style'),
    prevent_initial_call=True
)
def toggle_modal(open_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'open-modal-button':
        # Get all article names from the database
        article_names = get_all_article_names()
        list_items = [
            html.Li(
                html.A(
                    f"{name}",
                    target="_blank",
                ),
                style={'marginBottom': '10px', 'marginLeft': '20px'}
            )
            for name in article_names
        ]
        content = html.Ol(list_items, style={'paddingLeft': '40px', 'listStyleType': 'decimal', 'marginRight': '20px'})
        return {'display': 'flex'}, content
    elif button_id == 'close-modal-button':
        return {'display': 'none'}, no_update
    else:
        return no_update, no_update

# Callback to handle clicks on list items within the modal
@callback(
    Output('year-slider', 'value'),
    Output('world-map', 'clickData', allow_duplicate=True),
    Output('modal', 'style', allow_duplicate=True),
    Input({'type': 'list-item', 'index': ALL}, 'n_clicks'),
    State('year-slider', 'min'),
    State('year-slider', 'max'),
    prevent_initial_call=True
)
def handle_list_item_click(n_clicks, slider_min, slider_max):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update
    
    clicked_id = ctx.triggered[0]['prop_id']
    try:
        # Extract the index from the pattern-matched ID
        pattern_id = ast.literal_eval(clicked_id.split('.')[0])
        if pattern_id.get('type') == 'list-item':
            clicked_name = pattern_id.get('index')
        else:
            return no_update, no_update, no_update
    except (ValueError, SyntaxError):
        return no_update, no_update, no_update
    
    # Get the birth year of the clicked figure from the database
    birth_year = get_birth_year(clicked_name)
    if birth_year is None:
        raise PreventUpdate

    # Convert birth year to slider value
    slider_value = (birth_year - min_year) / (max_year - min_year)
    
    # Create clickData as if the point was clicked on the map
    click_data = {
        'points': [{
            'hovertext': clicked_name,
            'customdata': [birth_year, None]  # Assuming death is None for simplicity
        }]
    }
    
    # Close the modal
    modal_style = {'display': 'none'}
    
    return slider_value, click_data, modal_style

def ordinal_suffix(rank):
    if 11 <= rank % 100 <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank % 10, 'th')
    return suffix

# Run the app
if __name__ == '__main__':
    if 'DYNO' in os.environ:
        # Running on Heroku
        port = int(os.environ.get('PORT', 5000))
        app.run_server(host='0.0.0.0', port=port)
    else:
        # Running locally
        app.run_server(debug=True)