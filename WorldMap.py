import math

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np  # Import numpy for infinity values
import plotly.express as px
import datetime

# Load the data
df = pd.read_csv('top_10000_people_articles.csv')

# Filter out rows where birth or death is NaN
df = df.dropna(subset=['birth'])

# Normalize the row index for the color of the dots on the map:
df['color_value'] = 1.0 - (df.index - df.index.min()) / (df.index.max() - df.index.min())

# Initialize the Dash app
app = dash.Dash(__name__)

# Calculate the year range for the timeline, excluding NaN values and converting to int
min_year = np.int16(df['birth'].min())
max_year = datetime.datetime.now().year

# Create the app layout
app.layout = html.Div([
    html.H1("Historical Figures World Map and Timeline"),
    dcc.Graph(id='world-map'),
    dcc.Slider(
        id='year-slider',
        min=min_year,
        max=max_year,
        value=max_year,
        marks={str(year): str(year) for year in range(min_year, max_year + 1, 100)},
        step=10
    ),
    html.Div(id='year-display'),
    # html.A(id='wikipedia-link', children="Click on a dot to open the Wikipedia page", href="", target="_blank", style={"display": "none"})  # Hidden by default
    html.A(
        id='wikipedia-link',
        children="Click on a dot to open the Wikipedia page",
        href="",
        target="_blank",
        style={
            "color": "#ffffff",  # Link text color
            "fontSize": "22px",  # Increased font size
            "fontWeight": "bold",  # Bold text
            "textDecoration": "none",  # No underline
            "background": "linear-gradient(45deg, #ff5722, #ff9800)",  # Gradient background
            "padding": "15px",  # More padding
            "borderRadius": "10px",  # More rounded corners
            "border": "2px solid #ff5722",  # Thicker border
            "marginTop": "15px",  # More margin on top
            "boxShadow": "0 4px 8px rgba(0,0,0,0.3)",  # Shadow effect
        }
    )
])

# Callback to update the map and year display

@app.callback(
    [Output('world-map', 'figure'),
    Output('year-display', 'children')],
    [Input('year-slider', 'value')]
)
def update_map(selected_year):
    # Filter the dataframe for the selected year
    df_filtered = df[(df['birth'] <= selected_year) & ((df['death'] >= selected_year) | df['death'].isna())]

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
                                [0.0, "#87CEEB"],  # Light Sky Blue for low values
                                [0.5, "#FFD700"],  # Gold for mid values
                                [1.0, "#FF0000"]   # Red for high values
                            ],
                            center={"lat": 30, "lon": 15},
                            zoom=1.5,
                            height=600)

    fig.update_layout(
        mapbox_style="open-street-map",
        title=f"Historical Figures Active in {selected_year}",
        margin={"r":0,"t":40,"l":0,"b":0}
    )

    return fig, f"Year: {selected_year}"


@app.callback(
    [Output('wikipedia-link', 'href'),
    Output('wikipedia-link', 'children'),
    Output('wikipedia-link', 'style')],
    [Input('world-map', 'clickData')]
)

def display_click_data(clickData):
    if clickData:
        row_idx = df['article_name'] == clickData['points'][0]['hovertext']
        wiki_link = df[row_idx]['wikipedia link'].values[0]
        return wiki_link, clickData['points'][0]['hovertext'], {
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
        }  # Show the link
    return "", "", {"display": "none"}  # Hide the link when no point is clicked

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
