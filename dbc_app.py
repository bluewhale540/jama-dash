import os
import logger
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
    get_testgroup_from_label, \
    get_priority_labels, \
    get_priority_from_label, \
    get_planned_week_labels, \
    get_planned_week_from_label, \
    json_to_df, \
    retrieve_testruns

import charts
from charts import get_chart_types, get_default_colormap
import redis_data
import testrun_utils

ID_DROPDOWN_TEST_PLAN = 'id-dropdown-test-plan'
ID_DROPDOWN_TEST_CYCLE = 'id-dropdown-test-cycle'
ID_DROPDOWN_TEST_GROUP = 'id-dropdown-test-group'
ID_DROPDOWN_PRIORITY = 'id-dropdown-priority'
ID_DROPDOWN_WEEK = 'id-dropdown-week'
ID_DATE_PICKER_START_DATE = 'id-date-test-progress-start-date'
ID_DATE_PICKER_DEADLINE = 'id-date-test-progress-deadline'
ID_CHECKLIST_TEST_PROGRESS_OPTIONS = 'id-checklist-test-progress-options'
ID_CHECKLIST_WEEKLY_STATUS_OPTIONS = 'id-checklist-weekly-status-options'
ID_CHECKLIST_CURRENT_STATUS_BY_PERSON_OPTIONS = 'id-checklist-current-by-person-options'
ID_CHECKLIST_CURRENT_STATUS_BY_NETWORK_OPTIONS = 'id-chekclist-current-by-network-options'
ID_CHECKLIST_CURRENT_STATUS_BY_GROUP_OPTIONS = 'id-checklist-current-by-group-options'
ID_CHECKLIST_TEST_RUNS_OPTIONS='id-checklist-test-runs-options'

# checklist options for the test progress card
CHECKLIST_LABEL_BLOCKED_NOT_RUN = 'blocked as not run'
CHECKLIST_LABEL_INPROGRESS_NOT_RUN = 'in progress as not run'
CHECKLIST_VALUE_BLOCKED_NOT_RUN = 'treat_blocked_as_not_run'
CHECKLIST_VALUE_INPROGRESS_NOT_RUN = 'treat_inprogress_as_not_run'

test_progress_options = [
    dict(label=CHECKLIST_LABEL_BLOCKED_NOT_RUN, value=CHECKLIST_VALUE_BLOCKED_NOT_RUN),
    dict(label=CHECKLIST_LABEL_INPROGRESS_NOT_RUN, value=CHECKLIST_VALUE_INPROGRESS_NOT_RUN),
]

# checklist options for the test progress card
CHECKLIST_LABEL_SHOW_NOT_RUN = 'not run'
CHECKLIST_LABEL_SHOW_IN_PROGRESS = 'in progress'
CHECKLIST_LABEL_SHOW_BLOCKED = 'blocked'
CHECKLIST_LABEL_SHOW_PASSED = 'passed'
CHECKLIST_LABEL_SHOW_FAILED = 'failed'
CHECKLIST_VALUE_SHOW_NOT_RUN = 'show_not_run'
CHECKLIST_VALUE_SHOW_IN_PROGRESS = 'show_inprogress'
CHECKLIST_VALUE_SHOW_BLOCKED = 'show_blocked'
CHECKLIST_VALUE_SHOW_PASSED = 'show_passed'
CHECKLIST_VALUE_SHOW_FAILED = 'show_failed'

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


ID_CARD_TEST_PROGRESS = 'id-card-test-progress'
ID_CARD_CURRENT_STATUS_OVERALL = 'id-card-current-status-overall'
ID_CARD_EXECUTION_METHOD = 'id-card-execution-method'
ID_CARD_WEEKLY_STATUS = 'id-card-weekly-status'
ID_CARD_CURRENT_STATUS_BY_PERSON = 'id-card-current-status-by-person'
ID_CARD_CURRENT_STATUS_BY_NETWORK = 'id-car-current-status-by-network'
ID_CARD_CURRENT_STATUS_BY_GROUP = 'id-card-current-status-by-group'
ID_CARD_TEST_RUNS_TABLE = 'id-card-test-runs-table'

