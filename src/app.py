import dash
from dash import dcc, html, Input, Output, State, callback, no_update, ALL
from dash.exceptions import PreventUpdate
import ast
import plotly.express as px
import numpy as np
import communities
from data_processing import load_and_process_data, get_unique_occupations
from layout import create_app_layout, map_to_year
import warnings

warnings.filterwarnings('ignore')

# Initialize the Dash app
app = dash.Dash(__name__)

# Load and process data
df, min_year, max_year = load_and_process_data()
unique_occupations = get_unique_occupations(df)

# Create the app layout
app.layout = create_app_layout(unique_occupations, min_year, max_year)

# Initialize the FigureGroupFinder
figure_finder = communities.FigureGroupFinder(None)

# Random number generator with a fixed seed
rng = np.random.default_rng(seed=42)

def get_app_title(selected_occupation, article_name, year):
    selected_occupation = selected_occupation.capitalize()
    if article_name is not None and selected_occupation == "All":
        app_title = f"Figures Related to {article_name} Alive in {year}"
    elif article_name is not None and selected_occupation != "All":
        app_title = f"Figures Related to {article_name} Alive in {year} with the Occupation {selected_occupation}"
    elif article_name is None and selected_occupation != "All":
        app_title = f"Figures Alive in {year} with the Occupation {selected_occupation}"
    else:
        app_title = f"Important Figures Alive in {year}"
    return app_title

@callback(
    [Output('world-map', 'figure'),
     Output('app-title', 'children')],
    [Input('year-slider', 'value'),
     Input('occupation-dropdown', 'value'),
     Input('filtered-links', 'children'),
     Input('group-dropdown', 'value'),
     Input('world-map', 'clickData'),
     Input('wikipedia-link', 'children')],
    [State('world-map', 'relayoutData')]
)
def update_map(slider_value, selected_occupation, filtered_links, group_option, click_data, article_name, relayoutData):
    selected_year = map_to_year(slider_value, min_year, max_year)

    # Filter the dataframe for the selected year
    df_filtered = df[(df['birth'] <= selected_year) & ((df['death'] >= selected_year) | df['death'].isna())]

    # Apply occupation filter if one is selected
    if selected_occupation != "All":
        df_filtered = df_filtered[df_filtered['occupation'].apply(lambda x: selected_occupation in x)]

    if filtered_links and filtered_links is not None:
        page_id_to = ast.literal_eval(filtered_links)
        df_filtered = df_filtered[df_filtered['page_id'].isin(page_id_to)]

    # Add tiny random noise to latitude and longitude
    if 'noise_lat' not in df_filtered.columns:
        noise_scale = 0.0001
        df_filtered['noise_lat'] = rng.normal(0, noise_scale, size=len(df_filtered))
        df_filtered['noise_lon'] = rng.normal(0, noise_scale, size=len(df_filtered))

    df_filtered['latitude_jittered'] = df_filtered['latitude'] + df_filtered['noise_lat']
    df_filtered['longitude_jittered'] = df_filtered['longitude'] + df_filtered['noise_lon']

    # Create the map
    fig = px.scatter_mapbox(df_filtered,
                            lat='latitude_jittered',
                            lon='longitude_jittered',
                            hover_name='article_name',
                            hover_data={
                                'latitude_jittered': False,
                                'longitude_jittered': False,
                                'latitude': False,
                                'longitude': False,
                                'color_value': False,
                                'birth': True,
                                'death': True
                            },
                            color='color_value',
                            color_continuous_scale=[
                                [0.0, "#6495ED"],
                                [0.5, "#FFD700"],
                                [1.0, "#FF0000"]
                            ],
                            labels={'color_value': 'Historical<br>Significance'},
                            zoom=1.5,
                            height=600)

    # Update hover template to handle missing death years
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br><br>" +
                      "Birth: %{customdata[4]}<br>" +
                      "Death: %{customdata[5]}" +
                      "<extra></extra>"
    )

    # Replace NaN death years with empty string
    df_filtered['death'] = df_filtered['death'].fillna('')
    fig.update_traces(
        customdata=df_filtered[['noise_lat', 'noise_lon', 'latitude', 'longitude', 'birth', 'death']].values
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
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(
            tickmode='array',
            tickvals=[],
            ticktext=[],
            title=dict(
                text='<span style="color: #333; text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;">IMPORTANCE</span>',
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

    app_title = get_app_title(selected_occupation, article_name, selected_year)

    return fig, app_title

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
        return None, None, "", None, None

    article_name = click_data['points'][0]['hovertext']
    
    row_idx = df['article_name'] == article_name
    rank = df.index[row_idx][0] + 1
    
    wiki_link = df.loc[row_idx, 'wikipedia link'].values[0]
    description = df.loc[row_idx, 'description'].values[0]

    main_id = df.loc[row_idx, 'page_id'].values[0]
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
        list_items = [
            html.Li(
                html.A(
                    f"{name}",
                    href=df.loc[df['article_name'] == name, 'wikipedia link'].values[0],
                    target="_blank",
                    style={'color': '#3498db', 'textDecoration': 'none'}
                ),
                style={'marginBottom': '10px', 'marginLeft': '20px'}
            )
            for name in df['article_name']
        ]
        content = html.Ol(list_items, style={'paddingLeft': '40px', 'listStyleType': 'decimal', 'marginRight': '20px'})
        return {'display': 'flex'}, content
    elif button_id == 'close-modal-button':
        return {'display': 'none'}, no_update
    else:
        return no_update, no_update

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
    clicked_name = eval(clicked_id.split('.')[0])['index']
    
    # Get the birth year of the clicked figure
    birth_year = df.loc[df['article_name'] == clicked_name, 'birth'].values[0]
    
    # Convert birth year to slider value
    slider_value = (birth_year - min_year) / (max_year - min_year)
    
    # Create clickData as if the point was clicked on the map
    click_data = {
        'points': [{
            'hovertext': clicked_name,
            'customdata': df.loc[df['article_name'] == clicked_name, ['birth', 'death']].values[0].tolist()
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
    server = app.server
    app.run_server(debug=False)