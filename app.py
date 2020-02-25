
import os
from jama_client import jama_client
import login_dialog
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime
from weekly_testrun_status import get_weekly_status_bar_chart
from historical_testrun_status import get_historical_status_line_chart
from current_week_status_table import get_current_runs_table
from current_testrun_status import get_current_status_pie_chart

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
#    ('PIT', 'GX5_Phase1_Stage1_FAT2_Dry_Run', 'PIT FAT2 Dry Run Status'),
]
start_date = datetime.strptime('Feb 01 2020', '%b %d %Y')
test_deadline = datetime.strptime('Feb 28 2020', '%b %d %Y')

proj_list = [x[0] for x in testing_list]

client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, projkey_list=proj_list):
    exit(1)


colormap = \
    {'NOT_RUN': 'darkslategray', 'PASSED': 'green', 'FAILED': 'firebrick', 'BLOCKED': 'royalblue', 'INPROGRESS': 'darkorange'}
status_names = client.get_status_names()

FIG_TYPE_WEEKLY_STATUS_BAR_CHART = 'Weekly Status'
FIG_TYPE_HISTORICAL_STATUS_LINE_CHART = 'Historical Status'
FIG_TYPE_CURRENT_STATUS_PIE_CHART = 'Current Status'
FIG_TYPE_CURRENT_STATUS_BY_SET_BAR_CHART = 'Current Status By Testrun Set'
FIG_TYPE_CURRENT_RUNS_TABLE = 'Test Runs For Current Week'

chart_types = [
    FIG_TYPE_WEEKLY_STATUS_BAR_CHART,
    FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
    FIG_TYPE_CURRENT_STATUS_PIE_CHART,
    FIG_TYPE_CURRENT_RUNS_TABLE]
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
    df = client.retrieve_testruns(project_key=project, testplan_key=testplan)
    for testcycle in testcycles:
        testcycle_ui = testcycle  if testcycle is not None else 'Overall'
        # get a list of test cases
        df1 = df[df.testcycle.eq(testcycle)] if testcycle is not None else df
        testcases = [c for c in iter(df1.testcase.unique())]
        print(f'Creating charts for {testplan_ui}:{testcycle_ui}...')
        chart_data_db[testplan_ui][testcycle_ui] = {}
        testcases = [None, ] + testcases
        for testcase in testcases:
            testcase_ui = testcase if testcase is not None else 'Overall'
            chart_data_db[testplan_ui][testcycle_ui][testcase_ui] = {}
            for chart_type in chart_types:
                title = f'{chart_type} - {testplan_ui}'
                if testcycle is not None:
                    title += f':{testcycle_ui}'
                if testcase is not None:
                    title += f':{testcase_ui}'

                if chart_type == FIG_TYPE_WEEKLY_STATUS_BAR_CHART:
                    chart_data_db[testplan_ui][testcycle_ui][testcase_ui][chart_type] = \
                        [get_weekly_status_bar_chart(
                            df=df,
                            testcycle=testcycle,
                            testcase=testcase,
                            title=title,
                            colormap=colormap)]

                if chart_type == FIG_TYPE_HISTORICAL_STATUS_LINE_CHART:
                    chart_data_db[testplan_ui][testcycle_ui][testcase_ui][chart_type] = \
                        [get_historical_status_line_chart(
                            df=df,
                            testcycle=testcycle,
                            testcase=testcase,
                            start_date=start_date,
                            test_deadline=test_deadline,
                            title=title,
                            colormap=colormap,
                            treat_blocked_as_not_run=True,
                            treat_inprogress_as_not_run=True)]

                if chart_type == FIG_TYPE_CURRENT_STATUS_PIE_CHART:
                    chart_data_db[testplan_ui][testcycle_ui][testcase_ui][chart_type] = \
                        [get_current_status_pie_chart(
                            df=df,
                            testcycle=testcycle,
                            testcase=testcase,
                            title=title,
                            colormap=colormap)]

                if chart_type == FIG_TYPE_CURRENT_RUNS_TABLE:
                    chart_data_db[testplan_ui][testcycle_ui][testcase_ui][chart_type] = \
                        [html.H6(title), get_current_runs_table(
                            df=df,
                            testcycle=testcycle,
                            testcase=testcase,
                            title=title,
                            colormap=colormap)]

current_chart_type = next(iter(chart_types))
current_testplan = next(iter(testplans))
current_testcycle = next(iter(chart_data_db[current_testplan]))
current_testcase = next(iter(chart_data_db[current_testplan][current_testcycle]))


app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='id-test-plan',
                options=[{'label': i, 'value': i} for i in testplans],
                value=current_testplan
            ),
        ],
        style={'width': '50%', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id='id-test-cycle',
                options=[{'label': i, 'value': i} for i in iter(chart_data_db[current_testplan])],
                value=current_testcycle
            ),
        ],
        style={'width': '50%', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id='id-test-case',
                options=[{'label': i, 'value': i} for i in iter(chart_data_db[current_testplan][current_testcycle])],
                value=current_testcase
            ),
        ],
        style={'width': '50%', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id='id-chart-type',
                options=[{'label': i, 'value': i} for i in chart_types],
                value=current_chart_type
            ),
        ],
        style={'width': '50%', 'display': 'inline-block'})
    ]),
    html.Div(id='chart-container'),
])

@app.callback(
    [Output('id-test-cycle', 'options'),
     Output('id-test-cycle', 'value')],
    [Input('id-test-plan', 'value')]
)
def update_testcycle_options(testplan):
    global current_testplan
    global current_testcycle
    current_testplan = testplan
    testcycles = [i for i in iter(chart_data_db[current_testplan])]
    if current_testcycle not in testcycles:
        current_testcycle = next(iter(testcycles))
    options = [{'label': i, 'value': i} for i in testcycles]
    return options, current_testcycle

@app.callback(
    [Output('id-test-case', 'options'),
     Output('id-test-case', 'value')],
    [Input('id-test-plan', 'value'),
    Input('id-test-cycle', 'value')]
)
def update_testcase_options(testplan, testcycle):
    global current_testplan
    global current_testcycle
    global current_testcase
    current_testplan = testplan
    current_testcycle = testcycle
    testcases = [i for i in iter(chart_data_db[current_testplan][current_testcycle])]
    if current_testcase not in testcases:
        current_testcase = next(iter(testcases))
    options = [{'label': i, 'value': i} for i in testcases]
    return options, current_testcase

@app.callback(
    Output('chart-container', 'children'),
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-test-case', 'value'),
     Input('id-chart-type', 'value')])
def update_graph(testplan, testcycle, testcase, chart_type):
    global current_chart_type
    global current_testcycle
    global current_testcase
    current_chart_type = chart_type
    current_testcycle = testcycle
    current_testcase = testcase
    testcycles = [i for i in iter(chart_data_db[testplan])]
    if current_testcycle not in testcycles:
        current_testcycle = next(iter(testcycles))
    testcases = [i for i in iter(chart_data_db[current_testplan][current_testcycle])]
    if current_testcase not in testcases:
        current_testcase = next(iter(testcases))
    chart =  chart_data_db[testplan][current_testcycle][current_testcase][chart_type]
    return chart

if __name__ == '__main__':
    app.run_server(debug=False)