ID_CHART_TEST_PROGRESS= 'id-chart-test-progress'
ID_CHART_CURRENT_STATUS_OVERALL= 'id-chart-current-status-overall'
ID_CHART_EXECUTION_METHOD= 'id-chart-execution-method'
ID_CHART_WEEKLY_STATUS='id-chart-weekly-status'
ID_CHART_CURRENT_STATUS_BY_PERSON='id-chart-current-status-by-person'
ID_CHART_CURRENT_STATUS_BY_NETWORK='id-chart-current-status-by-network'
ID_CHART_CURRENT_STATUS_BY_GROUP= 'id-chart-current-status-by-group'
ID_CHART_TEST_RUNS_TABLE='id-chart-test-runs-table'

ID_COLLAPSE_TEST_PROGRESS = 'id-collapse-test-progress'
ID_COLLAPSE_CURRENT_STATUS_OVERALL = 'id-collapse-current-status-overall'
ID_COLLAPSE_EXECUTION_METHOD = 'id-collapse-execution-method'
ID_COLLAPSE_WEEKLY_STATUS = 'id-collapse-weekly-status'
ID_COLLAPSE_CURRENT_STATUS_BY_PERSON = 'id-collapse-current-status-by-person'
ID_COLLAPSE_CURRENT_STATUS_BY_NETWORK = 'id-collapse-current-status-by-network'
ID_COLLAPSE_CURRENT_STATUS_BY_GROUP = 'id-collapse-current-status-by-group'
ID_COLLAPSE_TEST_RUNS_TABLE ='id-collapse-test-runs-table'

ID_COLLAPSE_BUTTON_TEST_PROGRESS = 'id-collapse-button-test-progress'
ID_COLLAPSE_BUTTON_CURRENT_STATUS_OVERALL = 'id-collapse-button-current-status-overall'
ID_COLLAPSE_BUTTON_EXECUTION_METHOD = 'id-collapse-button-execution-method'
ID_COLLAPSE_BUTTON_WEEKLY_STATUS = 'id-collapse-button-weekly-status'
ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_PERSON = 'id-collapse-button-current-status-by-person'
ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_NETWORK = 'id-collapse-button-current-status-by-network'
ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_GROUP = 'id-collapse-button-current-status-by-group'
ID_COLLAPSE_BUTTON_TEST_RUNS_TABLE = 'id-collapse-button-test-runs-table'

ID_WEEK_DROPDOWN_CURRENT_STATUS_OVERALL = 'id-week-dropdown-current-status'
ID_WEEK_DROPDOWN_EXECUTION_METHOD = 'id-week-dropdown-execution-method'
ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_PERSON = 'id-week-dropdown-current-status-by-person'
ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_NETWORK = 'id-week-dropdown-current-status-by-network'
ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_GROUP = 'id-week-dropdown-current-status-by-group'
ID_WEEK_DROPDOWN_TEST_RUNS_TABLE = 'id-week-dropdown-testruns-table'
ID_WEEK_DROPDOWN_NOT_PRESENT = 'id-week-dropdown-not-present'

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
jama_url = os.environ.get('JAMA_API_URL')
jama_api_username = os.environ.get('JAMA_API_USERNAME')
jama_api_password = os.environ.get('JAMA_API_PASSWORD')

if jama_url is None:
    jama_url = 'https://paperclip.idirect.net'


@cache.memoize()
def get_data():
    """
    If Redis is available, retrieve the dataframe from Redis. This dataframe is periodically updated through the redis
    task.

    If Redis is not available, directly get the data from Contour
    """
    if redis_inst is not None:
        return redis_data.get_dataframe_json(redis_inst)

    # Attempt to get data directly from Contour
    try:
        df = retrieve_testruns(jama_url=jama_url,
                               jama_username=jama_api_username,
                               jama_password=jama_api_password)
    except Exception as e:
        logger.error(f'caught exception {e} trying to get test runs')
        return None

    if df is None:
        logger.error('cannot retrieve data from Jama/Contour server. Check config file!')
        return None

    print(df)
    df.to_csv('contour_data.csv', index=False)
    jsonified_df = testrun_utils.df_to_json(df)
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
def get_priority_options(testplan, testcycle, testgroup):
    df = json_to_df(get_data())
    priorities =  \
        [{'label': i, 'value': i} for i in get_priority_labels(
            df, testplan_key=testplan,
            testcycle_key=get_testcycle_from_label(testcycle),
            testgroup_key=get_testgroup_from_label(testgroup))]
    return priorities


