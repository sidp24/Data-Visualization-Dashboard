import pandas as pd
import dash
from dash import dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from dash.dependencies import State
import base64
import io

# Create the Dash app
app = dash.Dash(__name__)

# Add the Font Awesome CSS link to your app
app.css.append_css({
    "external_url": "https://use.fontawesome.com/releases/v5.15.3/css/all.css"
})

# Define the layout of the dashboard
app.layout = html.Div([
    html.H1([html.I(className='fas fa-chart-bar'), ' Data Visualization Dashboard'], style={'textAlign': 'center', 'color': '#007BFF'}),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': 'auto',
            'marginBottom': '20px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),dcc.Dropdown(
        id='dropdown',
        options=[],
        value=None,
        style={'width': '50%', 'margin': 'auto', 'marginBottom': '20px'}
    ),

    html.Div([
        dcc.Graph(id='bar-chart', className='graph-container'),
        dcc.Graph(id='line-chart', className='graph-container'),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})

    
])

# Callback to read the uploaded file and update the dropdown options
@app.callback(
    [Output('dropdown', 'options'),
     Output('dropdown', 'value')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_dropdown_options(contents, filename):
    if contents is None:
        raise PreventUpdate

    df = parse_contents(contents, filename)
    dropdown_options = [{'label': col, 'value': col} for col in df.columns]
    dropdown_value = df.columns[0] if not df.empty else None
    return dropdown_options, dropdown_value

# Callback to update the bar chart based on the dropdown selection
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('dropdown', 'value')],
    [State('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_bar_chart(selected_value, contents, filename):
    if selected_value is None or contents is None:
        raise PreventUpdate

    df = parse_contents(contents, filename)
    data_to_plot = df[['Month', selected_value]].to_dict('list')
    return {
        'data': [{'x': data_to_plot['Month'], 'y': data_to_plot[selected_value], 'type': 'bar'}],
        'layout': {'title': f'{selected_value} by Month'}
    }

# Callback to update the line chart based on the dropdown selection
@app.callback(
    Output('line-chart', 'figure'),
    [Input('dropdown', 'value')],
    [State('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_line_chart(selected_value, contents, filename):
    if selected_value is None or contents is None:
        raise PreventUpdate

    df = parse_contents(contents, filename)
    data_to_plot = df[['Month', selected_value]].to_dict('list')
    return {
        'data': [{'x': data_to_plot['Month'], 'y': data_to_plot[selected_value], 'type': 'line'}],
        'layout': {'title': f'{selected_value} by Month'}
    }

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        else:
            raise Exception('Unsupported file format')
    except Exception as e:
        print(e)
        return pd.DataFrame()
    return df

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
