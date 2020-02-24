import dash_core_components as dcc

def get_current_status_by_set_bar_chart(client, project, testplan, testcycle, title, colormap):
    df = client.get_testrun_status_by_set(project_key=project,
                                        testplan_key=testplan,
                                        testcycle_key=testcycle)
    data = []
    x_axis = [x for x in df.index]

    for status in client.get_status_names():
        y_axis = df[status].values
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

