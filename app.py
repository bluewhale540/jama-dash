
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
from testrun_utils import get_status_names
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




def read_config_file():
    config_file_name = 'jama-report-config.json'
    config_file = None
    for settings_dir in [expanduser('~'), '.']:
        path = settings_dir + '/' + config_file_name
        if isfile(path):
            config_file = path
            print(f'settings file {path} found!')
            break

    if config_file is None:
        print(f'settings file {config_file_name} not found!')
        exit(1)

    try:
        with open(config_file) as f:
            config = json.load(f)
    except json.decoder.JSONDecodeError as e:
        print(f'Settings file {config_file} has invalid format')
        print(f'{e}')
        return None
    except Exception as e:
        print(f'Error opening settings file {config_file}')
        print(f'{e}')
        return None
    return config

config = read_config_file()
if config is None:
    exit(1)

testplan_list = config.get('testplans')
if testplan_list is None:
    print('No testplans listed in config. Exiting!')
    exit(1)

colormap = None
chart_settings = config.get('chartSettings')
if chart_settings is not None:
    colormap = chart_settings.get('colormap')

dt = chart_settings.get('testStart')
start_date = parser.parse(dt) if dt is not None else None
dt = chart_settings.get('testDeadline')
test_deadline = parser.parse(dt) if dt is not None else None


proj_list = [x['project'] for x in testplan_list]

client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, projkey_list=proj_list):
    exit(1)

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

def get_testplans_ui():
    testplans_ui = []
    for t in testplan_list:
        display_name = t.get('displayName')
        if display_name is not None:
            testplans_ui.append(display_name)
    return testplans_ui

@cache.memoize()
def get_project_and_testplan(testplan_ui_key):
    for t in testplan_list:
        project = t.get('project')
        if project is None:
            print('Missing \'project\' field under testplan in config. Skipping...')
            continue
        testplan = t.get('name')
        if project is None:
            print('Missing testplan name in config. Skipping...')
            continue
        title = t.get('displayName')
        if title is None:
            title = project + ':' + testplan
        if title == testplan_ui_key:
            return project, testplan
    return None, None



@cache.memoize()
def get_testcycles(testplan_ui_key):
    project, testplan = get_project_and_testplan(testplan_ui_key=testplan_ui_key)
    if project is None or testplan is None:
        return []
    testcycles = [c for i,c in client.retrieve_testcycles(project_key=project, testplan_key=testplan)]
    if not len(testcycles) == 0:
        return [ALL_TEST_CYCLES, ] + testcycles

@cache.memoize()
def get_testcycle(testcycle_ui_key):
    return None if testcycle_ui_key == ALL_TEST_CYCLES else testcycle_ui_key


@cache.memoize()
def get_testruns(testplan_ui_key, testcycle_ui_key=None):
    project, testplan = get_project_and_testplan(testplan_ui_key=testplan_ui_key)
    if project is None or testplan is None:
        return None
    df = client.retrieve_testruns(project_key=project, testplan_key=testplan)
    testcycle = get_testcycle(testcycle_ui_key=testcycle_ui_key)
    if testcycle is not None:
        df1 = df[df.testcycle.eq(testcycle)]
        return df1
    return df


@cache.memoize()
def get_testgroups(testplan_ui_key, testcycle_ui_key=None):
    df = get_testruns(testplan_ui_key=testplan_ui_key, testcycle_ui_key=testcycle_ui_key)
    testgroups = [ALL_TEST_GROUPS, ] + [c for c in iter(df.testgroup.unique())]
    return testgroups

@cache.memoize()
def get_testgroup(testgroup_ui_key):
    return None if testgroup_ui_key == ALL_TEST_GROUPS else testgroup_ui_key


def get_app_layout():
    testplans_ui = get_testplans_ui()
    # get all test runs the first time
    for t in testplans_ui:
        get_testruns(testplan_ui_key=t)
    initial_chart_type = next(iter(get_chart_types()))
    initial_testplan_ui = next(iter(testplans_ui))
    testcycles_ui = get_testcycles(testplan_ui_key=initial_testplan_ui)
    initial_testcycle_ui = next(iter(testcycles_ui))
    testgroups_ui = get_testgroups(testplan_ui_key=initial_testplan_ui, testcycle_ui_key=initial_testcycle_ui)
    initial_testgroup = next(iter(testgroups_ui))
    chart_types = get_chart_types()

    layout = html.Div([
        html.Div([
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
        html.P('Current Time: {}'.format(str(datetime.datetime.now()))),
        html.P(id='data-update-text'),
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
    testcycle = get_testcycle(testcycle_ui)
    testgroup = get_testgroup(testgroup_ui)
    df = get_testruns(testplan_ui)
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
    testcycles = get_testcycles(testplan_ui_key=testplan_ui)
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
    testgroups = get_testgroups(testplan_ui_key=testplan_ui, testcycle_ui_key=testcycle_ui)
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
