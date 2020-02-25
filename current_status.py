import plotly.graph_objects as go
import dash_core_components as dcc
from testrun_utils import filter_df, get_status_names


def get_current_status_pie_chart(df, testcycle, testcase, title='Current Status', colormap=None):
    df1 = filter_df(df, testcycle, testcase)
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

    data=[go.Pie(labels=status_names, values=values,
                                 textinfo='label+percent',
                                 insidetextorientation='radial',
                                 marker_colors=pie_colors
                                 )]

    fig = go.Figure(data=data, layout=dict(title=title))
    return dcc.Graph(
            id='current-status',
            figure=fig)


def get_current_status_by_testcase_bar_chart(df, testcycle, testcase, title, colormap):
    df1 = filter_df(df, testcycle_key=testcycle, testcase_key=testcase)
    data = []
    x_axis = [x for x in df1.index]

    for status in get_status_names():
        y_axis = df1[status].values
        data.append(dict(name=set, x=x_axis, y=y_axis, type='bar',
                         text=y_axis,
                         textposition='auto',
                         marker=dict(color=colormap[status])))
    return dcc.Graph(
            id='testrun-status-by-set',
            figure = {
                'data': data,
                'layout': dict(
                    title=title,
                    xaxis={
                        'title': 'Testrun Sets',
                    },
                    yaxis={
                        'title': 'Number Of Test Runs',
                    },
                    barmode='stack'
                )
            }
        )


