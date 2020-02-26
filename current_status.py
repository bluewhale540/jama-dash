import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
from testrun_utils import filter_df, get_status_names
import pandas as pd


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


def get_testcase_status_bar_chart(df, testcycle, testcase, title, colormap, status_list):
    if len(status_list) == 0:
        return html.P('Status List is empty')

    if testcase is not None:
        return html.P('Please select All Test Cases')

    df1 = filter_df(df, testcycle_key=testcycle)

    testcases = [x for x  in iter(df1.testcase.unique())]

    data = []
    for tc in testcases:
        df2 = filter_df(df, testcase_key=tc)
        counts = df2['status'].value_counts()
        total = 0
        for s in status_list:
            val = counts.get(s)
            if val is not None:
                total += val
        if total == 0:
            continue

        d = {
            'testcase': tc,
            'total': total
        }
        d.update(counts)
        data.append(d)

    if len(data) == 0:
        return html.P(f'No test cases with status in {status_list}')

    df3 = pd.DataFrame(data, columns=['testcase', 'total'] + status_list)
    df3.sort_values(by=['total'], ascending=False, inplace=True)
    data = []
    x_axis = df3['testcase'].values

    for status in status_list:
        y_axis = df3[status]
        data.append(dict(name=status, x=x_axis, y=y_axis, type='bar',
                         text=y_axis,
                         textposition='auto',
                         marker=dict(color=colormap[status])))
    return dcc.Graph(
            id='testcase-failed-blocked',
            figure = {
                'data': data,
                'layout': dict(
                    title=title,
                    xaxis={
                        'title': 'Testcases',
                        'automargin': True,
                    },
                    yaxis={
                        'title': 'Number Of Test Runs',
                    },
                    barmode='stack'
                )
            }
        )


