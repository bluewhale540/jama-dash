import plotly.graph_objects as go
import pandas as pd
from dateutil import parser
from testrun_utils import get_testrun_status_historical, get_status_names


'''Generate the testrun line chart trace data

Parameters:
    df (dataframe): The test run data
    testcycle (stirng): The test cycle
    testgroup (string): The test group
    priority (string): The priority
    start_date (string): The earliest date to show
    test_deadline (string): The target date for all runs to be finished
    colormap (dict): The colors to use for the statuses
    treat_blocked_as_not_run (bool): Whether or not to treat blocked as not run
    treat_inprogress_as_not_run (bool): Whether or not to treat in progress runs as not run

Returns:
    data (list): Traces for each status over time
'''
def get_historical_status_line_traces(
        df, testcycle, testgroup, priority,
        start_date, test_deadline, colormap,
        treat_blocked_as_not_run=False,
        treat_inprogress_as_not_run=False):
    df1 = get_testrun_status_historical(df, testcycle_key=testcycle, testgroup_key=testgroup, priority_key=priority,
                                              start_date=start_date)
    if df1 is None:
        return []

    if treat_blocked_as_not_run:
        df1['NOT_RUN'] = df1['NOT_RUN'] + df1['BLOCKED']
        df1.drop(columns=['BLOCKED'])
    if treat_inprogress_as_not_run:
        df1['NOT_RUN'] = df1['NOT_RUN'] + df1['INPROGRESS']
        df1.drop(columns=['INPROGRESS'])

    # create historical status scatter graph
    deadline_x = []
    deadline_y = []

    x_list = [pd.to_datetime(d).date() for d in df1['date'].values]
    y_dict = {} # dict of y-axis with status name as key
    for status in get_status_names():
        y_dict[status] = df1[status].values

    display_required_burn = False
    if test_deadline is not None:
        tail = df1.tail(1)
        if not tail.empty:
            d = pd.to_datetime(tail.iloc[0]['date'])
            first_date = d.date()
            first_value = tail['NOT_RUN'].values[0]
            if first_value != 0:
                deadline_x = [first_date, test_deadline]
                deadline_y = [first_value, 0]
                display_required_burn = True

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
    # add required run rate trace
    if display_required_burn is True:
        data.append(go.Scatter(x=deadline_x,
                         y=deadline_y,
                         mode='lines',
                         name='required test run rate',
                         line=dict(dash='dash', color='black')))
    return data


'''Generate the test run line chart

Parameters:
    df (dataframe): The data
    testcycle (string): The test cycle
    testgroup (string): The test group
    priority (string): The priority
    colormap (dict): The colors to use for each status

Returns:
    fig: The line chart
'''
def get_historical_status_line_chart(df, testcycle, testgroup, priority, title, colormap, **kwargs):

    start_date = None
    val = kwargs.get('start_date')
    if val is not None:
        start_date = parser.parse(val)

    test_deadline = None
    val = kwargs.get('test_deadline')
    if val is not None:
        test_deadline = parser.parse(val)

    treat_blocked_as_not_run = False
    val = kwargs.get('treat_blocked_as_not_run')
    if val is not None:
        treat_blocked_as_not_run = True

    treat_inprogress_as_not_run = False
    val = kwargs.get('treat_inprogress_as_not_run')
    if val is not None:
        treat_inprogress_as_not_run = True

    traces = get_historical_status_line_traces(df, testcycle, testgroup, priority,
        start_date, test_deadline, colormap,
        treat_blocked_as_not_run,
        treat_inprogress_as_not_run)

    fig = dict(data=traces)
    return fig

