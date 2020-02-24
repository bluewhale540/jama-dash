import plotly.graph_objects as go
import dash_core_components as dcc

def get_current_status_pie_chart(client, project, testplan, testcycle, title, colormap):
    df = client.get_testrun_status_current(project_key=project,
                                           testplan_key=testplan,
                                           testcycle_key=testcycle)
    # create pie chart
    pie_colors = []

    for status in df.columns:
        pie_colors.append(colormap[status])

    data=[go.Pie(labels=df.columns, values=df.iloc[0].values.tolist(),
                                 textinfo='label+percent',
                                 insidetextorientation='radial',
                                 marker_colors=pie_colors
                                 )]

    fig = go.Figure(data=data, layout=dict(title=title))
    return dcc.Graph(
            id='current-status',
            figure=fig)
