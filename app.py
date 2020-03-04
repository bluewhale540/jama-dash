
import os
from os.path import expanduser, isfile
import datetime
from jama_client import jama_client
import login_dialog
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from weekly_status import get_weekly_status_bar_chart, get_current_week_testruns_table
from historical_status import get_historical_status_line_chart
from current_status import get_current_status_pie_chart, get_testgroup_status_bar_chart
from testrun_utils import get_status_names, JamaReportsConfig
from dateutil import parser
import json
from flask_caching import Cache



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

CACHE_CONFIG = {
    # 'redis' or 'filesystem'
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': './.cachedir',
    # 'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379')
    'DEBUG': True
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

FIG_TYPE_WEEKLY_STATUS_BAR_CHART = 'Weekly Status'
FIG_TYPE_HISTORICAL_STATUS_LINE_CHART = 'Historical Status'
FIG_TYPE_CURRENT_STATUS_PIE_CHART = 'Current Status'
FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART = 'Current Status By Test Group'
FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART = 'Test Groups with Blocked/Failed Runs'
FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART = 'Test Groups with Not Run/In Progress Runs'
FIG_TYPE_CURRENT_RUNS_TABLE = 'Test Runs For Current Week'

ALL_TEST_CYCLES = 'All Test Cycles'
ALL_TEST_GROUPS = 'All Test Groups'

def get_chart_types():
    chart_types = [
        FIG_TYPE_WEEKLY_STATUS_BAR_CHART,
        FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
        FIG_TYPE_CURRENT_STATUS_PIE_CHART,
        FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART,
        FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART,
        FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART,
        FIG_TYPE_CURRENT_RUNS_TABLE]
    return chart_types

@cache.memoize()
def connect(config):
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

    config = JamaReportsConfig()
    if config.read_config_file() is False:
        print('Error reading config')
        return None

    proj_list = config.get_projects()

    client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
    if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, projkey_list=proj_list):
        print('Error getting data from Jama/Contour')
        return None
    return client

@cache.memoize()
def read_config(config):
    return config.read_config_file()

@cache.memoize()
def get_testplans_ui(config):
    return config.get_testplan_names()

@cache.memoize()
def get_project_and_testplan(config, testplan_ui_key):
    return config.get_project_and_testplan(testplan_ui_key)

@cache.memoize()
def get_testcycles(client, config, testplan_ui_key):
    project, testplan = get_project_and_testplan(config=config, testplan_ui_key=testplan_ui_key)
    if project is None or testplan is None:
        return []
    testcycles = [c for i,c in client.retrieve_testcycles(project_key=project, testplan_key=testplan)]
    if not len(testcycles) == 0:
        return [ALL_TEST_CYCLES, ] + testcycles

@cache.memoize()
def get_testcycle(testcycle_ui_key):
    return None if testcycle_ui_key == ALL_TEST_CYCLES else testcycle_ui_key


@cache.memoize()
def get_testruns(client, config, testplan_ui_key, testcycle_ui_key=None):
    project, testplan = config.get_project_and_testplan(testplan_ui_key=testplan_ui_key)
    if project is None or testplan is None:
        return None
    df = client.retrieve_testruns(project_key=project, testplan_key=testplan)
    testcycle = get_testcycle(testcycle_ui_key=testcycle_ui_key)
    if testcycle is not None:
        df1 = df[df.testcycle.eq(testcycle)]
        return df1
    return df

@cache.memoize()
def get_testgroups(client, config, testplan_ui_key, testcycle_ui_key=None):
    df = get_testruns(client=client, config=config, testplan_ui_key=testplan_ui_key, testcycle_ui_key=testcycle_ui_key)
    testgroups = [ALL_TEST_GROUPS, ] + [c for c in iter(df.testgroup.unique())]
    return testgroups

@cache.memoize()
def get_testgroup(testgroup_ui_key):
    return None if testgroup_ui_key == ALL_TEST_GROUPS else testgroup_ui_key

@cache.memoize()
def get_colormap(config):
    return config.get_colormap()

@cache.memoize()
def get_start_date(config):
    return config.get_start_date()

@cache.memoize()
def get_test_deadline(config):
    return config.get_test_deadline()



