# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
from sodapy import Socrata
from datetime import datetime


"""
initiate dash app
"""
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

"""
get data 
"""
# data_url = "https://health.data.ny.gov/resource/xdss-u53e.csv?$where=test_date>'2021-01-10T12:00:00'"
# df = pd.read_csv(data_url)

# Unauthenticated client only works with public data sets. Note 'None'
# in place of application token, and no username or password:
client = Socrata("health.data.ny.gov", None)

results = client.get("xdss-u53e", limit=30000)

# Convert data to pandas DataFrame
# string to numbers
data = pd.DataFrame.from_records(results)

cols = data.columns.tolist()
df = data.iloc[:, :2]
num_cols = cols[2:]
for col in num_cols: 
    df[col] = pd.to_numeric(data[col])
    
# string test_date to datetime 
df['datetime'] = pd.to_datetime(df['test_date'])

# set index to datetime
df.set_index('datetime', inplace=True)

# create subset dataset for the latest 3 months
start_date = df.index[-1] - pd.tseries.offsets.DateOffset(months=3)
subset = df[df.index > start_date]

print(df.shape)
print(subset.shape)
# Data columns
'''
"test_date","county","new_positives","cumulative_number_of_positives","total_number_of_tests","cumulative_number_of_tests"
'''

"""
Dash layout
"""
markdown_text = '''
## Covid-19 Chart 
#### data source: [health.data.ny.gov](https://health.data.ny.gov/resource/xdss-u53e.csv)
'''
subset1 = subset[subset.index==subset.index[-1]].sort_values(by='county', ascending=True)

fig1 = px.scatter(
    subset1, 
    x="cumulative_number_of_tests", 
    y="cumulative_number_of_positives", color="county",
    hover_name="county", size="cumulative_number_of_positives", 
    size_max=60,
    log_x=True, 
    log_y=True, 
    )

county_names = subset['county'].unique()

app.layout = html.Div([
    html.P(
        children=dcc.Markdown(children=markdown_text)
        ),

    html.Div([
        html.H4('Latest cumulative cases in New York State'),      
        dcc.Graph(
            id='covid-cumulative-graph',
            figure=fig1
        ),

        html.H4('Latest new positives by county'),
        dcc.Dropdown(
            id='county-selected',
            options=[{'label':i, 'value':i} for i in county_names],
            value='St. Lawrence'
        ),

        dcc.Graph(
            id='covid-new-case-by-county'
        )
        ]
    )
])

@app.callback(
    Output('covid-new-case-by-county', 'figure'),
    Input('county-selected', 'value')
)
def update_graph(county_selected_name):
    subset2 = subset[subset['county']==county_selected_name]
    fig = px.scatter(
        subset2, 
        x="test_date",
        y="new_positives", 
        hover_name="new_positives")
        
    fig.update_layout(
        margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')
    
    return fig


if __name__ == '__main__':
    app.run_server(debug=True) # hot reloading
