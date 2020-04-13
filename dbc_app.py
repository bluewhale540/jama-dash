import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from flask_caching import Cache
from datetime import datetime as dt
from datetime import timedelta
from dateutil import parser

from testrun_utils import get_testplan_labels, \
    get_testcycle_labels, \
    get_testgroup_labels,\
    get_testcycle_from_label, \
    json_to_df

import charts
from charts import get_chart_types, get_default_colormap
import redis_data


CARD_TEST_PROGRESS='test_progress'
CARD_CURRENT_STATUS_OVERALL= 'current_status_overall'
CARD_CURRENT_STATUS_BY_GROUP='current_status_by_group'

ID_CHART_TEST_PROGRESS= 'id-chart-test-progress'
ID_CHART_CURRENT_STATUS_OVERALL= 'id-chart-current-status-overall'
ID_CHART_CURRENT_STATUS_BY_GROUP= 'id-chart-current-status-by-group'

ID_COLLAPSE_TEST_PROGRESS= 'id-collapse-test-progress'
ID_COLLAPSE_CURRENT_STATUS_OVERALL= 'id-collapse-current-status-overall'
ID_COLLAPSE_CURRENT_STATUS_BY_GROUP= 'id-collapse-current-status-by-group'



app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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

def get_selection_ui():
    testplans = get_testplan_options()
    initial_testplan = init_value(testplans)
    group1 = dbc.Col(
        [
            dbc.Label('select a test plan', html_for='id-test-plan'),
            dcc.Dropdown(
                id='id-test-plan',
                options=testplans,
                value=initial_testplan,
                persistence=True,
                persistence_type='local'
            ),
        ],
        lg=3
    )

    group2 = dbc.Col(
        [
            dbc.Label('select a test cycle', html_for='id-test-cycle'),
            dcc.Dropdown(
                id='id-test-cycle',
                persistence_type='local',
            ),
        ],
        lg=4
    )

    group3 = dbc.Col(
        [
            dbc.Label('select a test group', html_for='id-test-group'),
            dcc.Dropdown(
                id='id-test-group',
                persistence_type='local',
            ),
        ],
        lg=5
    )

    form = dbc.Row([group1, group2, group3])
    return form


def get_card_header(title, collapse_text='close', collapse_id=''):
    return dbc.CardHeader([
        dbc.Row([
            dbc.Col([html.H6(title, className='card-title')], width=10),
            dbc.Col([dbc.Button(collapse_text)], id=collapse_id, width=2)
        ])
    ])



def get_test_progress_ui():
    controls = dbc.Row([
        dbc.Col([dbc.Label('start date', html_for='id-start-date')], width=1),
        dbc.Col([dcc.DatePickerSingle(
            id='id-start-date',
            initial_visible_month=dt.today() - timedelta(days=90),
            persistence=True,
        )], width=2),
        dbc.Col([dbc.Label('test deadline', html_for='id-test-deadline')], width=1),
        dbc.Col([dcc.DatePickerSingle(
            id='id-test-deadline',
            min_date_allowed=dt.today() + timedelta(days=1),
            initial_visible_month=dt.today(),
            persistence=True,
            day_size=30
        )], width=2),
    ])
    chart = dbc.Row([dbc.Col(dcc.Loading(dcc.Graph(id=ID_CHART_TEST_PROGRESS)))])
    return dbc.Card([
        get_card_header('test progress', collapse_id=ID_COLLAPSE_TEST_PROGRESS),
        dbc.CardBody([
            controls,
            chart
        ])
    ])

def get_current_status_overall_ui():
    return dbc.Card([
        get_card_header('current status', collapse_id=ID_COLLAPSE_CURRENT_STATUS_OVERALL),
        dbc.CardBody(dcc.Loading(dcc.Graph(id=ID_CHART_CURRENT_STATUS_OVERALL))),
    ])

