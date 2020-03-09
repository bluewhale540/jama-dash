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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server


# initialize the data when the app starts
#tasks.update_data()

redis_instance = redis.StrictRedis.from_url(os.environ['REDIS_URL'])

def serve_layout():
    return html.Div(
        [
            dcc.Interval(interval=1 * 60 * 1000, id='interval'),
            html.H1('iDirect Test Reports'),
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id='id-test-plan'
                    ),
                ],
                style={'width': '50%', 'display': 'inline-block'}),
                html.Div([
                    dcc.Dropdown(
                        id='id-test-cycle'
                    ),
                ],
                style={'width': '50%', 'display': 'inline-block'}),
            ]),
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
    [Output('id-test-plan', 'options'),
    Output('id-test-plan', 'value')],
    [Input('interval', 'n_intervals')]
)
def update_graph(_):
    data_dict = json.loads(get_data())
    df = pd.DataFrame(data_dict)
    # TODO: check if testplan column exists first
    testplans = []
    if 'testplan' in df.columns:
        testplans = [{'label': i.replace('_', ' '), 'value': i} for i in df.testplan.unique()]
    if len(testplans) == 0:
        return 'no testplans found in dataset'
    initial_testplan = testplans[0]['value']
    return testplans, initial_testplan

@app.callback(
    Output('status', 'children'),
    [Input('interval', 'n_intervals')],
)
def update_status(_):
    data_last_updated = redis_instance.hget(
        tasks.REDIS_HASH_NAME, tasks.REDIS_UPDATED_KEY
    ).decode('utf-8')
    return 'Data last updated at {}'.format(data_last_updated)

@app.callback(
    [Output('id-test-cycle', 'options'),
     Output('id-test-cycle', 'value')],
    [Input('id-test-plan', 'value')]
)
def update_testcycle_options(testplan_ui):
    data_dict = json.loads(get_data())
    df = pd.DataFrame(data_dict)
    # TODO: check if testplan column exists first
    testcycles = []
    df = df[df.testplan.eq(testplan_ui)]
    if 'testcycle' in df.columns:
        testcycles = [{'label': i.replace('_', ' '), 'value': i} for i in df.testcycle.unique()]
    if len(testcycles) == 0:
        return None, None
    initial_testcycle = testcycles[0]['value']
    return testcycles, initial_testcycle


if __name__ == '__main__':
    app.run_server(debug=False)
