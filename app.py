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
    html.Div([
        html.H1([html.I(className='fas fa-chart-bar'), ' Data Visualization Dashboard'], style={'textAlign': 'center', 'color': '#007BFF', 'marginBottom': '10px'}),
        html.Button('🌙', id='theme-switch', n_clicks=0, style={'float': 'right', 'margin': '10px', 'fontSize': '20px', 'background': 'none', 'border': 'none'}),
    ], style={'position': 'relative'}),

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
            'marginBottom': '20px',
            'backgroundColor': '#f7f7f7'
        },
        multiple=False
    ),
    html.Div(id='error-message', style={'color': 'red', 'textAlign': 'center', 'marginBottom': '10px'}),
    dcc.Dropdown(
        id='dropdown',
        options=[],
        value=None,
        style={'width': '50%', 'margin': 'auto', 'marginBottom': '10px'},
        multi=True
    ),
    html.Button('Download Data', id='download-btn', style={'display': 'block', 'margin': '10px auto', 'backgroundColor': '#007BFF', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'padding': '10px 20px', 'fontSize': '16px'}),
    dcc.Download(id='download-data'),
    html.Div([
        html.Div([
            html.H4('Data Preview'),
            html.Div(id='data-table'),
        ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '2%'}),
        html.Div([
            html.H4('Statistics'),
            html.Div(id='stats-table'),
        ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ], style={'width': '90%', 'margin': 'auto', 'marginBottom': '20px'}),
    html.Div([
        dcc.Graph(id='bar-chart', className='graph-container'),
        dcc.Graph(id='line-chart', className='graph-container'),
        dcc.Graph(id='scatter-chart', className='graph-container'),
        dcc.Graph(id='pie-chart', className='graph-container'),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})

    
])

# Callback to read the uploaded file and update the dropdown options
@app.callback(
    [Output('dropdown', 'options'),
     Output('dropdown', 'value'),
     Output('data-table', 'children'),
     Output('error-message', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_dropdown_options(contents, filename):
    if contents is None:
        return [], None, '', ''
    try:
        df = parse_contents(contents, filename)
        if df.empty:
            return [], None, '', 'Uploaded file is empty or invalid.'
        dropdown_options = [{'label': col, 'value': col} for col in df.columns]
        dropdown_value = [df.columns[0]] if not df.empty else []
        # Data preview table (show first 5 rows)
        preview = df.head().to_dict('records')
        table = html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(str(row[col])) for col in df.columns]) for row in preview
            ])
        ])
        return dropdown_options, dropdown_value, table, ''
    except Exception as e:
        return [], None, '', f'Error: {str(e)}'