def get_current_status_by_group_ui():
    return dbc.Card([
        get_card_header('current status (by group)', collapse_id=ID_COLLAPSE_CURRENT_STATUS_BY_GROUP),
        dbc.CardBody(dcc.Loading(dcc.Graph(id=ID_CHART_CURRENT_STATUS_BY_GROUP))),
    ])


supported_cards = {
    CARD_TEST_PROGRESS: dict(
        title='test progress',
        chart_id=ID_CHART_TEST_PROGRESS,
        collapse_id=ID_COLLAPSE_TEST_PROGRESS,
        chart_type=charts.FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
        layout_func=get_test_progress_ui
    ),
    CARD_CURRENT_STATUS_OVERALL: dict(
        title='current status (overall)',
        chart_id=ID_CHART_CURRENT_STATUS_OVERALL,
        collapse_id=ID_COLLAPSE_CURRENT_STATUS_OVERALL,
        chart_type=charts.FIG_TYPE_CURRENT_STATUS_PIE_CHART,
        layout_func=get_current_status_overall_ui
    ),
    CARD_CURRENT_STATUS_BY_GROUP: dict(
        title='current status (by test group)',
        chart_id=ID_CHART_CURRENT_STATUS_BY_GROUP,
        collapse_id=ID_COLLAPSE_CURRENT_STATUS_BY_GROUP,
        chart_type=charts.FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART,
        layout_func=get_current_status_by_group_ui
    ),
}


def serve_layout():
    testplans = get_testplan_options()
    initial_testplan = init_value(testplans)
    testcycles = get_testcycle_options(initial_testplan)
    initial_testcycle = init_value(testcycles)
    testgroups = get_testgroup_options(testplan=initial_testplan, testcycle=initial_testcycle)
    initial_testgroup = init_value(testgroups)
    modified_datetime = redis_data.get_modified_datetime(redis_inst)

    layout = dbc.Container(
        [
            html.A(
                [
                    html.Img(
                        src='https://www.idirect.net/wp-content/uploads/2018/10/logo-color.svg',
                        style={
                            'height': '50px',
                            'width': '200px',
                            'float': 'left',
                            'position': 'relative',
                            'padding-top': 0,
                            'padding-right': '20px',
                            'display': 'inline-block'
                        }
                    )
                ],
                href='https://www.idirect.net'
            ),
            html.H2(
                'Test Execution Reports',
                style={
                    'color': 'blue',
                    'font-weight': 'normal',
                    'height': '50px',
                    'display': 'inline-block'
                }
            ),
            html.Hr(),
            dbc.CardHeader(get_selection_ui()),
            dbc.Row([
                dbc.Col(get_test_progress_ui(), width=12, style=dict(height='100%')),
            ]),
            dbc.Row([
                dbc.Col(get_current_status_overall_ui(), width=12, style=dict(height='100%'))
            ]),
            dbc.Row([
                dbc.Col(get_current_status_by_group_ui(), width=12, style=dict(height='100%'))
            ]),
            dbc.CardFooter([
                html.Div(id='id-status', children=f'Data last updated: {modified_datetime}')
            ]),
            dcc.Interval(interval=1 * 60 * 1000, id='id-interval'),
            # Hidden div inside the app that stores last updated date and time
            html.Div(id='id-last-modified-hidden', children=modified_datetime, style={'display': 'none'}),

        ]
    )
    return layout


app.layout = serve_layout()


