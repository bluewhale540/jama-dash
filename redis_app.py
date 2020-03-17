import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from flask_caching import Cache
import redis
from dateutil import parser
import os
from testrun_utils import get_testplan_labels, \
    get_testcycle_labels, \
    get_testgroup_labels,\
    get_testcycle_from_label, \
    json_to_df

import charts
from charts import get_chart_types, get_default_colormap
import redis_params

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


server = app.server

# initialize the data when the app starts
#tasks.update_data()

redis_instance = redis.StrictRedis.from_url(os.environ['REDIS_URL'])

FIG_TYPE_WEEKLY_STATUS_BAR_CHART = 'Weekly Status'
FIG_TYPE_HISTORICAL_STATUS_LINE_CHART = 'Historical Status'
FIG_TYPE_CURRENT_STATUS_PIE_CHART = 'Current Status'
FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART = 'Current Status By Test Group'
FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART = 'Test Groups with Blocked/Failed Runs'
FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART = 'Test Groups with Not Run/In Progress Runs'
FIG_TYPE_CURRENT_RUNS_TABLE = 'Test Runs For Current Week'

def get_chart_types():
    chart_types = [
        FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
        FIG_TYPE_WEEKLY_STATUS_BAR_CHART,
        FIG_TYPE_CURRENT_STATUS_PIE_CHART,
        FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART,
        FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART,
        FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART,
        FIG_TYPE_CURRENT_RUNS_TABLE
    ]
    return chart_types

@cache.memoize()
def get_data():
    '''Retrieve the dataframe from Redis
    This dataframe is periodically updated through the redis task
    '''
    jsonified_df = redis_instance.hget(
        redis_params.REDIS_HASH_NAME, redis_params.REDIS_DATASET_KEY
    ).decode('utf-8')
    return jsonified_df

init_value = lambda a: a[0]['value'] if len(a) > 0 and 'value' in a[0] else None
make_options = lambda lst: [{'label': i, 'value': i} for i in lst]


def get_value_from_options(options, current_value=None):
    if current_value is None:
        return init_value(options)
    for opt in options:
        value = opt.get('value')
        if current_value == value:
            return current_value
    return init_value(options)

# get testplans and first value
@cache.memoize()
def get_testplan_options():
    df = json_to_df(get_data())
    testplans =  [{'label': i, 'value': i} for i in get_testplan_labels(df)]
    return testplans

# get testplans and first value
@cache.memoize()
def get_testcycle_options(testplan):
    df = json_to_df(get_data())
    testcycles = [{'label': i, 'value': i}
                   for i in get_testcycle_labels(df, testplan_key=testplan)]
    return testcycles

# get testplans and first value
@cache.memoize()
def get_testgroup_options(testplan, testcycle):
    df = json_to_df(get_data())
    testgroups = [{'label': i, 'value': i}
                   for i in get_testgroup_labels(df,
                                                 testplan_key=testplan,
                                                 testcycle_key=get_testcycle_from_label(testcycle))]
    return testgroups

@cache.memoize()
def get_chart(df, testplan_ui, testcycle_ui, testgroup_ui, chart_type, colormap, start_date, test_deadline):
    return charts.get_chart(
        df, testplan_ui, testcycle_ui, testgroup_ui, chart_type, colormap, start_date, test_deadline)