@cache.memoize()
def get_week_options(testplan, testcycle, testgroup):
    df = json_to_df(get_data())
    weeks =  \
        [{'label': i, 'value': i} for i in get_planned_week_labels(
            df, testplan_key=testplan,
            testcycle_key=get_testcycle_from_label(testcycle),
            testgroup_key=get_testgroup_from_label(testgroup))]
    return weeks


@cache.memoize()
def get_chart(df, testplan_ui, testcycle_ui, testgroup_ui, priority_ui, week_ui, chart_type, colormap, **kwargs):
    return charts.get_chart(
            df, testplan_ui, testcycle_ui, testgroup_ui, priority_ui, week_ui, chart_type, colormap, **kwargs)



def get_selection_ui():
    testplans = get_testplan_options()
    initial_testplan = init_value(testplans)
    testcycles = get_testcycle_options(testplan=initial_testplan)
    initial_testcycle = init_value(testcycles)
    testgroups = get_testgroup_options(testplan=initial_testplan, testcycle=initial_testcycle)
    initial_testgroup = init_value(testgroups)
    priorities = get_priority_options(testplan=initial_testplan, testcycle=initial_testcycle,
                                      testgroup=initial_testgroup)
    initial_priority = init_value(priorities)
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
        lg=4
    )

    group2 = dbc.Col(
        [
            dbc.Label('select a test cycle', html_for=ID_DROPDOWN_TEST_CYCLE),
            dcc.Dropdown(
                id=ID_DROPDOWN_TEST_CYCLE,
                #options=testcycles,
                #value=initial_testcycle,
                persistence_type='local',
            ),
        ],
        lg=3
    )

    group3 = dbc.Col(
        [
            dbc.Label('select a test group', html_for=ID_DROPDOWN_TEST_GROUP),
            dcc.Dropdown(
                id=ID_DROPDOWN_TEST_GROUP,
                #options=testgroups,
                #value=initial_testgroup,
                persistence_type='local',
            ),
        ],
        lg=3
    )

    group4 = dbc.Col(
        [
            dbc.Label('select a priority', html_for=ID_DROPDOWN_PRIORITY),
            dcc.Dropdown(
                id=ID_DROPDOWN_PRIORITY,
                #options=priorities,
                #value=initial_priority,
                persistence_type='local',
            ),
        ],
        lg=2
    )

    form = dbc.Row([group1, group2, group3, group4])
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
                    value=[],
                    labelStyle={'display': 'block'},
                    inputStyle={'margin-right': '5px'},
                    persistence=True
                )
            ]),
        ),
    ])
    return controls

"""Generates the checklist controls for some charts

Parameters:
    id(constant): The id of the checklist

Returns:
    controls: The checklist controls for the app
"""
def get_status_checklist_controls(id):
    controls = dbc.Row([
        dbc.Col(
            dbc.FormGroup([
                dbc.Label('select status to show', html_for=id),
                dcc.Checklist(
                    id=id,
                    options=current_status_by_group_options,
                    value=[CHECKLIST_VALUE_SHOW_NOT_RUN,
                        CHECKLIST_VALUE_SHOW_IN_PROGRESS,
                        CHECKLIST_VALUE_SHOW_BLOCKED, 
                        CHECKLIST_VALUE_SHOW_PASSED,
                        CHECKLIST_VALUE_SHOW_FAILED],
                    labelStyle={'display': 'block'},
                    inputStyle={'margin-right': '5px'},
                    persistence=True
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
                    persistence=True
                )
            ])
        ),
    ])
    return controls