@app.callback(
    Output('id-last-modified-hidden', 'children'),
    [Input('id-interval', 'n_intervals')],
    [State('id-last-modified-hidden', 'children')]
)
def update_last_modified(n, prev_last_modified):
    if n is None:
        # TODO: When is this callback called with n == None
        raise PreventUpdate

    last_modified = redis_data.get_modified_datetime(redis_inst)
    if last_modified is None:
        # no data in Redis. TODO: Need to handle differently?
        raise PreventUpdate

    first_time = False
    prev_datetime = None
    if prev_last_modified is None:
        first_time = True
    else:
        try:
            prev_datetime = parser.parse(prev_last_modified)
        except Exception:
            # TODO: could be badly formatted date?
            # assume first time for now
            first_time = True
    current_datetime = parser.parse(last_modified)
    if (prev_datetime is not None and current_datetime > prev_datetime) or first_time is True:
        if first_time:
            app.logger.warning('Data in server found. Last modified: {last_modified}')
        else:
            app.logger.warning(f'Current data is from {prev_last_modified}. '
                  f'Deleting caches to get data from '
                  f'data modified at {last_modified}')
        return last_modified
    else:
        raise PreventUpdate



@app.callback(
    [Output('id-status', 'children'),
    Output('id-test-plan', 'options'),
    Output('id-test-plan', 'value')],
    [Input('id-last-modified-hidden', 'children')],
    [State('id-test-plan', 'value')]
)
def update_graph(modified_datetime, current_testplan):
    if modified_datetime is None:
        raise PreventUpdate
    # invalidate caches
    cache.delete_memoized(get_data)
    cache.delete_memoized(get_testplan_options)
    cache.delete_memoized(get_testcycle_options)
    cache.delete_memoized(get_testgroup_options)
    cache.delete_memoized(get_chart)
    options = get_testplan_options()
    value = get_value_from_options(options, current_testplan)
    status = f'Data was last updated at:{modified_datetime}'
    return status, options, value


@app.callback(
    [Output('id-test-cycle', 'options'),
     Output('id-test-cycle', 'value'),
     Output('id-test-cycle', 'persistence')],
    [Input('id-test-plan', 'value')],
    [State('id-test-cycle', 'value')]
)
def update_testcycle_options(testplan_ui, current_value):
    options = get_testcycle_options(testplan=testplan_ui)
    value = get_value_from_options(options, current_value)
    return [options, value, testplan_ui]

@app.callback(
    [Output('id-test-group', 'options'),
     Output('id-test-group', 'value'),
     Output('id-test-group', 'persistence')],
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value')],
    [State('id-test-group', 'value')]
)
def update_testgroup_options(testplan_ui, testcycle_ui, current_value):
    options = get_testgroup_options(testplan=testplan_ui, testcycle=testcycle_ui)
    value = get_value_from_options(options, current_value)
    persistence = testcycle_ui
    return [options, value, persistence]

@app.callback(
    [Output(ID_CHART_TEST_PROGRESS, 'figure'),
     Output(ID_CHART_CURRENT_STATUS_OVERALL, 'figure'),
     Output(ID_CHART_CURRENT_STATUS_BY_GROUP, 'figure')],
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-test-group', 'value'),
     Input('id-start-date', 'date'),
     Input('id-test-deadline', 'date')
     ])
def update_graph(testplan_ui, testcycle_ui, testgroup_ui, date1, date2):
    start_date = parser.parse(date1) if date1 is not None else None
    test_deadline = parser.parse(date2) if date2 is not None else None
    df = json_to_df(get_data())
    chart1 = get_chart(df,
                      testplan_ui,
                      testcycle_ui,
                      testgroup_ui,
                      chart_type=charts.FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
                      colormap=get_default_colormap(),
                      start_date=start_date ,
                      test_deadline=test_deadline)
    chart2 = get_chart(df,
                      testplan_ui,
                      testcycle_ui,
                      testgroup_ui,
                      chart_type=charts.FIG_TYPE_CURRENT_STATUS_PIE_CHART,
                      colormap=get_default_colormap(),
                      start_date=start_date ,
                      test_deadline=test_deadline)
    chart3 = get_chart(df,
                      testplan_ui,
                      testcycle_ui,
                      testgroup_ui,
                      chart_type=charts.FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART,
                      colormap=get_default_colormap(),
                      start_date=start_date ,
                      test_deadline=test_deadline)
    return [chart1, chart2, chart3]


if __name__ == '__main__':
    app.run_server(debug=True)
