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

ID_DROPDOWN_TEST_PLAN='id-dropdown-test-plan'
ID_DROPDOWN_TEST_CYCLE='id-dropdown-test-cycle'
ID_DROPDOWN_TEST_GROUP='id-dropdown-test-group'
ID_DATE_PICKER_START_DATE='id-date-test-progress-start-date'
ID_DATE_PICKER_DEADLINE='id-date-test-progress-deadline'
ID_CHECKLIST_TEST_PROGRESS_OPTIONS='id-checklist-test-progress-options'
ID_CHECKLIST_CURRENT_STATUS_BY_GROUP_OPTIONS='id-checklist-current-by-group-options'
ID_CHECKLIST_TEST_RUNS_OPTIONS='id-checklist-test-runs-options'

# checklist options for the test progress card
CHECKLIST_LABEL_BLOCKED_NOT_RUN='blocked as not run'
CHECKLIST_LABEL_INPROGRESS_NOT_RUN='in progress as not run'
CHECKLIST_VALUE_BLOCKED_NOT_RUN='treat_blocked_as_not_run'
CHECKLIST_VALUE_INPROGRESS_NOT_RUN='treat_inprogress_as_not_run'

test_progress_options = [
    dict(label=CHECKLIST_LABEL_BLOCKED_NOT_RUN, value=CHECKLIST_VALUE_BLOCKED_NOT_RUN),
    dict(label=CHECKLIST_LABEL_INPROGRESS_NOT_RUN, value=CHECKLIST_VALUE_INPROGRESS_NOT_RUN),
]

# checklist options for the test progress card
CHECKLIST_LABEL_SHOW_NOT_RUN='not run'
CHECKLIST_LABEL_SHOW_IN_PROGRESS='in progress'
CHECKLIST_LABEL_SHOW_BLOCKED='blocked'
CHECKLIST_LABEL_SHOW_PASSED='passed'
CHECKLIST_LABEL_SHOW_FAILED='failed'
CHECKLIST_VALUE_SHOW_NOT_RUN='show_not_run'
CHECKLIST_VALUE_SHOW_IN_PROGRESS='show_in_progress'
CHECKLIST_VALUE_SHOW_BLOCKED='show_blocked'
CHECKLIST_VALUE_SHOW_PASSED='show_passed'
CHECKLIST_VALUE_SHOW_FAILED='show_failed'

current_status_by_group_options = [
    dict(label=CHECKLIST_LABEL_SHOW_NOT_RUN, value=CHECKLIST_VALUE_SHOW_NOT_RUN),
    dict(label=CHECKLIST_LABEL_SHOW_IN_PROGRESS, value=CHECKLIST_VALUE_SHOW_IN_PROGRESS),
    dict(label=CHECKLIST_LABEL_SHOW_BLOCKED, value=CHECKLIST_VALUE_SHOW_BLOCKED),
    dict(label=CHECKLIST_LABEL_SHOW_PASSED, value=CHECKLIST_VALUE_SHOW_PASSED),
    dict(label=CHECKLIST_LABEL_SHOW_FAILED, value=CHECKLIST_VALUE_SHOW_FAILED),
]

# checklist options for the test runs table card
CHECKLIST_LABEL_SHOW_CURRENT_WEEK='show test runs scheduled for current week'
CHECKLIST_VALUE_SHOW_CURRENT_WEEK='current_week'

test_runs_table_options = [
    dict(label=CHECKLIST_LABEL_SHOW_CURRENT_WEEK, value=CHECKLIST_VALUE_SHOW_CURRENT_WEEK)
]


ID_CARD_TEST_PROGRESS='id-card-test-progress'
ID_CARD_CURRENT_STATUS_OVERALL='id-card-current-status-overall'
ID_CARD_CURRENT_STATUS_BY_GROUP='id-card-current-status-by-group'
ID_CARD_TEST_RUNS_TABLE='id-card-test-runs-table'
ID_CARD_WEEKLY_STATUS='id-card-weekly-status'