# Callback to show statistics for selected columns
@app.callback(
    Output('stats-table', 'children'),
    [Input('dropdown', 'value'),
     Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_stats(selected_values, contents, filename):
    if not selected_values or contents is None:
        return ''
    df = parse_contents(contents, filename)
    stats_tables = []
    for selected_value in selected_values:
        if selected_value not in df.columns or df[selected_value].dtype not in ['int64', 'float64']:
            stats_tables.append(html.Div(f'No statistics for {selected_value}'))
            continue
        stats = df[selected_value].describe().to_dict()
        table = html.Table([
            html.Thead(html.Tr([html.Th(selected_value)])),
            html.Tbody([
                html.Tr([html.Td(str(k)), html.Td(str(round(v, 2)))]) for k, v in stats.items()
            ])
        ])
        stats_tables.append(table)
    return html.Div(stats_tables)

# Callback to update the bar chart based on the dropdown selection
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('dropdown', 'value')],
    [State('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_bar_chart(selected_values, contents, filename):
    if not selected_values or contents is None:
        raise PreventUpdate
    df = parse_contents(contents, filename)
    if 'Month' not in df.columns:
        return {'data': [], 'layout': {'title': 'Invalid data'}}
    data = []
    for col in selected_values:
        if col in df.columns:
            data.append({
                'x': df['Month'],
                'y': df[col],
                'type': 'bar',
                'name': col,
                'marker': {'color': '#007BFF'},
            })
    return {
        'data': data,
        'layout': {
            'title': f"{' & '.join(selected_values)} by Month",
            'plot_bgcolor': '#f9f9f9',
            'paper_bgcolor': '#f9f9f9',
            'font': {'color': '#333'},
        }
    }

# Callback to update the line chart based on the dropdown selection
@app.callback(
    Output('line-chart', 'figure'),
    [Input('dropdown', 'value')],
    [State('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_line_chart(selected_values, contents, filename):
    if not selected_values or contents is None:
        raise PreventUpdate
    df = parse_contents(contents, filename)
    if 'Month' not in df.columns:
        return {'data': [], 'layout': {'title': 'Invalid data'}}
    data = []
    for col in selected_values:
        if col in df.columns:
            data.append({
                'x': df['Month'],
                'y': df[col],
                'type': 'line',
                'name': col,
                'line': {'width': 3},
            })
    return {
        'data': data,
        'layout': {
            'title': f"{' & '.join(selected_values)} by Month",
            'plot_bgcolor': '#f9f9f9',
            'paper_bgcolor': '#f9f9f9',
            'font': {'color': '#333'},
        }
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

# Scatter chart callback
@app.callback(
    Output('scatter-chart', 'figure'),
    [Input('dropdown', 'value')],
    [State('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_scatter_chart(selected_values, contents, filename):
    if not selected_values or contents is None or len(selected_values) < 2:
        return {'data': [], 'layout': {'title': 'Select at least two columns for scatter plot'}}
    df = parse_contents(contents, filename)
    x_col, y_col = selected_values[:2]
    if x_col not in df.columns or y_col not in df.columns:
        return {'data': [], 'layout': {'title': 'Invalid columns'}}
    return {
        'data': [{
            'x': df[x_col],
            'y': df[y_col],
            'mode': 'markers',
            'type': 'scatter',
            'marker': {'size': 10, 'color': '#17a2b8'},
            'name': f'{x_col} vs {y_col}'
        }],
        'layout': {
            'title': f'Scatter: {x_col} vs {y_col}',
            'plot_bgcolor': '#f9f9f9',
            'paper_bgcolor': '#f9f9f9',
            'font': {'color': '#333'},
        }
    }

# Pie chart callback
@app.callback(
    Output('pie-chart', 'figure'),
    [Input('dropdown', 'value')],
    [State('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_pie_chart(selected_values, contents, filename):
    if not selected_values or contents is None:
        return {'data': [], 'layout': {'title': 'Select a column for pie chart'}}
    df = parse_contents(contents, filename)
    col = selected_values[0]
    if col not in df.columns:
        return {'data': [], 'layout': {'title': 'Invalid column'}}
    value_counts = df[col].value_counts()
    return {
        'data': [{
            'labels': value_counts.index,
            'values': value_counts.values,
            'type': 'pie',
            'name': col
        }],
        'layout': {
            'title': f'Pie Chart: {col}',
            'plot_bgcolor': '#f9f9f9',
            'paper_bgcolor': '#f9f9f9',
            'font': {'color': '#333'},
        }
    }

# Download callback
@app.callback(
    Output('download-data', 'data'),
    [Input('download-btn', 'n_clicks'),
     Input('upload-data', 'contents')],
    [State('upload-data', 'filename')],
    prevent_initial_call=True
)
def download_data(n_clicks, contents, filename):
    if n_clicks is None or contents is None:
        return None
    df = parse_contents(contents, filename)
    return dict(content=df.to_csv(index=False), filename='dashboard_data.csv')

# Theme switcher callback
@app.callback(
    Output('app-container', 'style'),
    [Input('theme-switch', 'n_clicks')]
)
def switch_theme(n_clicks):
    if n_clicks % 2 == 1:
        return {'backgroundColor': '#222', 'color': '#eee'}
    return {'backgroundColor': '#fff', 'color': '#222'}

# Run the app
if __name__ == '__main__':
    app.layout = html.Div(app.layout.children, id='app-container')
    app.run(debug=True)