CARD_KEY_TITLE = 'title'
CARD_KEY_OBJ_TYPE = 'type' # graph or table
CARD_KEY_CHART_ID = 'chart_id'
CARD_KEY_COLLAPSE_ID = 'collapse_id'
CARD_KEY_COLLAPSE_BUTTON_ID = 'collapse_button_id'
CARD_KEY_COLLAPSE_INITIAL_STATE = 'collapse_initial_state' # open=True, collapsed=False
CARD_KEY_WEEK_DROPDOWN_ID = 'week_dropdown_id'
CARD_KEY_WEEK_DROPDOWN_PRESENT = 'week_dropdown_present'
CARD_KEY_CHART_TYPE = 'chart_type'
CARD_KEY_CONTROLS_LAYOUT_FUNC = 'controls_layout_func'
CARD_KEY_CONTROLS_LIST = 'controls_list'

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
        CARD_KEY_WEEK_DROPDOWN_PRESENT: False,
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
        CARD_KEY_WEEK_DROPDOWN_ID: ID_WEEK_DROPDOWN_CURRENT_STATUS_OVERALL,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_STATUS_PIE_CHART,
    },
    ID_CARD_EXECUTION_METHOD: {
        CARD_KEY_TITLE: 'execution method',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_EXECUTION_METHOD,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_EXECUTION_METHOD,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_EXECUTION_METHOD,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_WEEK_DROPDOWN_ID: ID_WEEK_DROPDOWN_EXECUTION_METHOD,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_EXEC_METHOD_PIE_CHART,
    },
    ID_CARD_WEEKLY_STATUS: {
        CARD_KEY_TITLE: 'weekly status',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_WEEKLY_STATUS,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_WEEKLY_STATUS,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_WEEKLY_STATUS,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_WEEK_DROPDOWN_PRESENT: False,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_WEEKLY_STATUS_BAR_CHART,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_status_checklist_controls(ID_CHECKLIST_WEEKLY_STATUS_OPTIONS),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_CHECKLIST_WEEKLY_STATUS_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'show_not_run', 'show_blocked', 'show_inprogress', 'show_failed', 'show_passed'})
        ]
    },
    ID_CARD_CURRENT_STATUS_BY_PERSON: {
        CARD_KEY_TITLE: 'current status (by person)',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_CURRENT_STATUS_BY_PERSON,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_CURRENT_STATUS_BY_PERSON,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_PERSON,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_WEEK_DROPDOWN_ID: ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_PERSON,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_STATUS_BY_PERSON_BAR_CHART,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_status_checklist_controls(ID_CHECKLIST_CURRENT_STATUS_BY_PERSON_OPTIONS),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_CHECKLIST_CURRENT_STATUS_BY_PERSON_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'show_not_run', 'show_blocked', 'show_inprogress', 'show_failed', 'show_passed'})
        ]
    },
    ID_CARD_CURRENT_STATUS_BY_NETWORK: {
        CARD_KEY_TITLE: 'current status (by test network)',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_CURRENT_STATUS_BY_NETWORK,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_CURRENT_STATUS_BY_NETWORK,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_NETWORK,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_WEEK_DROPDOWN_ID: ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_NETWORK,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_STATUS_BY_NETWORK_BAR_CHART,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_status_checklist_controls(ID_CHECKLIST_CURRENT_STATUS_BY_NETWORK_OPTIONS),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_CHECKLIST_CURRENT_STATUS_BY_NETWORK_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'show_not_run', 'show_blocked', 'show_inprogress', 'show_failed', 'show_passed'})
        ]
    },
    ID_CARD_CURRENT_STATUS_BY_GROUP: {
        CARD_KEY_TITLE: 'current status (by test group)',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_GRAPH,
        CARD_KEY_CHART_ID: ID_CHART_CURRENT_STATUS_BY_GROUP,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_CURRENT_STATUS_BY_GROUP,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_CURRENT_STATUS_BY_GROUP,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_WEEK_DROPDOWN_ID: ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_GROUP,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_status_checklist_controls(ID_CHECKLIST_CURRENT_STATUS_BY_GROUP_OPTIONS),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_CHECKLIST_CURRENT_STATUS_BY_GROUP_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'show_not_run', 'show_blocked', 'show_inprogress', 'show_failed', 'show_passed'})
        ]
    },
    ID_CARD_TEST_RUNS_TABLE: {
        CARD_KEY_TITLE: 'test run data',
        CARD_KEY_OBJ_TYPE: CARD_OBJ_TYPE_TABLE,
        CARD_KEY_CHART_ID: ID_CHART_TEST_RUNS_TABLE,
        CARD_KEY_COLLAPSE_ID: ID_COLLAPSE_TEST_RUNS_TABLE,
        CARD_KEY_COLLAPSE_BUTTON_ID: ID_COLLAPSE_BUTTON_TEST_RUNS_TABLE,
        CARD_KEY_COLLAPSE_INITIAL_STATE: True,
        CARD_KEY_WEEK_DROPDOWN_ID: ID_WEEK_DROPDOWN_TEST_RUNS_TABLE,
        CARD_KEY_CHART_TYPE: charts.FIG_TYPE_CURRENT_RUNS_TABLE,
        CARD_KEY_CONTROLS_LAYOUT_FUNC: get_test_runs_controls(),
        CARD_KEY_CONTROLS_LIST: [
            dict(id=ID_CHECKLIST_TEST_RUNS_OPTIONS, type=CTRL_CHECKLIST,
                 kwarg_key={'current_week'})
        ]
    }
}