def get_app_layout():
    config = JamaReportsConfig()
    if read_config(config=config) is False:
        return html.Div('Invalid config file')

    testplans_ui= get_testplans_ui(config=config)
    if testplans_ui is None:
        return html.Div('No testplans found. Please check your config file')

    # call all config APIs to cache the results
    get_colormap(config=config)
    get_start_date(config=config)
    get_test_deadline(config=config)

    client = connect(config=config)
    if client is None:
        return html.Div('Unable to connect to Contour. Check credentials')

    initial_chart_type = next(iter(get_chart_types()))
    initial_testplan_ui = next(iter(testplans_ui))
    testcycles_ui = get_testcycles(client=client, config=config, testplan_ui_key=initial_testplan_ui)
    initial_testcycle_ui = next(iter(testcycles_ui))
    testgroups_ui = get_testgroups(client=client, config=config, testplan_ui_key=initial_testplan_ui, testcycle_ui_key=initial_testcycle_ui)
    initial_testgroup = next(iter(testgroups_ui))
    chart_types = get_chart_types()

    # get all test runs the first time so we can cache the results
    for t in testplans_ui:
        for c in get_testcycles(client=client, config=config, testplan_ui_key=t):
            get_testruns(client=client, config=config, testplan_ui_key=t, testcycle_ui_key=c)

    layout = html.Div([
        html.Div([
            html.P('Current Time: {}'.format(str(datetime.datetime.now()))),
            html.P(id='data-update-text'),
            html.Div([
                dcc.Dropdown(
                    id='id-test-plan',
                    options=[{'label': i, 'value': i} for i in testplans_ui],
                    value=initial_testplan_ui
                ),
            ],
            style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id='id-test-cycle',
                    options=[{'label': i, 'value': i} for i in testcycles_ui],
                    value=initial_testcycle_ui
                ),
            ],
            style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id='id-test-case',
                    options=[{'label': i, 'value': i} for i in testgroups_ui],
                    value=initial_testgroup
                ),
            ],
            style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id='id-chart-type',
                    options=[{'label': i, 'value': i} for i in chart_types],
                    value=initial_chart_type
                ),
            ],
            style={'width': '50%', 'display': 'inline-block'})
        ]),
        html.Div(id='chart-container'),
        dcc.Interval(
            id='interval-component',
            interval= 1 * 1000,  # in milliseconds
            n_intervals=0)
    ])
    return layout

app.layout = get_app_layout


@app.callback(Output('data-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_chart_data(n):
    print('In interval call back {}'.format(str(datetime.datetime.now())))
    return 'Last Updated: {}'.format(str(datetime.datetime.now()))


@cache.memoize()
def get_chart(testplan_ui, testcycle_ui, testgroup_ui, chart_type):
    config = JamaReportsConfig()
    client = jama_client()
    testcycle = get_testcycle(testcycle_ui_key=testcycle_ui)
    testgroup = get_testgroup(testgroup_ui_key=testgroup_ui)
    colormap = get_colormap(config=config)
    start_date = get_start_date(config=config)
    test_deadline = get_test_deadline(config=config)
    df = get_testruns(client=client, config=config, testplan_ui_key=testplan_ui)
    if df is None:
        return  None
    title = f'{chart_type} - {testplan_ui}'
    if testcycle is not None:
        title += f':{testcycle_ui}'
    if testgroup is not None:
        title += f':{testgroup_ui}'

    print(f'Creating charts for {title}...')

    if chart_type == FIG_TYPE_WEEKLY_STATUS_BAR_CHART:
        chart = \
            [get_weekly_status_bar_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                title=title,
                colormap=colormap)]

    if chart_type == FIG_TYPE_HISTORICAL_STATUS_LINE_CHART:
        chart = \
            [get_historical_status_line_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                start_date=start_date,
                test_deadline=test_deadline,
                title=title,
                colormap=colormap,
                treat_blocked_as_not_run=True,
                treat_inprogress_as_not_run=True)]

    if chart_type == FIG_TYPE_CURRENT_STATUS_PIE_CHART:
        chart = \
            [get_current_status_pie_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                title=title,
                colormap=colormap)]

    if chart_type == FIG_TYPE_CURRENT_RUNS_TABLE:
        chart = \
            [html.H6(title), get_current_week_testruns_table(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                title=title,
                colormap=colormap)]

    if chart_type == FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART:
        chart = \
            [get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, title=title,
                                           colormap=colormap, status_list=get_status_names())]

    if chart_type == FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART:
        chart = \
            [get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, title=title,
                                           colormap=colormap, status_list=['BLOCKED', 'FAILED'])]

    if chart_type == FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART:
        chart = \
            [get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, title=title,
                                           colormap=colormap, status_list=['NOT_RUN', 'INPROGRESS'])]

    return chart

@app.callback(
    [Output('id-test-cycle', 'options'),
     Output('id-test-cycle', 'value')],
    [Input('id-test-plan', 'value')]
)
def update_testcycle_options(testplan_ui):
    config = JamaReportsConfig()
    client = jama_client()
    testcycles = get_testcycles(client=client, config=config, testplan_ui_key=testplan_ui)
    testcycle = next(iter(testcycles))
    options = [{'label': i, 'value': i} for i in testcycles]
    return options, testcycle

@app.callback(
    [Output('id-test-case', 'options'),
     Output('id-test-case', 'value')],
    [Input('id-test-plan', 'value'),
    Input('id-test-cycle', 'value')]
)
def update_testgroup_options(testplan_ui, testcycle_ui):
    config = JamaReportsConfig()
    client = jama_client()
    testgroups = get_testgroups(client=client, config=config, testplan_ui_key=testplan_ui, testcycle_ui_key=testcycle_ui)
    testgroup = next(iter(testgroups))
    options = [{'label': i, 'value': i} for i in testgroups]
    return options, testgroup

@app.callback(
    Output('chart-container', 'children'),
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-test-case', 'value'),
     Input('id-chart-type', 'value')])
def update_graph(testplan_ui, testcycle_ui, testgroup_ui, chart_type):
    chart = get_chart(testplan_ui, testcycle_ui, testgroup_ui, chart_type)
    return chart

if __name__ == '__main__':
    app.run_server(debug=False)
