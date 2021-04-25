# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from sodapy import Socrata

"""
initiate dash app
"""
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

"""
get data 
"""
#data_url = 'https://health.data.ny.gov/resource/xdss-u53e.csv'

# Unauthenticated client only works with public data sets. Note 'None'
# in place of application token, and no username or password:
client = Socrata("health.data.ny.gov", None)

# Example authenticated client (needed for non-public datasets):
# client = Socrata("health.data.ny.gov",
#                  "covid",
#                  username="cp5z95nt01g5jh145uqfqyfbn",
#                  password="2bb9tq2hp88bodchhhuwrydqpdmc6ealz9ln7eo8vdox3i5nyp")

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("xdss-u53e", limit=30000)

# Convert to pandas DataFrame
df = pd.DataFrame.from_records(results)

print(df.shape)
# Data columns
'''
"test_date","county","new_positives","cumulative_number_of_positives","total_number_of_tests","cumulative_number_of_tests"
'''

"""
Dash layout
"""
fig = px.line(df, x="test_date", y="cumulative_number_of_positives", color="county", hover_name="county", log_y=True)

markdown_text = '''

### Covid-19 cumulative number of positives in New York State
Chart by Blue Jay Analytics, data source: [health.data.ny.gov](https://health.data.ny.gov/resource/xdss-u53e.csv)

View county data by double-click county name in the right side legend.
'''
app.layout = html.Div(
    children=[
        dcc.Markdown(children=markdown_text),
        
        dcc.Graph(
            id='covid-cumulative-graph',
            figure=fig
        )
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True) # hot reloading