ID_CHART_TEST_PROGRESS= 'id-chart-test-progress'
ID_CHART_CURRENT_STATUS_OVERALL= 'id-chart-current-status-overall'
ID_CHART_CURRENT_STATUS_BY_GROUP= 'id-chart-current-status-by-group'
ID_CHART_TEST_RUNS_TABLE='id-chart-test-runs-table'
ID_CHART_WEEKLY_STATUS='id-chart-weekly-status'

ID_COLLAPSE_TEST_PROGRESS= 'id-collapse-test-progress'
ID_COLLAPSE_CURRENT_STATUS_OVERALL= 'id-collapse-current-status-overall'
ID_COLLAPSE_CURRENT_STATUS_BY_GROUP= 'id-collapse-current-status-by-group'
ID_COLLAPSE_TEST_RUNS_TABLE='id-collapse-test-runs-table'
ID_COLLAPSE_WEEKLY_STATUS='id-collapse-weekly-status'

ID_COLLAPSE_BUTTON_TEST_PROGRESS= 'id-collapse-button-test-progress'
ID_COLLAPSE_BUTTON_CURRENT_STATUS_OVERALL= 'id-collapse-button-current-status-overall'
ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_GROUP= 'id-collapse-button-current-status-by-group'
ID_COLLAPSE_BUTTON_TEST_RUNS_TABLE='id-collapse-button-test-runs-table'
ID_COLLAPSE_BUTTON_WEEKLY_STATUS='id-collapse-button-weekly-status'

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
def get_chart(df, testplan_ui, testcycle_ui, testgroup_ui, chart_type, colormap, **kwargs):
    return charts.get_chart(
        df, testplan_ui, testcycle_ui, testgroup_ui, chart_type, colormap, **kwargs)

