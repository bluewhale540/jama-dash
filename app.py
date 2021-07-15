import os
from datetime import datetime
from jama_client import jama_client
import login_dialog
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from weekly_status import get_weekly_status_bar_chart
from historical_status import get_historical_status_line_chart
from current_status import get_current_status_pie_chart, get_testgroup_status_bar_chart
from testrun_utils import get_status_names, JamaReportsConfig
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
with app.server.app_context():
    cache.clear()

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
'''
@cache.memoize()
'''
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

    proj_list = config.get_projects()

    client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
    if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, project_list=proj_list):
        print('Error getting data from Jama/Contour')
        return None
    return client

def read_config(config):
    return config.read_config_file()

'''
@cache.memoize()
'''
def get_testplans_ui(config):
    return config.get_testplan_names()

'''
@cache.memoize()
'''
def get_project_and_testplan(config, testplan_ui_key):
    return config.get_project_and_testplan(testplan_ui_key)

'''
@cache.memoize()
'''
def get_testcycles(client, config, testplan_ui_key):
    project, testplan = get_project_and_testplan(config=config, testplan_ui_key=testplan_ui_key)
    if project is None or testplan is None:
        return []
    testcycles = [c for i,c in client.retrieve_testcycles(project_key=project, testplan_key=testplan)]
    if not len(testcycles) == 0:
        return [ALL_TEST_CYCLES, ] + testcycles

'''
@cache.memoize()
'''
def get_testcycle(testcycle_ui_key):
    return None if testcycle_ui_key == ALL_TEST_CYCLES else testcycle_ui_key

'''
@cache.memoize()
'''
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

'''
@cache.memoize()
'''
def get_testgroups(client, config, testplan_ui_key, testcycle_ui_key=None):
    df = get_testruns(client=client, config=config, testplan_ui_key=testplan_ui_key, testcycle_ui_key=testcycle_ui_key)
    testgroups = [ALL_TEST_GROUPS, ] + [c for c in iter(df.testgroup.unique())]
    return testgroups

'''
@cache.memoize()
'''
def get_testgroup(testgroup_ui_key):
    return None if testgroup_ui_key == ALL_TEST_GROUPS else testgroup_ui_key

'''
@cache.memoize()
'''
def get_colormap(config):
    return config.get_colormap()

'''
@cache.memoize()
'''
def get_start_date(config):
    return config.get_start_date()

'''
@cache.memoize()
'''
def get_test_deadline(config):
    return config.get_test_deadline()

config = JamaReportsConfig()
if read_config(config=config) is False:
    exit(1)

client = connect(config=config)
if client is None:
    exit(1)

testplans_ui_global = get_testplans_ui(config=config)
# get all test runs the first time so we can cache the results
for t in testplans_ui_global:
    for c in get_testcycles(client=client, config=config, testplan_ui_key=t):
        get_testruns(client=client, config=config, testplan_ui_key=t, testcycle_ui_key=c)

# call all config APIs to cache the results
get_colormap(config=config)
get_start_date(config=config)
get_test_deadline(config=config)


def get_app_layout():
    testplans_ui = get_testplans_ui(config=config)
    initial_testplan_ui = next(iter(testplans_ui))
    testcycles_ui = get_testcycles(client=client, config=config, testplan_ui_key=initial_testplan_ui)
    initial_testcycle_ui = next(iter(testcycles_ui))
    testgroups_ui = get_testgroups(client=client, config=config,
                                   testplan_ui_key=initial_testplan_ui,
                                   testcycle_ui_key=initial_testcycle_ui)
    initial_testgroup = next(iter(testgroups_ui))
    chart_types = get_chart_types()
    initial_chart_type = next(iter(get_chart_types()))


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
                    id='id-test-group',
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
        html.Div(id='id-updated-time'),
        dcc.Interval(
            id='id-interval',
            interval= 60 * 1000,  # in milliseconds
            n_intervals=0)
    ])
    return layout

app.layout = get_app_layout

@app.callback(Output('id-updated-time', 'children'),
              [Input('id-interval', 'n_intervals')],
              [State('id-test-plan', 'value'),
               State('id-test-cycle', 'value'),
               State('id-test-group', 'value')])
def update_chart_data(n, testplan, testcycle, tesgroup):

    if n == 0:
        return [html.Span('Initial Data')]
    for t in testplans_ui_global:
        project, testplan = config.get_project_and_testplan(testplan_ui_key=t)
        if project is None or testplan is None:
            return 'Project or Testplan missing in config'
        client.retrieve_testruns(project_id=project, testplan_key=testplan, update=True)
    #cache.delete_memoized(get_testruns)
    #cache.delete_memoized(get_chart)
    update_text = 'Last Updated: {} - Refresh to see updates'.format(datetime.now().strftime('%m-%d-%Y %H:%M:%S'))
    return [html.Span(update_text)]

'''
@cache.memoize()
'''
def get_chart(testplan_ui, testcycle_ui, testgroup_ui, chart_type):
    print('In Get chart: {}'.format(str(datetime.now().strftime('%M %d-%Y %H:%M:%S'))))
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
                priority=None,
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
                df1=df,
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
    [Input('id-test-plan', 'value')],
    [State('id-test-cycle', 'value')]
)
def update_testcycle_options(testplan_ui, current_test_cycle):
    testcycles = get_testcycles(client=client, config=config, testplan_ui_key=testplan_ui)
    testcycle = current_test_cycle
    if current_test_cycle not in testcycles:
        testcycle = next(iter(testcycles))
    options = [{'label': i, 'value': i} for i in testcycles]
    return options, testcycle

@app.callback(
    [Output('id-test-group', 'options'),
     Output('id-test-group', 'value')],
    [Input('id-test-plan', 'value'),
    Input('id-test-cycle', 'value')]
)
def update_testgroup_options(testplan_ui, testcycle_ui):
    testgroups = get_testgroups(client=client, config=config, testplan_ui_key=testplan_ui, testcycle_ui_key=testcycle_ui)
    testgroup = next(iter(testgroups))
    options = [{'label': i, 'value': i} for i in testgroups]
    return options, testgroup

@app.callback(
    [Output('chart-container', 'children')],
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-test-group', 'value'),
     Input('id-chart-type', 'value')])
def update_graph(testplan_ui, testcycle_ui, testgroup_ui, chart_type):
    chart = get_chart(testplan_ui, testcycle_ui, testgroup_ui, chart_type)
    return chart

if __name__ == '__main__':
    app.run_server(debug=False)
