from jama_client import jama_client
import dash_core_components as dcc
from datetime import timedelta

def get_weekly_status_chart(client, project, testplan, testcycle, title, colormap):
    df = client.get_testrun_status_by_planned_weeks(project_key=project,
                                                    testplan_key=testplan,
                                                    testcycle_key=testcycle)
    data = []
    fmt_date = lambda x: x.strftime('%b %d') + ' - ' + (x + timedelta(days=4)).strftime('%b %d') \
        if x is not None else 'Unassigned'
    x_axis = [fmt_date(x) for x in df['planned_week'].values]

    for status in client.get_status_names():
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

