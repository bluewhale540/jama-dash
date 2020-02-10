
import os
from jama_client import jama_client
import login_dialog
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


jama_url = os.environ.get('JAMA_API_URL')
jama_api_username = os.environ.get('JAMA_API_USERNAME')
jama_api_password = os.environ.get('JAMA_API_PASSWORD')

if jama_url is None:
    jama_url = 'https://paperclip.idirect.net'

if jama_api_password is None or jama_api_username is None:
    # get Jama/contour login credentials using a dialog box
    while True:
        result = login_dialog.run()
        if result is None:
            exit(1)
        break
    jama_api_username = result[0]
    jama_api_password = result[1]

client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password):
    exit(1)
# list of project, test plan and chart title
testing_list = [
    ('PIT', 'GX5_Phase1_Stage1_FAT2_Dry_Run', 'PIT FAT2 Dry Run Status'),
    ('VRel', '2.7.1-3.1-FAT2 Testing (Priority1)', 'SIT FAT2 Testing Status')
]

colormap = \
    {'NOT_RUN': 'gray', 'PASSED': 'green', 'FAILED': 'firebrick', 'BLOCKED': 'royalblue', 'INPROGRESS': 'orange'}
status_names = client.get_status_names()

df_by_testplan = {}
for project, testplan, title in testing_list:
    testcycle_db = client.retrieve_testcycles(project_key=project, testplan_key=testplan)
    if testcycle_db is None:
        exit(1)

    testcycles = [None,]
    for id, cycle in testcycle_db:
        testcycles.append(cycle)
    df_by_cycle = {}
    for cycle in testcycles:
        df = client.get_testrun_status_by_planned_weeks(project_key=project, testplan_key=testplan,
                                                        testcycle_key=cycle)
        if cycle is None:
            df_by_cycle['Overall'] = df
        else:
            df_by_cycle[cycle] = df
    df_by_testplan[title] = df_by_cycle

current_testplan = next(iter(df_by_testplan))
current_testcycle = next(iter(df_by_testplan[current_testplan]))


app.layout = html.Div([
    html.Div([

        html.Div([
            dcc.Dropdown(
                id='id-test-plan',
                options=[{'label': i, 'value': i} for i in iter(df_by_testplan)],
                value=current_testplan
            ),
        ],
        style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='id-test-cycle',
                #options=[{'label': i, 'value': i} for i in df_by_testplan[current_testplan]],
                value=current_testcycle
            ),
        ],
        style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='weekly-status'),
])

@app.callback(
    Output('id-test-cycle', 'options'),
    [Input('id-test-plan', 'value')])
def update_testcycle_options(testplan):
    current_testplan = testplan
    current_testcycle = next(iter(df_by_testplan[current_testplan]))
    options = [{'label': i, 'value': i} for i in iter(df_by_testplan[testplan])]
    return options

@app.callback(
    Output('id-test-cycle', 'value'),
    [Input('id-test-plan', 'value')])
def update_current_testcycle(testplan):
    current_testcycle = next(iter(df_by_testplan[testplan]))
    return current_testcycle

@app.callback(
    Output('weekly-status', 'figure'),
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value')])
def update_graph(testplan, testcycle):
    current_testplan = testplan
    current_testcycle = testcycle
    df_by_cycle = df_by_testplan[current_testplan]
    if current_testcycle not in iter(df_by_cycle):
        current_testcycle = next(iter(df_by_testplan[current_testplan]))
    df = df_by_cycle[current_testcycle]
    data = []
    x_axis = df['planned_week'].values
    for status in status_names:
        y_axis = df[status].values
        data.append(dict(name=status, x=x_axis, y=y_axis, type='bar',
                         text=y_axis,
                         textposition='auto',
                         marker=dict(color=colormap[status])))
    return {
        'data': data,
        'layout': dict(
            title=testplan + ': ' + testcycle,
            uniformtext_minsize=8,
            uniformtext_mode='auto',
            xaxis={
                'title': 'Planned Week',
            },
            yaxis={
                'title': 'Number Of Test Runs',
            },
            barmode='stack'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=False)
