import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Load the data
df = pd.read_csv('top_10000_people_articles.csv')
print(df.head())
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
    html.Div(id='year-display')
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


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

