import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime as dt
import flask
import json
import redis
import time
import os
import pandas as pd

import tasks

app = dash.Dash('app')
server = app.server

# initialize the data when the app starts
#tasks.update_data()

redis_instance = redis.StrictRedis.from_url(os.environ['REDIS_URL'])

def serve_layout():
    return html.Div(
        [
            dcc.Interval(interval=1 * 60 * 1000, id='interval'),
            html.H1('Redis, Celery, and Periodic Updates'),
            html.Div(id='status'),
            html.Div(id='chart'),
        ]
    )


app.layout = serve_layout

def get_data():
    '''Retrieve the dataframe from Redis
    This dataframe is periodically updated through the redis task
    '''
    jsonified_df = redis_instance.hget(
        tasks.REDIS_HASH_NAME, tasks.REDIS_DATASET_KEY
    ).decode('utf-8')

    return jsonified_df


@app.callback(
    Output('chart', 'children'),
    [Input('interval', 'n_intervals')],
)
def update_graph(_):
    data_dict = json.loads(get_data())
    testplans = [x['name'] for x in data_dict['testplan']]
    if len(testplans) == 0:
        return 'no testplans found'
    return html.Div([
                   dcc.Dropdown(
                       id='id-test-plan',
                       options=[{'label': i, 'value': i} for i in testplans],
                       value=testplans[0]
                   ),
               ])


@app.callback(
    Output('status', 'children'),
    [Input('interval', 'n_intervals')],
)
def update_status(value, _):
    data_last_updated = redis_instance.hget(
        tasks.REDIS_HASH_NAME, tasks.REDIS_UPDATED_KEY
    ).decode('utf-8')
    return 'Data last updated at {}'.format(data_last_updated)


if __name__ == '__main__':
    app.run_server(debug=False)