# set up reverse lookup
collapse_id_to_chart_type = {}
for x in supported_cards:
    collapse_id_to_chart_type[supported_cards[x][CARD_KEY_COLLAPSE_ID]] = supported_cards[x][CARD_KEY_CHART_TYPE]


collapse_id_to_card_id= {}
for x in supported_cards:
    collapse_id_to_card_id[supported_cards[x][CARD_KEY_COLLAPSE_ID]] = x


def get_card_header(title, collapse_button_id, collapse_text, week_dropdown=True, week_dropdown_id=None):
    testplans = get_testplan_options()
    initial_testplan = init_value(testplans)
    testcycles = get_testcycle_options(testplan=initial_testplan)
    initial_testcycle = init_value(testcycles)
    testgroups = get_testgroup_options(testplan=initial_testplan, testcycle=initial_testcycle)
    initial_testgroup = init_value(testgroups)
    if week_dropdown:
        weeks = get_week_options(testplan=initial_testplan, testcycle=initial_testcycle, testgroup=initial_testgroup)
        initial_week = init_value(weeks)
        return dbc.CardHeader([
            dbc.Row([
                dbc.Col([html.H6(title, className='card-title')], width=3),
                dbc.Col([
                    dcc.Dropdown(
                        id=week_dropdown_id,
                        options=weeks,
                        value=initial_week,
                        persistence=True,
                        persistence_type='local'
                        #multi='True'
                    ),
                ],
                width=6),
                dbc.Col(width=1),
                dbc.Col([dbc.Button(collapse_text, id=collapse_button_id)], width=2)
            ])
        ])
    
    else:
        return dbc.CardHeader([
            dbc.Row([
                dbc.Col([html.H6(title, className='card-title')], width=10),
                dbc.Col([dbc.Button(collapse_text, id=collapse_button_id)], width=2)
            ])
        ])

def collapse_button_text(state):
    return 'collapse' if state is True else 'expand'


'''Gets the full card layout for the charts

Parameters:
    card_id: The ID of the supported card
    
Returns:
    The dashboard card'''
