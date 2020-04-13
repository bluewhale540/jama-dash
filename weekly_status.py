import dash_html_components as html
import dash_table

from jama_client import jama_client
import testrun_utils
import dash_core_components as dcc
from datetime import timedelta

from testrun_utils import get_testruns_for_current_week, get_status_names


def get_weekly_status_bar_chart(df, testcycle, testgroup, title, colormap):
    df1 = testrun_utils.get_testrun_status_by_planned_weeks(df, testcycle_key=testcycle, testgroup_key=testgroup)
    # sort in ascending order with NaN value first
    df1.sort_values('planned_week', axis=0, ascending=True, inplace=True, na_position='first')
    fmt_date = lambda x: x.strftime('%b %d') + ' - ' + (x + timedelta(days=4)).strftime('%b %d') \
        if x is not None else 'Unassigned'
    x_axis = [fmt_date(x) for x in df1['planned_week'].values]
    data = []
    for status in testrun_utils.get_status_names():
        y_axis = df1[status].values
        data.append(dict(name=status, x=x_axis, y=y_axis, type='bar',
                         text=y_axis,
                         textposition='inside',
                         marker=dict(color=colormap[status])))

    figure = {
        'data': data,
        'layout': dict(
            xaxis={
                'title': 'Planned Week',
            },
            yaxis={
                'title': 'Number Of Test Runs',
            },
            barmode='stack'
        )
    }

    return figure


def get_current_week_testruns_table(df, testcycle, testgroup, title, colormap):
    df = get_testruns_for_current_week(df=df, testcycle_key=testcycle, testgroup_key=testgroup)
    if df is None:
        return html.P('No test runs found!')

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