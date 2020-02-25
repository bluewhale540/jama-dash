import dash_table
import dash_html_components as html
from testrun_utils import get_testruns_for_current_week, get_status_names

def get_current_runs_table(df, testcycle, testcase, title, colormap):
    df = get_testruns_for_current_week(df=df, testcycle_key=testcycle, testcase_key=testcase)
    if df is None:
        return html.P('No test runs found!')

    if testcycle is not None:
        # drop test cycle column since we are printing it elsewhere
        df = df.drop(columns=['testcycle'])
    if testcase is not None:
        # drop test cycle column since we are printing it elsewhere
        df = df.drop(columns=['testcase'])

    table = dash_table.DataTable(
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
            } for s in get_status_names()
        ],
        style_cell={
            'minWidth': '0px', 'maxWidth': '60px',
            'whiteSpace': 'normal',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        }
    )
    return table


def get_current_runs_table_old(client, project, testplan, testcycle, title, colormap):
    df = client.get_testruns_for_current_week(project_key=project,
                                              testplan_key=testplan,
                                              testcycle_key=testcycle)
    if testcycle is not None:
        # drop test cycle column since we are printing it elsewhere
        df = df.drop(columns=['testcycle'])

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
            } for s in client.get_status_names()
        ],
        style_cell={
            'minWidth': '0px', 'maxWidth': '60px',
            'whiteSpace': 'normal',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        }
    )
    return table