def serve_layout():
    testplans = get_testplan_options()
    initial_testplan = init_value(testplans)
    testcycles = get_testcycle_options(initial_testplan)
    initial_testcycle = init_value(testcycles)
    testgroups = get_testgroup_options(testplan=initial_testplan, testcycle=initial_testcycle)
    initial_testgroup = init_value(testgroups)
    return html.Div(
        [
            dcc.Interval(interval=1 * 60 * 1000, id='id-interval'),
            # Hidden div inside the app that stores last updated date and time
            html.Div(id='id-last-update-hidden', style={'display': 'none'}),
            html.H1('iDirect Test Reports'),
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id='id-test-plan',
                        options=testplans,
                        value=initial_testplan
                    ),
                ],
                style={'width': '50%', 'display': 'inline-block'}),
                html.Div([
                    dcc.Dropdown(
                        id='id-test-cycle',
                        options=testcycles,
                        value=initial_testcycle
                    ),
                ],
                style={'width': '50%', 'display': 'inline-block'}),
                html.Div([
                    dcc.Dropdown(
                        id='id-test-group',
                        options=testgroups,
                        value=initial_testgroup
                    ),
                ],
                style={'width': '50%', 'display': 'inline-block'}),
                html.Div([
                    dcc.Dropdown(
                        id='id-chart-type',
                        options=make_options(get_chart_types()),
                        value=FIG_TYPE_HISTORICAL_STATUS_LINE_CHART
                    ),
                ],
                style={'width': '50%', 'display': 'inline-block'}),
            ]),
            dcc.Loading(
                id='id-loading',
                children=[
                    html.Div(id='id-chart')
                ],
                type='graph',
            ),
            html.Div(id='id-status'),
        ]
    )


app.layout = serve_layout()

@app.callback(
    [Output('id-last-update-hidden', 'children'),
     Output('id-status', 'children'),
    Output('id-test-plan', 'options'),
    Output('id-test-plan', 'value')],
    [Input('id-interval', 'n_intervals')],
    [State('id-test-plan', 'value'),
     State('id-last-update-hidden', 'children')]
)
def update_graph(_, current_testplan, prev_date):
    data_last_updated = redis_instance.hget(
        redis_params.REDIS_HASH_NAME, redis_params.REDIS_UPDATED_KEY
    ).decode('utf-8')
    first = False
    prev = None
    try:
        prev = parser.parse(prev_date)
    except Exception:
        first = True
    current = parser.parse(data_last_updated)
    if (prev is not None and current > prev) or first is True:
        if not first:
            print(f'Data is from prev update at {prev_date}. '
                  f'Deleting caches to get data from '
                  f'current update at {data_last_updated}')
        # invalidate caches
        cache.delete_memoized(get_data)
        cache.delete_memoized(get_testplan_options)
        cache.delete_memoized(get_testcycle_options)
        cache.delete_memoized(get_testgroup_options)
        cache.delete_memoized(get_chart)

    options = get_testplan_options()
    value = get_value_from_options(options, current_testplan)
    status = f'Data last updated:{data_last_updated}'
    return data_last_updated, status, options, value

@app.callback(
    [Output('id-test-cycle', 'options'),
     Output('id-test-cycle', 'value')],
    [Input('id-test-plan', 'value')],
    [State('id-test-cycle', 'value')]
)
def update_testcycle_options(testplan_ui, current_value):
    options = get_testcycle_options(testplan=testplan_ui)
    value = get_value_from_options(options, current_value)
    return options, value


@app.callback(
    [Output('id-test-group', 'options'),
     Output('id-test-group', 'value')],
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value')],
    [State('id-test-group', 'value')]
)
def update_testgroup_options(testplan_ui, testcycle_ui, current_value):
    options = get_testgroup_options(testplan=testplan_ui, testcycle=testcycle_ui)
    value = get_value_from_options(options, current_value)
    return options, value

@app.callback(
    [Output('id-chart', 'children')],
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-test-group', 'value'),
     Input('id-chart-type', 'value')])
def update_graph(testplan_ui, testcycle_ui, testgroup_ui, chart_type):
    df = json_to_df(get_data())
    chart = get_chart(df,
                      testplan_ui,
                      testcycle_ui,
                      testgroup_ui,
                      chart_type=chart_type,
                      colormap=get_default_colormap(),
                      start_date=parser.parse('Feb 1 2020') ,
                      test_deadline=parser.parse('Mar 13 2020'))
    return chart


if __name__ == '__main__':
    app.run_server(debug=False)
