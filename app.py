
import os
from jama_client import jama_client
import login_dialog
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime
from weekly_status import get_weekly_status_chart
from historical_status import get_historical_status_line_chart
from current_testruns import get_current_runs_table
from current_status import get_current_status_pie_chart

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

# list of project, test plan and chart title
testing_list = [
    ('VRel', '2.7.1-3.1-FAT2 Testing (Priority1)', 'SIT FAT2 Testing Status'),
    ('PIT', 'GX5_Phase1_Stage1_FAT2_Dry_Run', 'PIT FAT2 Dry Run Status'),
]

test_deadline = datetime.strptime('Feb 28 2020', '%b %d %Y')

proj_list = [x[0] for x in testing_list]

client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, projkey_list=proj_list):
    exit(1)


colormap = \
    {'NOT_RUN': 'darkslategray', 'PASSED': 'green', 'FAILED': 'firebrick', 'BLOCKED': 'royalblue', 'INPROGRESS': 'darkorange'}
status_names = client.get_status_names()

FIG_TYPE_WEEKLY_STATUS_CHART = 'Weekly Status'
FIG_TYPE_HISTORICAL_STATUS_CHART = 'Historical Status'
FIG_TYPE_CURRENT_STATUS_CHART = 'Current Status'
FIG_TYPE_CURRENT_RUNS_TABLE = 'Test Runs For Current Week'

chart_types = [FIG_TYPE_WEEKLY_STATUS_CHART, FIG_TYPE_HISTORICAL_STATUS_CHART, FIG_TYPE_CURRENT_STATUS_CHART, FIG_TYPE_CURRENT_RUNS_TABLE]
current_chart_type = next(iter(chart_types))
testplans = [] # list of all test plans

# DB of chart data by type, testplan and test cycle
chart_data_db = {}
for project, testplan, title in testing_list:
    testplan_ui = title  # we will use title to mean testplan in the UI
    testplans.append(testplan_ui)
    chart_data_db[testplan_ui] = {}
    testcycles = [None, ] + [c for i,c in client.retrieve_testcycles(project_key=project, testplan_key=testplan)]
#    df = pd.DataFrame() # initialize an empty data frame
    for testcycle in testcycles:
        testcycle_ui = testcycle
        if testcycle is None:
            # rename it to Overall
            testcycle_ui = 'Overall'
        print(f'Creating charts for {testplan_ui}:{testcycle_ui}...')
        chart_data_db[testplan_ui][testcycle_ui] = {}
        for chart_type in chart_types:
            title = f'{chart_type} - {testplan_ui}:{testcycle_ui}'
            if chart_type == FIG_TYPE_WEEKLY_STATUS_CHART:
                chart_data_db[testplan_ui][testcycle_ui][chart_type] = \
                    [get_weekly_status_chart(client, project, testplan, testcycle, title, colormap)]
            if chart_type == FIG_TYPE_HISTORICAL_STATUS_CHART:
                chart_data_db[testplan_ui][testcycle_ui][chart_type] = \
                    [get_historical_status_line_chart(client, project, testplan, testcycle, test_deadline, title,
                                                      colormap)]
            if chart_type == FIG_TYPE_CURRENT_STATUS_CHART:
                chart_data_db[testplan_ui][testcycle_ui][chart_type] = \
                    [get_current_status_pie_chart(client, project, testplan, testcycle, title,
                                                      colormap)]
            if chart_type == FIG_TYPE_CURRENT_RUNS_TABLE:
                chart_data_db[testplan_ui][testcycle_ui][chart_type] = \
                    [html.H6(title), get_current_runs_table(client, project, testplan, testcycle, title, colormap)]

current_chart_type = next(iter(chart_types))
current_testplan = next(iter(testplans))
current_testcycle = next(iter(chart_data_db[current_testplan]))


app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='id-test-plan',
                options=[{'label': i, 'value': i} for i in testplans],
                value=current_testplan
            ),
        ],
        style={'width': '33%', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id='id-test-cycle',
                options=[{'label': i, 'value': i} for i in iter(chart_data_db[current_testplan])],
                value=current_testcycle
            ),
        ],
        style={'width': '33%', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id='id-chart-type',
                options=[{'label': i, 'value': i} for i in chart_types],
                value=current_chart_type
            ),
        ],
        style={'width': '33%', 'display': 'inline-block'})
    ]),
    html.Div(id='chart-container'),
])

@app.callback(
    Output('id-test-cycle', 'options'),
    [Input('id-test-plan', 'value')])
def update_testcycle_options(testplan):
    global current_testplan
    global current_testcycle
    current_testplan = testplan
    testcycles = [i for i in iter(chart_data_db[current_testplan])]
    if current_testcycle not in testcycles:
        current_testcycle = next(testcycles)
    options = [{'label': i, 'value': i} for i in testcycles]
    return options

@app.callback(
    Output('chart-container', 'children'),
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-chart-type', 'value')])
def update_graph(testplan, testcycle, chart_type):
    global current_chart_type
    global current_testcycle
    current_chart_type = chart_type
    current_testcycle = testcycle
    chart =  chart_data_db[testplan][testcycle][chart_type]
    return chart

if __name__ == '__main__':
    app.run_server(debug=False)
