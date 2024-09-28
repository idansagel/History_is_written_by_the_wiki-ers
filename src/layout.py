# layout.py

from dash import html, dcc
import dash_bootstrap_components as dbc
import math
import plotly.graph_objects as go

def map_to_year(x: float, min_year: int, max_year: int) -> int:
    if not 0 <= x <= 1:
        raise ValueError("x must be between 0 and 1 inclusive")
    scaled_x = math.pow(x, 0.2)
    return int(float(min_year) + scaled_x * (float(max_year) - float(min_year)))

def create_app_layout(unique_occupations, min_year, max_year):
    common_styles = {
        'fontFamily': '"Montserrat", sans-serif',
        'color': '#333',
    }

    button_style = {
        'padding': '10px 20px',
        'backgroundColor': '#5DADE2',
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'fontSize': '14px',
        'cursor': 'pointer',
        'transition': 'background-color 0.3s',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.2)',
        'width': '100%',
    }

    return dbc.Container([
        # Title Row
        dbc.Row([
            dbc.Col([
                html.H1(
                    f"Important Figures Alive in {max_year}",
                    id="app-title",
                    className="app-title",
                    style={
                        'textAlign': 'center',
                        'fontWeight': 'bold',
                        'textTransform': 'uppercase',
                        'letterSpacing': '2px',
                        'marginBottom': '5px',
                        'marginTop': '15px',
                        **common_styles
                    }
                ),
            ], width=12)
        ]),
        # Dropdowns and Button Row
        dbc.Row([
            dbc.Col([
                html.Label("Occupation:", className="label", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='occupation-dropdown',
                    options=[{'label': occ, 'value': occ} for occ in unique_occupations],
                    value="All",
                    placeholder="Select an occupation",
                    clearable=False,
                    className='dropdown'
                )
            ], xs=4, sm=3, md=3, lg=3),
            dbc.Col([
                html.Label("Related by:", className="label", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='group-dropdown',
                    options=[
                        {'label': 'Share Wikipedia Links', 'value': 'neighbors'},
                        {'label': 'Same Cluster', 'value': 'louvain'}
                    ],
                    value='neighbors',
                    placeholder="Select a group option",
                    clearable=False,
                    className='dropdown'
                )
            ], xs=4, sm=3, md=3, lg=3),
            dbc.Col([
                html.Label("select", className="label", style={'fontWeight': 'bold', 'visibility': 'hidden'}),  # add invisible label to match dropdowns
                html.Button(
                    [
                        html.Span('Ranks List', className='ranks-full'),
                        html.Span('ranks', className='ranks-short')  # Changed to lowercase 'ranks'
                    ],
                    id='open-modal-button',
                    style=button_style
                ),            
            ], xs=4, sm=3, md=3, lg=3),
        ], justify="center", align="center", className="mb-4"),

        # Modal Div
        html.Div(
            id='modal',
            className='modal',
            children=[
                html.Div(
                    className='modal-content',
                    children=[
                        html.H2('List of Figures and Their Ranks', style={'textAlign': 'center'}),
                        html.Div(id='list-container', style={'maxHeight': '400px', 'overflowY': 'scroll'}),
                        html.Button('Close', id='close-modal-button', style={'marginTop': '20px', **button_style}),
                    ],
                )
            ],
            style={'display': 'none'}
        ),

        # Map Row
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        dcc.Graph(
                            id='world-map',
                            figure=go.Figure(
                                layout=dict(
                                    mapbox=dict(
                                        style="open-street-map",
                                        center=dict(lat=30, lon=15),
                                        zoom=1.5
                                    ),
                                    showlegend=False,
                                    hovermode=False,
                                    margin=dict(l=0, r=0, t=0, b=0),
                                    mapbox_style="open-street-map"
                                )
                            ),
                            config={
                                'displayModeBar': False,
                                'scrollZoom': True,
                                'doubleClick': 'reset+autosize',
                                'modeBarButtonsToRemove': [
                                    'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
                                    'autoScale2d', 'resetScale2d', 'hoverClosestCartesian',
                                    'hoverCompareCartesian', 'zoom2d', 'sendDataToCloud',
                                    'toggleHover', 'toggleSpikelines', 'resetViewMapbox',
                                ],
                            },
                            style={'height': '50vh'}
                        ),
                        html.Div(
                            [
                                dbc.Spinner(color="#5DADE2", type="grow", size="lg"),
                            ],
                            id="loading-overlay",
                            style={
                                "position": "absolute",
                                "top": 0,
                                "left": 0,
                                "width": "100%",
                                "height": "100%",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                                "display": "none",
                                "justifyContent": "center",
                                "alignItems": "center",
                                "zIndex": 1000,
                            },
                        ),
                    ], style={"position": "relative"}),
                ], id='map-container'),  # Add the 'map-container' Div with the correct ID
            ], width=12),
        ]),
        # Slider Row
        dbc.Row([
            dbc.Col([
                dcc.Slider(
                    id='year-slider',
                    min=0,
                    max=1,
                    value=1,
                    step=0.001,
                    marks={x: str(map_to_year(x, min_year, max_year)) for x in [i / 12 for i in range(12)] + [1]},
                    className="slider",
                    updatemode='drag'
                ),
            ], width=12, className="slider-container", style={'marginTop': '20px'}),
        ]),
        # Hidden Divs
        html.Div(id='filtered-links', style={'display': 'none'}),
        html.Div(id='current-selection', style={'display': 'none'}),
        # Info Row
        dbc.Row([
            dbc.Col([
                html.A(
                    id='wikipedia-link',
                    children="Select any Dot",
                    target="_blank",
                    className="wikipedia-link",
                    style={
                        'fontFamily': '"Montserrat", sans-serif',
                        'fontSize': '18px',
                        'textAlign': 'center',
                        'display': 'block',
                        'marginBottom': '10px',
                        'textTransform': 'uppercase',
                        'letterSpacing': '1px',
                        'fontWeight': 'bold',
                    }
                ),
                html.Div(
                    id='description-display',
                    className="description-display",
                    style={
                        'fontFamily': '"Montserrat", sans-serif',
                        'fontSize': '16px',
                        'textAlign': 'center',
                    }
                )
            ], width=12, className="info-container", style={
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'marginTop': '0',
            }),
        ]),
    ], fluid=True, className="app-container", style=common_styles)