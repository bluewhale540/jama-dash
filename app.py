
import os
from jama_client import jama_client
import login_dialog
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import pandas
import jinja2.ext

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

proj_list = [x[0] for x in testing_list]

client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, projkey_list=proj_list):
    exit(1)

colormap = \
    {'NOT_RUN': 'darkslategray', 'PASSED': 'green', 'FAILED': 'firebrick', 'BLOCKED': 'royalblue', 'INPROGRESS': 'darkorange'}
status_names = client.get_status_names()

df_by_testplan = {}
df_testruns_by_testplan = {}
for project, testplan, title in testing_list:
    testcycle_db = client.retrieve_testcycles(project_key=project, testplan_key=testplan)
    if testcycle_db is None:
        exit(1)

    testcycles = [None,]
    for id, cycle in testcycle_db:
        testcycles.append(cycle)
    df_by_cycle = {}
    df_testruns_by_cycle = {}
    for cycle in testcycles:
        df = client.get_testrun_status_by_planned_weeks(project_key=project, testplan_key=testplan,
                                                        testcycle_key=cycle)
        df2 = client.get_testruns_for_current_week(project_key=project, testplan_key=testplan,
                                                        testcycle_key=cycle)
        if cycle is None:
            df_by_cycle['Overall'] = df
            df_testruns_by_cycle['Overall'] = df2
        else:
            df_by_cycle[cycle] = df
            # drop test cycle column since we are printing it elsewhere
            df2 = df2.drop(columns=['testcycle'])
            df_testruns_by_cycle[cycle] = df2
    df_by_testplan[title] = df_by_cycle
    df_testruns_by_testplan[title] = df_testruns_by_cycle


current_testplan = next(iter(df_by_testplan))
current_testcycle = next(iter(df_by_testplan[current_testplan]))


app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='id-test-plan',
                options=[{'label': i, 'value': i} for i in iter(df_by_testplan)],
                value=current_testplan
            ),
        ],
        style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='id-test-cycle',
                value=current_testcycle
            ),
        ],
        style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),
    dcc.Graph(id='weekly-status'),
    html.Hr(),
    html.Div(id='datatable-container')
])

@app.callback(
    Output('id-test-cycle', 'options'),
    [Input('id-test-plan', 'value')])
def update_testcycle_options(testplan):
    current_testplan = testplan
    current_testcycle = next(iter(df_by_testplan[current_testplan]))
    options = [{'label': i, 'value': i} for i in iter(df_by_testplan[testplan])]
    return options

@app.callback(
    Output('id-test-cycle', 'value'),
    [Input('id-test-plan', 'value')])
def update_current_testcycle(testplan):
    current_testcycle = next(iter(df_by_testplan[testplan]))
    return current_testcycle

@app.callback(
    Output('datatable-container', 'children'),
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value')])
def update_table(testplan, testcycle):
    df_testruns_by_cycle = df_testruns_by_testplan[testplan]
    df = df_testruns_by_cycle[testcycle]
    df['execution_date'] = df['execution_date'].apply(lambda x: x.date())
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
    return [html.H6('Test Runs Scheduled This Week'), table]


@app.callback(
    Output('weekly-status', 'figure'),
    [Input('id-test-plan', 'value'),
     Input('id-test-cycle', 'value')])
def update_graph(testplan, testcycle):
    current_testplan = testplan
    current_testcycle = testcycle
    df_by_cycle = df_by_testplan[current_testplan]
    if current_testcycle not in iter(df_by_cycle):
        current_testcycle = next(iter(df_by_testplan[current_testplan]))
    df = df_by_cycle[current_testcycle]
    data = []
    x_axis = df['planned_week'].values
    for status in status_names:
        y_axis = df[status].values
        data.append(dict(name=status, x=x_axis, y=y_axis, type='bar',
                         text=y_axis,
                         textposition='auto',
                         marker=dict(color=colormap[status])))
    return {
        'data': data,
        'layout': dict(
            title=testplan + ': ' + testcycle,
            uniformtext_minsize=8,
            uniformtext_mode='auto',
            xaxis={
                'title': 'Planned Week',
            },
            yaxis={
                'title': 'Number Of Test Runs',
            },
            barmode='stack'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=False)