def get_card_layout(card_id):
    if card_id not in supported_cards:
        return None
    card = supported_cards[card_id]
    chart_id = card[CARD_KEY_CHART_ID]

    # parameters for the collapse button
    collapse_id = card[CARD_KEY_COLLAPSE_ID]
    collapse_button_id = card[CARD_KEY_COLLAPSE_BUTTON_ID]
    collapse_initial_state = card[CARD_KEY_COLLAPSE_INITIAL_STATE]

    # if the card has a week dropdown or not
    if CARD_KEY_WEEK_DROPDOWN_PRESENT in card:
        week_dropdown = card[CARD_KEY_WEEK_DROPDOWN_PRESENT]
    else:
        week_dropdown = True
    
    # if there is a week dropdown, assign its id
    week_dropdown_id = None
    if week_dropdown:
        week_dropdown_id = card[CARD_KEY_WEEK_DROPDOWN_ID]

    title = card[CARD_KEY_TITLE]
    card_body_children = []
    controls_func = card.get(CARD_KEY_CONTROLS_LAYOUT_FUNC)
    if controls_func is not None:
        card_body_children.append(controls_func)
    chart_obj = dcc.Graph(id=chart_id) if card.get(CARD_KEY_OBJ_TYPE) == CARD_OBJ_TYPE_GRAPH else html.Div(id=chart_id)
    chart = dcc.Loading(dbc.Row([dbc.Col(chart_obj)]))
    card_body_children.append(chart)
    return dbc.Card([
        get_card_header(title=title, 
            collapse_button_id=collapse_button_id, 
            collapse_text=collapse_button_text(True),
            week_dropdown=week_dropdown,
            week_dropdown_id=week_dropdown_id),
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
                dbc.Col(get_card_layout(ID_CARD_TEST_PROGRESS), width=12)
            ], no_gutters=True)
        ] +
        [
            dbc.Row([
                dbc.Col(get_card_layout(ID_CARD_CURRENT_STATUS_OVERALL), width=6),
                dbc.Col(get_card_layout(ID_CARD_EXECUTION_METHOD), width=6)
            ], no_gutters=True)
        ] +
        [
            dbc.Row([
                dbc.Col(get_card_layout(ID_CARD_WEEKLY_STATUS), width=6),
                dbc.Col(get_card_layout(ID_CARD_CURRENT_STATUS_BY_PERSON), width=6)
            ], no_gutters=True)
        ] +
        [
            dbc.Row([
                dbc.Col(get_card_layout(ID_CARD_CURRENT_STATUS_BY_NETWORK), width=6),
                dbc.Col(get_card_layout(ID_CARD_CURRENT_STATUS_BY_GROUP), width=6)
            ], no_gutters=True)
        ] +
        [
            dbc.Row([
                dbc.Col(get_card_layout(ID_CARD_TEST_RUNS_TABLE), width=12),
            ], no_gutters=True)
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

'''
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
'''


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
    cache.delete_memoized(get_priority_options)
    cache.delete_memoized(get_week_options)
    cache.delete_memoized(get_chart)
    testplan_options = get_testplan_options()
    testplan_value = get_value_from_options(testplan_options, current_testplan)
    status = f'Data last updated: {modified_datetime}'
    return status, testplan_options, testplan_value


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
    persistence = testplan_ui + ':' + testcycle_ui
    return [options, value, persistence]


@app.callback(
    [Output(ID_DROPDOWN_PRIORITY, 'options'),
     Output(ID_DROPDOWN_PRIORITY, 'value'),
     Output(ID_DROPDOWN_PRIORITY, 'persistence')],
    [Input(ID_DROPDOWN_TEST_PLAN, 'value'),
     Input(ID_DROPDOWN_TEST_CYCLE, 'value'),
     Input(ID_DROPDOWN_TEST_GROUP, 'value')],
    [State(ID_DROPDOWN_PRIORITY, 'value')]
)
def update_priority_options(testplan_ui, testcycle_ui, testgroup_ui, current_value):
    options = get_priority_options(testplan=testplan_ui, testcycle=testcycle_ui, testgroup=testgroup_ui)
    value = get_value_from_options(options, current_value)
    persistence = testplan_ui + ':' + testcycle_ui + ':' + testgroup_ui
    return [options, value, persistence]


@app.callback(
    [Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_OVERALL, 'options'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_OVERALL, 'value'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_OVERALL, 'persistence'),
     Output(ID_WEEK_DROPDOWN_EXECUTION_METHOD, 'options'),
     Output(ID_WEEK_DROPDOWN_EXECUTION_METHOD, 'value'),
     Output(ID_WEEK_DROPDOWN_EXECUTION_METHOD, 'persistence'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_PERSON, 'options'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_PERSON, 'value'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_PERSON, 'persistence'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_NETWORK, 'options'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_NETWORK, 'value'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_NETWORK, 'persistence'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_GROUP, 'options'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_GROUP, 'value'),
     Output(ID_WEEK_DROPDOWN_CURRENT_STATUS_BY_GROUP, 'persistence'),
     Output(ID_WEEK_DROPDOWN_TEST_RUNS_TABLE, 'options'),
     Output(ID_WEEK_DROPDOWN_TEST_RUNS_TABLE, 'value'),
     Output(ID_WEEK_DROPDOWN_TEST_RUNS_TABLE, 'persistence')],
    [Input(ID_DROPDOWN_TEST_PLAN, 'value'),
     Input(ID_DROPDOWN_TEST_CYCLE, 'value'),
     Input(ID_DROPDOWN_TEST_GROUP, 'value')]
)
def update_week_options(testplan_ui, testcycle_ui, testgroup_ui):
    options = get_week_options(testplan=testplan_ui, testcycle=testcycle_ui, testgroup=testgroup_ui)
    value = get_value_from_options(options)
    persistence = testplan_ui + ':' + testcycle_ui + ':' + testgroup_ui
    return [options, value, persistence] * 6


