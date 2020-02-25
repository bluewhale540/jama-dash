import plotly.graph_objects as go
import dash_core_components as dcc
import pandas as pd
from testrun_utils import get_testrun_status_historical, get_status_names

def get_historical_status_line_chart(
        df, testcycle, testcase,
        start_date, test_deadline, title, colormap,
        treat_blocked_as_not_run=False,
        treat_inprogress_as_not_run=False):
    df = get_testrun_status_historical(df, testcycle_key=testcycle, testcase_key=testcase,
                                              start_date=pd.to_datetime(start_date))
    if treat_blocked_as_not_run:
        df['NOT_RUN'] = df['NOT_RUN'] + df['BLOCKED']
        df.drop(columns=['BLOCKED'])
    if treat_inprogress_as_not_run:
        df['NOT_RUN'] = df['NOT_RUN'] + df['INPROGRESS']
        df.drop(columns=['INPROGRESS'])

    # create historical status scatter graph
    deadline_x = []
    deadline_y = []

    x_list = [pd.to_datetime(d).date() for d in df['date'].values]
    y_dict = {} # dict of y-axis with status name as key
    for status in get_status_names():
        y_dict[status] = df[status].values
    if test_deadline is not None:
        tail = df.tail(1)
        current_date = pd.to_datetime(tail['date'].values[0])
        deadline_x = [current_date, pd.to_datetime(test_deadline)]
        deadline_y = [tail['NOT_RUN'].values[0], 0]

    # Add traces
    data = []
    for status in get_status_names():
        if status == 'INPROGRESS' and treat_inprogress_as_not_run is True:
            continue
        if status == 'BLOCKED' and treat_blocked_as_not_run is True:
            continue
        data.append(go.Scatter(x=x_list,
                         y=y_dict[status],
                         mode='lines',
                         name=status,
                         line=dict(color=colormap[status])))
    # add deadline meeting trace
    if test_deadline is not None:
        data.append(go.Scatter(x=deadline_x,
                         y=deadline_y,
                         mode='lines',
                         name='required burn rate',
                         line=dict(dash='dash', color='black')))
    fig = go.Figure(data=data, layout=dict(title=title))
    return dcc.Graph(
            id='historical-status',
            figure=fig)



def get_historical_status_line_chart_old(
        client, project, testplan, testcycle,
        start_date, test_deadline, title, colormap,
        treat_blocked_as_not_run=False,
        treat_inprogress_as_not_run=False):
    df = client.get_testrun_status_historical(project_key=project,
                                              testplan_key=testplan,
                                              testcycle_key=testcycle,
                                              start_date=pd.to_datetime(start_date))
    if treat_blocked_as_not_run:
        df['NOT_RUN'] = df['NOT_RUN'] + df['BLOCKED']
        df.drop(columns=['BLOCKED'])
    if treat_inprogress_as_not_run:
        df['NOT_RUN'] = df['NOT_RUN'] + df['INPROGRESS']
        df.drop(columns=['INPROGRESS'])

    # create historical status scatter graph
    deadline_x = []
    deadline_y = []

    x_list = [pd.to_datetime(d).date() for d in df['date'].values]
    y_dict = {} # dict of y-axis with status name as key
    for status in client.get_status_names():
        y_dict[status] = df[status].values
    if test_deadline is not None:
        tail = df.tail(1)
        current_date = pd.to_datetime(tail['date'].values[0])
        deadline_x = [current_date, pd.to_datetime(test_deadline)]
        deadline_y = [tail['NOT_RUN'].values[0], 0]

    # Add traces
    data = []
    for status in client.get_status_names():
        if status == 'INPROGRESS' and treat_inprogress_as_not_run is True:
            continue
        if status == 'BLOCKED' and treat_blocked_as_not_run is True:
            continue
        data.append(go.Scatter(x=x_list,
                         y=y_dict[status],
                         mode='lines',
                         name=status,
                         line=dict(color=colormap[status])))
    # add deadline meeting trace
    if test_deadline is not None:
        data.append(go.Scatter(x=deadline_x,
                         y=deadline_y,
                         mode='lines',
                         name='required burn rate',
                         line=dict(dash='dash', color='black')))
    fig = go.Figure(data=data, layout=dict(title=title))
    return dcc.Graph(
            id='historical-status',
            figure=fig)


