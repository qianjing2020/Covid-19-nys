# Run this app with `python <app_name>.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import sys
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
from sodapy import Socrata
from datetime import date
from urllib.request import urlopen
import json
from settings import API_CAN

pd.options.mode.chained_assignment = None  # default='warn'
"""
initiate dash app
"""
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

"""
get geo data that contains counity boundaries
"""
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
#fips_df = pd.read_csv('county_fips.csv')

"""
get vaccination data - most recently updated county-level Covid vaccination data 
"""
data_URL = "https://api.covidactnow.org/v2/county/NY.csv?apiKey="+ API_CAN

try:
    data_vac = pd.read_csv(data_URL, dtype={"fips": str})
    print('Vaccination data successfully retrieved!')
except:
    print('Upstream pipeline broke. Check vaccination data source.')
    sys.exit()

vac_df = data_vac[['fips', 'county', 'state', 'population', 'actuals.cases', 'actuals.deaths', 'actuals.vaccinationsCompleted', 'metrics.vaccinationsCompletedRatio']]

# change column headers
vac_df.columns=['FIPS', 'county', 'state', 'population', 'cases', 'deaths', 'vaccination completed', 'vaccination completed (%)']
# change last col to percentage
vac_df.iloc[:,-1]=vac_df.iloc[:,-1]*100
# round all numerical values to 2 decimals
vac_df.round(2)

# print(vac_df.head())

"""
get Covid case time series data from NYS public health dept
"""
try:
    client = Socrata("health.data.ny.gov", None)
    results = client.get("xdss-u53e", limit=30000)
    print('Positive case data successfully retrieved!')
except:
    print('Upstream pipeline broke. Check Socrata API and NYS Dept of Public Health covid data source.')
    sys.exit()

# Convert data to pandas DataFrame
data = pd.DataFrame.from_records(results)

# Convert strings to numbers
cols = data.columns.tolist()
# create df for converted data
df = data.iloc[:, :2]
num_cols = cols[2:]
for col in num_cols:
    df.loc[:, col] = pd.to_numeric(data.loc[:, col].values)

# string test_date to datetime
df.loc[:, 'datetime'] = pd.to_datetime(df.loc[:, 'test_date'].values)

# set index to datetime
df.set_index('datetime', inplace=True)

# create subset dataset for last 3 months
start_date = df.index[-1] - pd.tseries.offsets.DateOffset(months=3)
subset = df[df.index > start_date]
print(f'Data cols: {subset.columns.tolist()}')

"""
Create components for Dash layout
"""
y = vac_df['vaccination completed (%)']
miny, maxy = y.min(), y.max()

fig0 = px.choropleth_mapbox(
        vac_df, geojson=counties, locations="FIPS",
        hover_name = "county", 
        hover_data = [ "population", "vaccination completed (%)"],
        color='vaccination completed (%)',
        range_color=(miny, maxy), 
        mapbox_style="carto-positron",
        opacity=0.6,
        zoom=6, center={"lat": 43.2994, "lon":-74.2179},
        labels={'Fully-vaccinated (%)': 'vaccination completed (%)'}
        )
fig0.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})


# sorted data from the last date of sample
subset1 = subset[subset.index == subset.index[-1]
                 ].sort_values(by='county', ascending=True)

fig1 = px.scatter(
    subset1,
    x="cumulative_number_of_tests",
    y="cumulative_number_of_positives", color="county",
    hover_name="county", size="cumulative_number_of_positives",
    size_max=60,
    log_x=True,
    log_y=True,
)

# Get names for dcc dropdown menu
county_names = subset['county'].unique()
# print(county_names)

title = 'Covid-19 Vaccination and Cases in NYS'
timestamptxt = 'Blue Jay Analytics, ' + date.today().strftime("%B %d, %Y")

app.layout = html.Div([
    html.H1(title),
    
    html.P(timestamptxt),

    dcc.Markdown(
        '''Data source: [health.data.ny.gov](https://health.data.ny.gov/resource/xdss-u53e.csv) and [Covid Act Now Org](https://api.covidactnow.org/)'''
    ),
  
    html.Div([
        html.H4( "Fig 1. Vaccination Completeness in NYS counties"),    
        dcc.Graph(
            id="vac-choropleth",
            figure=fig0
            ),

        html.H4('Fig 2. Cumulative positive cases in NYS counties'),
        dcc.Graph(
            id='covid-cumulative-graph',
            figure=fig1
            ),

        html.H4('Fig 3. New positive cases in selected counties'),
        dcc.Dropdown(
            id='county-selected',
            options=[{'label': i, 'value': i} for i in county_names],
            multi=True,
            value=['Albany', 'St. Lawrence']
        ),

        dcc.Graph(
            id='new-case-county-graph'
        )
    ])
])

@app.callback(
    Output('new-case-county-graph', 'figure'),
    [Input('county-selected', 'value')]
)
def update_graph(selected_county):
    condition = subset['county'].isin(selected_county)
    subset2 = subset[condition]
    fig = px.bar(
        subset2,
        x="test_date",
        y="new_positives",
        color='county',
        barmode='group',
        opacity=0.9
        )

    fig.update_layout(
        margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig

# # update text 
# @app.callback(Output('live-update-text', 'children'),
#               [Input('interval-component', 'n_intervals')])
# def update_date(n):
#       return [html.P('Last updated ' +str(datetime.datetime.now()))]


if __name__ == '__main__':
    app.run_server(debug=True)  # hot reloading
