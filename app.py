
import os
from jama_client import jama_client
import login_dialog
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import pandas as pd
from datetime import timedelta, date, datetime


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

test_deadline = datetime.strptime('Feb 28 2020', '%b %d %Y')

proj_list = [x[0] for x in testing_list]

client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, projkey_list=proj_list):
    exit(1)


colormap = \
    {'NOT_RUN': 'darkslategray', 'PASSED': 'green', 'FAILED': 'firebrick', 'BLOCKED': 'royalblue', 'INPROGRESS': 'darkorange'}
status_names = client.get_status_names()

FIG_TYPE_WEEKLY_CHART = 'Weekly Status'
FIG_TYPE_HISTORICAL_CHART = 'Historical Status'
FIG_TYPE_CURRENT_RUNS_TABLE= 'Test Runs For Current Week'
chart_types = [FIG_TYPE_WEEKLY_CHART, FIG_TYPE_HISTORICAL_CHART, FIG_TYPE_CURRENT_RUNS_TABLE]
current_chart_type = next(iter(chart_types))
testplans = [] # list of all test plans

# DB of chart data by type, testplan and test cycle
chart_data_db = {}
for project, testplan, title in testing_list:
    testplan_ui = title  # we will use title to mean testplan in the UI
    testplans.append(testplan_ui)
    chart_data_db[testplan_ui] = {}
    testcycles = [None, ] + [c for i,c in client.retrieve_testcycles(project_key=project, testplan_key=testplan)]
    df = pd.DataFrame() # initialize an empty data frame
    for cycle in testcycles:
        cycle_ui = cycle
        if cycle is None:
            # rename it to Overall
            cycle_ui = 'Overall'

        chart_data_db[testplan_ui][cycle_ui] = {}
        for chart_type in chart_types:
            if chart_type == FIG_TYPE_WEEKLY_CHART:
                df = client.get_testrun_status_by_planned_weeks(project_key=project,
                                                                testplan_key=testplan,
                                                                testcycle_key=cycle)
            if chart_type == FIG_TYPE_HISTORICAL_CHART:
                df = client.get_testrun_status_historical(project_key=project,
                                                          testplan_key=testplan,
                                                          testcycle_key=cycle)
            if chart_type == FIG_TYPE_CURRENT_RUNS_TABLE:
                df = client.get_testruns_for_current_week(project_key=project,
                                                          testplan_key=testplan,
                                                          testcycle_key=cycle)
                if cycle is not None:
                    # drop test cycle column since we are printing it elsewhere
                    df = df.drop(columns=['testcycle'])

            chart_data_db[testplan_ui][cycle_ui][chart_type] = df

current_chart_type = next(iter(chart_types))
current_testplan = next(iter(testplans))
current_testcycle = next(iter(chart_data_db[current_testplan]))

# build current week testrun tables into this lookup for fast refresh
current_week_tables_db = {}
for i in iter(testplans):
    current_week_tables_db[i] = {}

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

def get_current_runs_table(testplan, testcycle):
    df = chart_data_db[testplan][testcycle][FIG_TYPE_CURRENT_RUNS_TABLE]
    #df['execution_date'] = df['execution_date'].apply(lambda x: x.date() if x is not None else None)
    table =  dash_table.DataTable(
        id='datatable-testruns',
        columns=[
            {'name': i, 'id': i, 'deletable': False, 'selectable': False}
                for i in df.columns
        ],
        data=df.to_dict('records'),
        editable=False,
        filter_action='native',
        sort_action='native',
        page_size=50,
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in df.columns
        ] +
        [
            {
                'if': {'column_id': 'testcycle'},
                'maxWidth': '30px'
            },
            {
                'if': {'column_id': 'status'},
                'maxWidth': '30px'
            },
            {
                'if': {'column_id': 'execution_date'},
                'maxWidth': '24px'
            },
            {
                'if': {'column_id': 'assigned_to'},
                'maxWidth': '24px'
            },

        ],
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{status} eq "' + s + '"',
                },
                'backgroundColor': colormap[s],
                'color': 'white'
            } for s in status_names
        ],
        style_cell={
            'minWidth': '0px', 'maxWidth': '60px',
            'whiteSpace': 'normal',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        }
    )

    current_week_tables_db[testplan][testcycle] = table
    return table

def get_weekly_status_chart(testplan, testcycle):
    df = chart_data_db[testplan][testcycle][FIG_TYPE_WEEKLY_CHART]
    data = []
    fmt_date = lambda x: x.strftime('%b %d') + ' - ' + (x + timedelta(days=4)).strftime('%b %d') \
        if x is not None else 'Unassigned'
    x_axis = [fmt_date(x) for x in df['planned_week'].values]

    for status in status_names:
        y_axis = df[status].values
        data.append(dict(name=status, x=x_axis, y=y_axis, type='bar',
                         text=y_axis,
                         textposition='inside',
                         marker=dict(color=colormap[status])))
    return dcc.Graph(
            id='weekly-status',
            figure = {
                'data': data,
                'layout': dict(
                    title=testplan + ': ' + testcycle,
                    xaxis={
                        'title': 'Planned Week',
                    },
                    yaxis={
                        'title': 'Number Of Test Runs',
                    },
                    barmode='stack'
                )
            }
        )


def get_historical_status_chart(testplan, testcycle):
    df = chart_data_db[testplan][testcycle][FIG_TYPE_HISTORICAL_CHART]
    # create historical status scatter graph
    deadline_x = []
    deadline_y = []

    x_list = [pd.to_datetime(d).date() for d in df['date'].values]
    y_dict = {} # dict of y-axis with status name as key
    for status in status_names:
        y_dict[status] = df[status].values
    if test_deadline is not None:
        tail = df.tail(1)
        current_date = pd.to_datetime(tail['date'].values[0])
        deadline_x = [current_date, pd.to_datetime(test_deadline)]
        deadline_y = [tail['NOT_RUN'].values[0], 0]

    # Add traces
    data = []
    for status in status_names:
        data.append(go.Scatter(x=x_list,
                         y=y_dict[status],
                         mode='lines',
                         name=status,
                         line=dict(color=colormap[status])))
    # add deadline meeting trace
    if test_deadline is not None:
        data.append(go.Scatter(x=deadline_x,
                         y=deadline_y,
                         mode='lines',
                         name='required burn rate',
                         line=dict(dash='dash', color='black')))
    fig = go.Figure(data=data)
    return dcc.Graph(
            id='historical-status',
            figure = fig)


@app.callback(
    Output('chart-container', 'children'),
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value'),
     Input('id-chart-type', 'value')])
def update_graph(testplan, testcycle, type):
    global current_chart_type
    global current_testcycle
    current_chart_type = type
    current_testcycle = testcycle
    if type == FIG_TYPE_WEEKLY_CHART:
        return [get_weekly_status_chart(testplan, testcycle)]
    if type == FIG_TYPE_HISTORICAL_CHART:
        return [get_historical_status_chart(testplan, testcycle)]
    if type == FIG_TYPE_CURRENT_RUNS_TABLE:
        return [get_current_runs_table(testplan, testcycle)]
    return []


if __name__ == '__main__':
    app.run_server(debug=False)
