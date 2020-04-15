import dash_html_components as html
from testrun_utils import STATUS_NOT_RUN, STATUS_BLOCKED, STATUS_FAILED, STATUS_PASSED, STATUS_INPROGRESS
from testrun_utils import filter_df, get_testruns_for_current_week, get_status_names
import pandas as pd
import dash_table


def get_current_status_pie_chart(df, testcycle, testgroup, colormap=None):
    df1 = filter_df(df, testcycle_key=testcycle, testgroup_key=testgroup)
    counts = df1['status'].value_counts()

    status_names = []
    values = []
    for index, value in counts.items():
        status_names.append(index)
        values.append(value)

    # create pie chart
    pie_colors = []
    if colormap is not None:
        for status in status_names:
            pie_colors.append(colormap[status])

    data = [
        dict(type='pie',
            labels=status_names,
            values=values,
            texttemplate='%{label}<br>%{value:,s} test runs<br>(%{percent})',
            textinfo='text',
            insidetextorientation='radial',
            marker_colors=pie_colors)]

    fig = dict(data=data, layout=dict(height=600))
    return fig


def get_testgroup_status_bar_chart(df, testcycle, testgroup, colormap, **kwargs):

    status_list = []
    if kwargs.get('show_not_run') is not None and kwargs['show_not_run'] is True:
        status_list.append(STATUS_NOT_RUN)
    if kwargs.get('show_inprogress') is not None and kwargs['show_inprogress'] is True:
        status_list.append(STATUS_INPROGRESS)
    if kwargs.get('show_blocked') is not None and kwargs['show_blocked'] is True:
        status_list.append(STATUS_BLOCKED)
    if kwargs.get('show_passed') is not None and kwargs['show_passed'] is True:
        status_list.append(STATUS_PASSED)
    if kwargs.get('show_failed') is not None and kwargs['show_failed'] is True:
        status_list.append(STATUS_FAILED)

    df1 = filter_df(df, testcycle_key=testcycle)

    testgroups = [x for x  in iter(df1.testgroup.unique())]

    data = []
    for group in testgroups:
        df2 = filter_df(df, testgroup_key=group)
        counts = df2['status'].value_counts()
        total = 0
        for s in status_list:
            val = counts.get(s)
            if val is not None:
                total += val
        if total == 0:
            continue

        d = {
            'testgroup': group,
            'total': total
        }
        d.update(counts)
        data.append(d)

    if len(data) == 0:
        return html.P(f'No test cases with status in {status_list}')

    df3 = pd.DataFrame(data, columns=['testgroup', 'total'] + status_list)
    df3.sort_values(by=['total'], ascending=False, inplace=True)
    data = []
    x_axis = df3['testgroup'].values

    for status in status_list:
        y_axis = df3[status]
        data.append(dict(name=status, x=x_axis, y=y_axis, type='bar',
                         text=y_axis,
                         textposition='auto',
                         marker=dict(color=colormap[status])))
    figure = dict(
        data=data,
        layout=dict(
            height=800,
            textangle=-45,
            yaxis=dict(title='Number Of Test Runs'),
            barmode='stack',
            autosize=True))
    return figure



def get_testruns_table(df, testcycle, testgroup, colormap, **kwargs):
    if kwargs.get('current_week') is not None and kwargs['current_week'] is True:
        df1 = get_testruns_for_current_week(df=df, testcycle_key=testcycle, testgroup_key=testgroup)
    else:
        df1 = df

    if df1 is None:
        return html.P('No test runs found!')

    style_cell_conditional = [
                                 {
                                     'if': {'column_id': c},
                                     'textAlign': 'left'
                                 } for c in df1.columns

                             ]
    '''
    style_cell_conditional += [
        {
            'if': {'column_id': 'testcycle'},
            'maxWidth': '30px'
        },
        {
            'if': {'column_id': 'status'},
            'maxWidth': '24px'
        },
        {
            'if': {'column_id': 'execution_date'},
            'maxWidth': '26px'
        },
        {
            'if': {'column_id': 'assigned_to'},
            'maxWidth': '24px'
        },

    ]
    '''

    table = dash_table.DataTable(
        id='datatable-testruns',
        columns=[
            dict(name=i, id=i, deletable=False, selectable=False, hideable='last') for i in df1.columns
        ],
        data=df1.to_dict('records'),
        editable=False,
        filter_action='native',
        sort_action='native',
        page_size=10,
        persistence=True,
        export_columns='all',
        export_format='csv',
        export_headers='names',
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_cell_conditional=style_cell_conditional,
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