def get_selection_ui():
    testplans = get_testplan_options()
    initial_testplan = init_value(testplans)
    group1 = dbc.Col(
        [
            dbc.Label('select a test plan', html_for=ID_DROPDOWN_TEST_PLAN),
            dcc.Dropdown(
                id=ID_DROPDOWN_TEST_PLAN,
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
            dbc.Label('select a test cycle', html_for=ID_DROPDOWN_TEST_CYCLE),
            dcc.Dropdown(
                id=ID_DROPDOWN_TEST_CYCLE,
                persistence_type='local',
            ),
        ],
        lg=4
    )

    group3 = dbc.Col(
        [
            dbc.Label('select a test group', html_for=ID_DROPDOWN_TEST_GROUP),
            dcc.Dropdown(
                id=ID_DROPDOWN_TEST_GROUP,
                persistence_type='local',
            ),
        ],
        lg=5
    )

    form = dbc.Row([group1, group2, group3])
    return form



def get_test_progress_controls():
    controls = dbc.Row([
        dbc.Col(
            dbc.FormGroup([
                dbc.Label('start date', html_for=ID_DATE_PICKER_START_DATE),
                dcc.DatePickerSingle(
                    id=ID_DATE_PICKER_START_DATE,
                    initial_visible_month=dt.today() - timedelta(days=90),
                    persistence=True,
                )
            ]), width=2
        ),
        dbc.Col(
            dbc.FormGroup([
                dbc.Label('test deadline', html_for=ID_DATE_PICKER_DEADLINE),
                dcc.DatePickerSingle(
                    id=ID_DATE_PICKER_DEADLINE,
                    min_date_allowed=dt.today() + timedelta(days=1),
                    initial_visible_month=dt.today(),
                    persistence=True,
                    day_size=30
                )
            ]), width=2
        ),
        dbc.Col(
            dbc.FormGroup([
                dbc.Label('options', html_for=ID_CHECKLIST_TEST_PROGRESS_OPTIONS),
                dcc.Checklist(
                    id=ID_CHECKLIST_TEST_PROGRESS_OPTIONS,
                    options=test_progress_options,
                    value=[CHECKLIST_VALUE_BLOCKED_NOT_RUN, CHECKLIST_VALUE_INPROGRESS_NOT_RUN],
                    labelStyle={'display': 'block'},
                    inputStyle={'margin-right': '5px'}
                )
            ]),
        ),
    ])
    return controls


def get_current_status_by_group_controls():
    controls = dbc.Row([
        dbc.Col(
            dbc.FormGroup([
                dbc.Label('select traces to show', html_for=ID_CHECKLIST_CURRENT_STATUS_BY_GROUP_OPTIONS),
                dcc.Checklist(
                    id=ID_CHECKLIST_CURRENT_STATUS_BY_GROUP_OPTIONS,
                    options=current_status_by_group_options,
                    value=[CHECKLIST_VALUE_SHOW_BLOCKED, CHECKLIST_VALUE_SHOW_FAILED],
                    labelStyle={'display': 'block'},
                    inputStyle={'margin-right': '5px'},
                )
            ])
        ),
    ])
    return controls

def get_test_runs_controls():
    controls = dbc.Row([
        dbc.Col(
            dbc.FormGroup([
                dcc.Checklist(
                    id=ID_CHECKLIST_TEST_RUNS_OPTIONS,
                    options=test_runs_table_options,
                    value=[],
                    labelStyle={'display': 'block'},
                    inputStyle={'margin-right': '5px'},
                )
            ])
        ),
    ])
    return controls


CARD_KEY_TITLE='title'
CARD_KEY_OBJ_TYPE='type' # graph or table
CARD_KEY_CHART_ID='chart_id'
CARD_KEY_COLLAPSE_ID='collapse_id'
CARD_KEY_COLLAPSE_BUTTON_ID='collapse_button_id'
CARD_KEY_COLLAPSE_INITIAL_STATE='collapse_initial_state' # open=True, collapsed=False
CARD_KEY_CHART_TYPE='chart_type'
CARD_KEY_CONTROLS_LAYOUT_FUNC='controls_layout_func'
CARD_KEY_CONTROLS_LIST= 'controls_list'

CTRL_DATE_PICKER_SINGLE=1
CTRL_CHECKLIST=2

CARD_OBJ_TYPE_GRAPH=1
CARD_OBJ_TYPE_TABLE=2

control_to_value_map = {
    CTRL_DATE_PICKER_SINGLE: 'date',
    CTRL_CHECKLIST: 'value'
}


supported_cards = {
    ID_CARD_TEST_PROGRESS: {
        CARD_KEY_TITLE: 'test progress',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_TEST_PROGRESS,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_TEST_PROGRESS,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_TEST_PROGRESS,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_test_progress_controls(),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_DATE_PICKER_START_DATE, type=CTRL_DATE_PICKER_SINGLE, kwarg_key='start_date'),
            dict(id=ID_DATE_PICKER_DEADLINE, type=CTRL_DATE_PICKER_SINGLE, kwarg_key='test_deadline'),
            dict(id=ID_CHECKLIST_TEST_PROGRESS_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'treat_blocked_as_not_run', 'treat_inprogress_as_not_run'})
        ]
    },
    ID_CARD_CURRENT_STATUS_OVERALL: {
        CARD_KEY_TITLE: 'current status (overall)',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_CURRENT_STATUS_OVERALL,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_CURRENT_STATUS_OVERALL,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_CURRENT_STATUS_OVERALL,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_STATUS_PIE_CHART,
    },
    ID_CARD_CURRENT_STATUS_BY_GROUP: {
        CARD_KEY_TITLE: 'current status (by test group)',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_CURRENT_STATUS_BY_GROUP,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_CURRENT_STATUS_BY_GROUP,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_GROUP,
        CARD_KEY_COLLAPSE_INITIAL_STATE: False,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_current_status_by_group_controls(),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_CHECKLIST_CURRENT_STATUS_BY_GROUP_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'show_not_run', 'show_blocked', 'show_inprogress', 'show_failed', 'show_passed'})
        ]
    },
    ID_CARD_TEST_RUNS_TABLE: {
        CARD_KEY_TITLE: 'test runs',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_TABLE,
        CARD_KEY_CHART_ID: ID_CHART_TEST_RUNS_TABLE,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_TEST_RUNS_TABLE,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_TEST_RUNS_TABLE,
        CARD_KEY_COLLAPSE_INITIAL_STATE: False,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_RUNS_TABLE,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_test_runs_controls(),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_CHECKLIST_TEST_RUNS_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'current_week'})
        ]
    },
    ID_CARD_WEEKLY_STATUS: {
        CARD_KEY_TITLE: 'weekly status ',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_WEEKLY_STATUS,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_WEEKLY_STATUS,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_WEEKLY_STATUS,
        CARD_KEY_COLLAPSE_INITIAL_STATE: False,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_WEEKLY_STATUS_BAR_CHART,
    }
}

