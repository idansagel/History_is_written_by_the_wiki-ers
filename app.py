import dash
from dash.dependencies import Input, Output, State
import pandas as pd
import ast
import numpy as np
import plotly.express as px
import communities
from data_processing import load_and_process_data, get_unique_occupations
from layout import create_app_layout, map_to_year

# Initialize the Dash app
app = dash.Dash(__name__)

# Load and process data
df, min_year, max_year = load_and_process_data()
unique_occupations = get_unique_occupations(df)

# Create the app layout
app.layout = create_app_layout(unique_occupations, min_year, max_year)

# Initialize the FigureGroupFinder
figure_finder = communities.FigureGroupFinder(None)

@app.callback(
    [Output('world-map', 'figure'),
     Output('year-display', 'children')],
    [Input('year-slider', 'value'),
     Input('occupation-dropdown', 'value'),
     Input('filtered-links', 'children'),
     Input('group-dropdown', 'value'),
     Input('world-map', 'clickData')],
    [State('world-map', 'relayoutData')]
)
def update_map(slider_value, selected_occupation, filtered_links, group_option, click_data, relayoutData):
    selected_year = map_to_year(slider_value, min_year, max_year)
    # Filter the dataframe for the selected year
    df_filtered = df[(df['birth'] <= selected_year) & ((df['death'] >= selected_year) | df['death'].isna())]

    # Apply occupation filter if one is selected
    if selected_occupation != "All":
        df_filtered = df_filtered[df_filtered['occupation'].apply(lambda x: selected_occupation in x)]

    if filtered_links and filtered_links is not None:
        page_id_to = ast.literal_eval(filtered_links)
        df_filtered = df_filtered[df_filtered['page_id'].isin(page_id_to)]

    # Create the map
    fig = px.scatter_mapbox(df_filtered,
                            lat='latitude',
                            lon='longitude',
                            hover_name='article_name',
                            hover_data={
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
                      "Birth: %{customdata[0]}<br>" +
                      "Death: %{customdata[1]}" +
                      "<extra></extra>"
    )

    # Replace NaN death years with empty string
    df_filtered['death'] = df_filtered['death'].fillna('')
    fig.update_traces(
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
        title=f"Historical Figures Active in {selected_year} - {group_option.capitalize()} Group",
        margin={"r":0,"t":40,"l":0,"b":0}
    )

    return fig, f"Year: {selected_year}"

@app.callback(
    [Output('wikipedia-link', 'href'),
     Output('wikipedia-link', 'children'),
     Output('description-display', 'children'),
     Output('wikipedia-link', 'style'),
     Output('filtered-links', 'children')],
    [Input('world-map', 'clickData'),
     Input('map-container', 'n_clicks'),
     Input('group-dropdown', 'value')],
    [State('world-map', 'clickData')]
)
def update_click_data(click_data, n_clicks, group_option, current_click_data):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'map-container':
        return "", "Click on a dot to open the Wikipedia page", "", {"display": "none"}, None

    if click_data is None:
        return "", "Click on a dot to open the Wikipedia page", "", {"display": "none"}, None

    article_name = click_data['points'][0]['hovertext']
    row_idx = df['article_name'] == article_name
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

    return (wiki_link, 
            article_name, 
            description, 
            {
                "display": "block",
                "color": "#ffffff",
                "fontSize": "22px",
                "fontWeight": "bold",
                "textDecoration": "none",
                "background": "linear-gradient(45deg, #ff5722, #ff9800)",
                "padding": "15px",
                "borderRadius": "10px",
                "border": "2px solid #ff5722",
                "marginTop": "15px",
                "boxShadow": "0 4px 8px rgba(0,0,0,0.3)",
                "transition": "background 0.3s, transform 0.3s",
            },
            str(related_ids))

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)