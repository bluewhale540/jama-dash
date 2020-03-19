import dash
import redis
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from flask_caching import Cache
from datetime import datetime as dt
from datetime import timedelta
from dateutil import parser
import os
from testrun_utils import get_testplan_labels, \
    get_testcycle_labels, \
    get_testgroup_labels,\
    get_testcycle_from_label, \
    json_to_df

import charts
from charts import get_chart_types, get_default_colormap
import redis_data

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

redis_inst = redis_data.get_redis_inst()

@cache.memoize()
def get_data():
    '''
    Retrieve the dataframe from Redis
    This dataframe is periodically updated through the redis task
    '''
    return redis_data.get_dataframe_json(redis_inst)


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
                        options=make_options(charts.get_chart_types()),
                        value=charts.FIG_TYPE_HISTORICAL_STATUS_LINE_CHART
                    ),
                ],
                style={'width': '50%', 'display': 'inline-block'}),
            ]),
            html.Div(id='id-controls-container-1',
                     children=[
                         html.Div('Start Date'),
                         dcc.DatePickerSingle(
                             id='id-start-date',
                             initial_visible_month=dt.today() - timedelta(days=90),
                     )],
                     style= {'display': 'none'}
            ),
            html.Div(id='id-controls-container-2',
                     children=[
                         html.Div('Test Deadline'),
                         dcc.DatePickerSingle(
                             id='id-test-deadline',
                             min_date_allowed=dt.today() + timedelta(days=1),
                             initial_visible_month=dt.today(),
                     )],
                     style= {'display': 'none'}
            ),
            dcc.Loading(
                id='id-loading',
                children=[
                    html.Div(id='id-chart')
                ],
                type='graph'
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
def update_graph(n, current_testplan, prev_date):
    if n is None:
        raise PreventUpdate
    last_updated = redis_data.get_updated_datetime(redis_inst)
    last_modified = redis_data.get_modified_datetime(redis_inst)
    if last_updated is None or last_modified is None:
        raise PreventUpdate

    first = False
    prev = None
    try:
        prev = parser.parse(prev_date)
    except Exception:
        first = True
    current = parser.parse(last_modified)
    if (prev is not None and current > prev) or first is True:
        if not first:
            app.logger.warning(f'Current data is from {prev_date}. '
                  f'Deleting caches to get data from '
                  f'data modified at {last_modified}')
        # invalidate caches
        cache.delete_memoized(get_data)
        cache.delete_memoized(get_testplan_options)
        cache.delete_memoized(get_testcycle_options)
        cache.delete_memoized(get_testgroup_options)
        cache.delete_memoized(get_chart)

    options = get_testplan_options()
    value = get_value_from_options(options, current_testplan)
    status = f'Data last updated:{last_updated}'
    return last_updated, status, options, value

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
    [Output('id-chart', 'children'),
     Output('id-controls-container-1', 'style'),
     Output('id-controls-container-2', 'style')],
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-test-group', 'value'),
     Input('id-chart-type', 'value'),
     Input('id-start-date', 'date'),
     Input('id-test-deadline', 'date')
     ])
def update_graph(testplan_ui, testcycle_ui, testgroup_ui, chart_type, date1, date2):
    start_date = parser.parse(date1) if date1 is not None else None
    test_deadline = parser.parse(date2) if date2 is not None else None
    df = json_to_df(get_data())
    chart = get_chart(df,
                      testplan_ui,
                      testcycle_ui,
                      testgroup_ui,
                      chart_type=chart_type,
                      colormap=get_default_colormap(),
                      start_date=start_date ,
                      test_deadline=test_deadline)
    style = {'display': 'none'}
    if chart_type == charts.FIG_TYPE_HISTORICAL_STATUS_LINE_CHART:
        style = {'display': 'inline-block'}
    return chart, style, style


if __name__ == '__main__':
    app.run_server(debug=True)