# set up reverse lookup
collapse_id_to_chart_type = {}
for x in supported_cards:
    collapse_id_to_chart_type[supported_cards[x][CARD_KEY_COLLAPSE_ID]] = supported_cards[x][CARD_KEY_CHART_TYPE]


collapse_id_to_card_id= {}
for x in supported_cards:
    collapse_id_to_card_id[supported_cards[x][CARD_KEY_COLLAPSE_ID]] = x


def get_card_header(title, collapse_button_id, collapse_text):
    return dbc.CardHeader([
        dbc.Row([
            dbc.Col([html.H6(title, className='card-title')], width=10),
            dbc.Col([dbc.Button(collapse_text, id=collapse_button_id)], width=2)
        ])
    ])

def collapse_button_text(state):
    return 'collapse' if state is True else 'expand'

def get_card_layout(card):
    if card not in supported_cards:
        return None
    x = supported_cards[card]
    chart_id = x[CARD_KEY_CHART_ID]
    collapse_id = x[CARD_KEY_COLLAPSE_ID]
    collapse_button_id = x[CARD_KEY_COLLAPSE_BUTTON_ID]
    collapse_initial_state = x[CARD_KEY_COLLAPSE_INITIAL_STATE]
    title = x[CARD_KEY_TITLE]
    card_body_children = []
    controls_func = x.get(CARD_KEY_CONTROLS_LAYOUT_FUNC)
    if controls_func is not None:
        card_body_children.append(controls_func)
    chart_obj = dcc.Graph(id=chart_id) if x.get(CARD_KEY_OBJ_TYPE) == CARD_OBJ_TYPE_GRAPH else html.Div(id=chart_id)
    chart = dcc.Loading(dbc.Row([dbc.Col(chart_obj)]))
    card_body_children.append(chart)
    return dbc.Card([
        get_card_header(title=title, collapse_button_id=collapse_button_id, collapse_text=collapse_button_text(True)),
        dbc.Collapse(dbc.CardBody(card_body_children), id=collapse_id, is_open=collapse_initial_state)
    ])


def serve_layout():
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
                'test execution reports',
                style={
                    'color': 'blue',
                    'font-weight': 'normal',
                    'height': '50px',
                    'display': 'inline-block'
                }
            ),
            html.Hr(),
            dbc.CardHeader(get_selection_ui()),
        ] +
        [
            dbc.Row([
                dbc.Col(get_card_layout(x), width=12),
            ]) for x in supported_cards
        ] +
        [
            dbc.CardFooter([
                html.Div(id='id-status', children=f'Data last updated: {modified_datetime}')
            ]),
            dcc.Interval(interval=1 * 60 * 1000, id='id-interval'),
            # Hidden div inside the app that stores last updated date and time
            html.Div(id='id-last-modified-hidden', children=modified_datetime, style={'display': 'none'}),

        ], fluid=True
    )
    return layout


app.layout = serve_layout

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
    Output(ID_DROPDOWN_TEST_PLAN, 'options'),
    Output(ID_DROPDOWN_TEST_PLAN, 'value')],
    [Input('id-last-modified-hidden', 'children')],
    [State(ID_DROPDOWN_TEST_PLAN, 'value')]
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
    status = f'Data last updated: {modified_datetime}'
    return status, options, value


@app.callback(
    [Output(ID_DROPDOWN_TEST_CYCLE, 'options'),
     Output(ID_DROPDOWN_TEST_CYCLE, 'value'),
     Output(ID_DROPDOWN_TEST_CYCLE, 'persistence')],
    [Input(ID_DROPDOWN_TEST_PLAN, 'value')],
    [State(ID_DROPDOWN_TEST_CYCLE, 'value')]
)
def update_testcycle_options(testplan_ui, current_value):
    options = get_testcycle_options(testplan=testplan_ui)
    value = get_value_from_options(options, current_value)
    return [options, value, testplan_ui]

