from dash import dcc, html
import math

def map_to_year(x: float, min_year: int, max_year: int) -> int:
    if not 0 <= x <= 1:
        raise ValueError("x must be between 0 and 1 inclusive")
    
    # Adjust the curve by squaring x to get a compressed lower range and expanded upper range
    scaled_x = math.pow(x, 0.2)
    
    # Map the scaled value to the year range
    return int(min_year + scaled_x * (max_year - min_year))

def create_app_layout(unique_occupations, min_year, max_year):

    return html.Div([
        html.H1("Historical Figures World Map and Timeline"),
        dcc.Dropdown(
            id='occupation-dropdown',
            options=[{'label': occ, 'value': occ} for occ in unique_occupations],
            value="All",
            placeholder="Select an occupation"
        ),
        dcc.Dropdown(
            id='group-dropdown',
            options=[
                {'label': 'Incoming and Outgoing Links', 'value': 'neighbors'},
                {'label': 'Louvain Cluster', 'value': 'louvain'}
            ],
            value='neighbors',
            placeholder="Select a group option"
        ),
        html.Div([
            dcc.Graph(id='world-map', config={'displayModeBar': True, 'scrollZoom': True})
        ], id='map-container', style={'position': 'relative'}),
        dcc.Slider(
            id='year-slider',
            min=0,
            max=1,
            value=1,
            step=0.001,
            marks = {x: str(map_to_year(x, min_year, max_year)) for x in [i / 12 for i in range(12)] + [1]}           
            ),
        html.Div(id='year-display'),
        html.Div(id='filtered-links', style={'display': 'none'}),
        html.A(
            id='wikipedia-link',
            children="Click on a dot to open the Wikipedia page",
            href="",
            target="_blank",
            style={
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
            }
        ),
        html.Div(id='description-display', style={
            "color": "#ffffff",
            "fontSize": "18px",
            "padding": "15px",
            "background": "#333333",
            "borderRadius": "10px",
            "marginTop": "15px",
            "boxShadow": "0 4px 8px rgba(0,0,0,0.3)"
        })
    ])


