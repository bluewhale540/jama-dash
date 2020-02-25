from jama_client import jama_client
import testrun_utils
import dash_core_components as dcc
from datetime import timedelta

def get_weekly_status_bar_chart(df, testcycle, testcase, title, colormap):
    df1 = testrun_utils.get_testrun_status_by_planned_weeks(df, testcycle_key=testcycle, testcase_key=testcase)
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
    return dcc.Graph(
            id='weekly-status',
            figure = {
                'data': data,
                'layout': dict(
                    title=title,
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