@app.callback(
    [Output(ID_DROPDOWN_TEST_GROUP, 'options'),
     Output(ID_DROPDOWN_TEST_GROUP, 'value'),
     Output(ID_DROPDOWN_TEST_GROUP, 'persistence')],
    [Input(ID_DROPDOWN_TEST_PLAN, 'value'),
     Input(ID_DROPDOWN_TEST_CYCLE, 'value')],
    [State(ID_DROPDOWN_TEST_GROUP, 'value')]
)
def update_testgroup_options(testplan_ui, testcycle_ui, current_value):
    options = get_testgroup_options(testplan=testplan_ui, testcycle=testcycle_ui)
    value = get_value_from_options(options, current_value)
    persistence = testcycle_ui
    return [options, value, persistence]

def update_figure(is_open, testplan, testcycle, testgroup, *args):
    if not is_open:
        raise PreventUpdate
    ctx = dash.callback_context
    collapse_id = list(ctx.inputs.keys())[0].split('.')[0]
    chart_type = collapse_id_to_chart_type[collapse_id]
    card_id = collapse_id_to_card_id[collapse_id]
    card_info = supported_cards[card_id]
    kwargs_to_pass = {}
    ctrl_list = card_info.get(CARD_KEY_CONTROLS_LIST)
    if ctrl_list is not None:
        for arg, item in zip(args, ctrl_list):
            kwarg_key = item['kwarg_key']
            if isinstance(kwarg_key, list):
                for arg1, kwarg_key1 in zip(arg, kwarg_key):
                    kwargs_to_pass[kwarg_key1] = arg1
            elif isinstance(kwarg_key, set): # this is the case for a checklist
                for arg1 in arg:
                    kwargs_to_pass[arg1] = True if arg1 in kwarg_key else False
            else:
                kwargs_to_pass[kwarg_key] = arg

    df = json_to_df(get_data())
    chart = get_chart(df, testplan, testcycle, testgroup,
                      chart_type=chart_type,
                      colormap=get_default_colormap(),
                      **kwargs_to_pass)
    return chart


def register_chart_update_callback(card_id):
    card_info = supported_cards[card_id]
    collapse_id = card_info[CARD_KEY_COLLAPSE_ID]
    chart_id = card_info[CARD_KEY_CHART_ID]
    chart_obj_type = card_info[CARD_KEY_OBJ_TYPE]
    output = Output(chart_id, 'figure') if chart_obj_type == CARD_OBJ_TYPE_GRAPH else Output(chart_id, 'children')
    inputs = [
        Input(collapse_id, 'is_open'),
        Input(ID_DROPDOWN_TEST_PLAN, 'value'),
        Input(ID_DROPDOWN_TEST_CYCLE, 'value'),
        Input(ID_DROPDOWN_TEST_GROUP, 'value'),
    ]

    if card_info.get(CARD_KEY_CONTROLS_LIST) is not None:
        for ctrl in card_info[CARD_KEY_CONTROLS_LIST]:
            inputs.append(Input(ctrl['id'], control_to_value_map[ctrl['type']]))

    app.callback(output, inputs)(update_figure)



def toggle_collapse(n, is_open):
    if n:
        return [not is_open, collapse_button_text(not is_open)]
    return [is_open, collapse_button_text(is_open)]

def register_card_collapse_callback(card_id):
    x = supported_cards[card_id]
    collapse_id = x[CARD_KEY_COLLAPSE_ID]
    collapse_button_id = x[CARD_KEY_COLLAPSE_BUTTON_ID]
    outputs = [Output(collapse_id, 'is_open'), Output(collapse_button_id, 'children')]
    inputs = [Input(collapse_button_id, 'n_clicks')]
    states = [State(collapse_id, 'is_open')]
    app.callback(outputs, inputs, states)(toggle_collapse)

for card_id in supported_cards:
    register_card_collapse_callback(card_id)
    register_chart_update_callback(card_id)

if __name__ == '__main__':
    app.run_server(debug=True)