def update_figure_with_week(is_open, testplan, testcycle, testgroup, priority, week, *args):
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
    chart = get_chart(df, testplan, testcycle, testgroup, priority,
                      week_ui=week,
                      chart_type=chart_type,
                      colormap=get_default_colormap(),
                      **kwargs_to_pass)
    
    return chart

def update_figure_without_week(is_open, testplan, testcycle, testgroup, priority, *args):
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
    chart = get_chart(df, testplan, testcycle, testgroup, priority,
                      chart_type=chart_type,
                      week_ui=None,
                      colormap=get_default_colormap(),
                      **kwargs_to_pass)
    
    return chart


def register_chart_update_callback(card_id):
    card_info = supported_cards[card_id]
    collapse_id = card_info[CARD_KEY_COLLAPSE_ID]
    chart_id = card_info[CARD_KEY_CHART_ID]
    chart_obj_type = card_info[CARD_KEY_OBJ_TYPE]
    output = Output(chart_id, 'figure') if chart_obj_type == CARD_OBJ_TYPE_GRAPH else Output(chart_id, 'children')
    
    week_dropdown = card_info.get(CARD_KEY_WEEK_DROPDOWN_ID)
    week_value = None
    if week_dropdown is not None:
        week_value = Input(week_dropdown, 'value')
        inputs = [
            Input(collapse_id, 'is_open'),
            Input(ID_DROPDOWN_TEST_PLAN, 'value'),
            Input(ID_DROPDOWN_TEST_CYCLE, 'value'),
            Input(ID_DROPDOWN_TEST_GROUP, 'value'),
            Input(ID_DROPDOWN_PRIORITY, 'value'),
            week_value
        ]
        if card_info.get(CARD_KEY_CONTROLS_LIST) is not None:
            for ctrl in card_info[CARD_KEY_CONTROLS_LIST]:
                inputs.append(Input(ctrl['id'], control_to_value_map[ctrl['type']]))

        app.callback(output, inputs)(update_figure_with_week)

    else:
        inputs = [
            Input(collapse_id, 'is_open'),
            Input(ID_DROPDOWN_TEST_PLAN, 'value'),
            Input(ID_DROPDOWN_TEST_CYCLE, 'value'),
            Input(ID_DROPDOWN_TEST_GROUP, 'value'),
            Input(ID_DROPDOWN_PRIORITY, 'value'),
        ]
        if card_info.get(CARD_KEY_CONTROLS_LIST) is not None:
            for ctrl in card_info[CARD_KEY_CONTROLS_LIST]:
                inputs.append(Input(ctrl['id'], control_to_value_map[ctrl['type']]))

        app.callback(output, inputs)(update_figure_without_week)


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
    app.run_server(host='0.0.0.0', debug=True)
