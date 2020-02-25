import plotly.graph_objects as go
import dash_core_components as dcc
from testrun_utils import filter_df

def get_current_status_pie_chart(df, testcycle=None, testcase=None, title='Current Status', colormap=None):
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
