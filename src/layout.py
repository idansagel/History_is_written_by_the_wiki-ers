from dash import dcc, html
import math
import plotly.graph_objects as go

def map_to_year(x: float, min_year: int, max_year: int) -> int:
    if not 0 <= x <= 1:
        raise ValueError("x must be between 0 and 1 inclusive")
    scaled_x = math.pow(x, 0.2)
    return int(min_year + scaled_x * (max_year - min_year))

def create_app_layout(unique_occupations, min_year, max_year):
    common_styles = {
        'fontFamily': '"Montserrat", sans-serif',
        'color': '#333',
    }
    
    dropdown_container_style = {
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'marginBottom': '20px',
    }
    
    dropdown_style = {
        'width': '200px',
        'marginLeft': '5px',
    }
    
    label_style = {
        'fontWeight': 'bold',
        'marginRight': '5px',
    }

    pair_style = {
        'display': 'flex',
        'alignItems': 'center',
        'marginRight': '20px',
    }

    slider_style = {
        'width': '100%',
        'marginTop': '20px',
    }

    button_style = {
        'padding': '10px 20px',
        'backgroundColor': '#5DADE2',  # Cool shade of light blue
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'fontSize': '14px',
        'cursor': 'pointer',
        'transition': 'background-color 0.3s',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.2)',
    }

    return html.Div([
        html.Div([
            html.H1(
                f"Important Figures Alive in {max_year}",
                id="app-title",
                style={
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'textTransform': 'uppercase',
                    'letterSpacing': '2px',
                    'marginBottom': '20px',
                    **common_styles
                }
            ),
            html.Div([
                html.Div([
                    html.Label("Occupation:", style=label_style),
                    dcc.Dropdown(
                        id='occupation-dropdown',
                        options=[{'label': occ, 'value': occ} for occ in unique_occupations],
                        value="All",
                        placeholder="Select an occupation",
                        style=dropdown_style,
                        clearable=False
                    )
                ], style=pair_style),
                html.Div([
                    html.Label("Related by:", style=label_style),
                    dcc.Dropdown(
                        id='group-dropdown',
                        options=[
                            {'label': 'Share Wikipedia Links', 'value': 'neighbors'},
                            {'label': 'Same Cluster', 'value': 'louvain'}
                        ],
                        value='neighbors',
                        placeholder="Select a group option",
                        style=dropdown_style,
                        clearable=False
                    )
                ], style=pair_style),
                html.Button('Ranks List', id='open-modal-button', style=button_style),
            ], style=dropdown_container_style),
        ], className="header", style=common_styles),

        html.Div([
            html.Div([
                html.Div([
                    html.H2('List of Figures and Their Ranks'),
                    html.Div(id='list-container', style={'maxHeight': '400px', 'overflowY': 'scroll'}),
                    html.Button('Close', id='close-modal-button', style={'marginTop': '20px', **button_style}),
                ], className='modal-body', style={'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px'}),
            ], className='modal-content-wrapper', style={'position': 'relative', 'margin': '0 auto', 'width': '80%', 'maxWidth': '500px'}),
        ], id='modal', className='modal', style={'display': 'none', 'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0, 0, 0, 0.5)', 'justifyContent': 'center', 'alignItems': 'center'}),

        html.Div([
            dcc.Loading(
                id="loading-1",
                type="default",
                children=[
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
                            'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'zoom2d', 'sendDataToCloud', 'toggleHover', 'toggleSpikelines', 'resetViewMapbox'],
                        }
                    )
                ]
            )
        ], id='map-container', className="map-container", style=common_styles),

        html.Div([
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
        ], className="slider-container", style={**common_styles, **slider_style}),
        
        html.Div(id='filtered-links', style={'display': 'none'}),
        html.Div(id='current-selection', style={'display': 'none'}),

        html.Div([
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
        ], className="info-container", style={
            **common_styles,
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'marginTop': '0',
        })
    ], className="app-container", style=common_styles)