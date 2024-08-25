import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Load the data
df = pd.read_csv('top_10000_people_articles.csv')

# Convert birth and death years to integers, handling any non-numeric values
df['birth'] = pd.to_numeric(df['birth'], errors='coerce').fillna(0).astype(int)
df['death'] = pd.to_numeric(df['death'], errors='coerce').fillna(2023).astype(int)

# Initialize the Dash app
app = dash.Dash(__name__)

# Create dictionaries for country coordinates (you'll need to expand this)
country_coords = {
    'United States': (37.0902, -95.7129),
    'united kingdom': (55.3781, -3.4360),
    # Add more country coordinates as needed
}

# Apply country coordinates
df['lat'] = df['country'].map(lambda x: country_coords.get(x, (0, 0))[0])
df['lon'] = df['country'].map(lambda x: country_coords.get(x, (0, 0))[1])

# Calculate the year range for the timeline
min_year = df['birth'].min()
max_year = df['death'].max()

# Create the app layout
app.layout = html.Div([
    html.H1("Historical Figures World Map and Timeline"),
    dcc.Graph(id='world-map'),
    dcc.Slider(
        id='year-slider',
        min=min_year,
        max=max_year,
        value=min_year,
        marks={str(year): str(year) for year in range(min_year, max_year + 1, 100)},
        step=1
    ),
    html.Div(id='year-display'),
    # html.A(id='wikipedia-link', children="Click on a dot to open the Wikipedia page", href="", target="_blank", style={"display": "none"})  # Hidden by default
    html.A(
        id='wikipedia-link',
        children="Click on a dot to open the Wikipedia page",
        href="",
        target="_blank",
        style={
            "display": "none",
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
            "transition": "background 0.3s, transform 0.3s",  # Smooth transition for hover effects
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
    df_filtered = df[(df['birth'] <= selected_year) & (df['death'] >= selected_year)]

    # Create the map
    fig = px.scatter_geo(df_filtered,
                         lat='lat',
                         lon='lon',
                         hover_name='article_name',
                         hover_data=['country', 'birth', 'death'],
                         projection='natural earth')

    fig.update_layout(title=f"Historical Figures Active in {selected_year}")
    fig.update_geos(showcountries=True, countrycolor="Gray", showcoastlines=True, coastlinecolor="Gray")

    return fig, f"Selected Year: {selected_year}"

# Callback to handle click events on the map
# @app.callback(
#     Output('wikipedia-link', 'href'),
#     Output('wikipedia-link', 'style'),
#     [Input('world-map', 'clickData')]
# )

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
