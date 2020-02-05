import os
import pandas as pd
import plotly.graph_objects as go
from jama_client import jama_client
import login_dialog
from datetime import datetime
import pytz
from tzlocal import get_localzone

def display_current_status_chart(df_status, status_names, colormap, title):
    # create pie chart
    pie_colors = []
    for index in df_status.index:
        pie_colors.append(colormap[index])
    fig = go.Figure(data=[go.Pie(labels=df_status.index, values=df_status.values,
                                 textinfo='label+percent',
                                 insidetextorientation='radial',
                                 marker_colors=pie_colors
                                 )])
    fig.update_layout(title_text=title)
    fig.show()

def display_historical_status_chart(df_status, status_names, colormap, title, deadline=None):
    # create historical status scatter graph
    fig = go.Figure()

    x_axis = [pd.to_datetime(d).date() for d in df_status['date'].values]
    # Add traces
    for status in status_names:
        y_axis = df_status[status].values
        fig.add_trace(go.Scatter(x=x_axis, y=y_axis,
                                 mode='lines',
                                 name=status,
                                 line=dict(color=colormap[status])
                                 ))
    # add deadline meeting trace
    tail = df_status.tail(1)
    current_date = pd.to_datetime(tail['date'].values[0])
    deadline_x = [current_date, pd.to_datetime(deadline)]
    deadline_y = [tail['NOT_RUN'].values[0], 0]
    fig.add_trace(go.Scatter(x=deadline_x, y=deadline_y,
                             mode='lines',
                             line=dict(dash='dash', color='black')))
    fig.update_layout(title_text=title)
    fig.show()

def main():
    jama_url = os.environ.get('JAMA_API_URL')
    jama_api_username = os.environ.get('JAMA_API_USERNAME')
    jama_api_password = os.environ.get('JAMA_API_PASSWORD')

    if jama_url is None:
        jama_url = 'https://paperclip.idirect.net'

    if jama_api_password is None or jama_api_username is None:
        # get Jama/contour login credentials using a dialog box
        while True:
            result = login_dialog.run()
            if result is None:
                exit(1)
            break
        jama_api_username = result[0]
        jama_api_password = result[1]

    client = jama_client()
    if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password):
        exit(1)
    # list of project, test plan and chart title
    testing_list = [
        ('PIT', 'GX5_Phase1_Stage1_FAT2_Dry_Run', 'PIT FAT2 Dry Run Status'),
        ('VRel', '2.7.1-3.1-FAT2 Testing', 'SIT FAT2 Testing Status')
    ]

    colormap = \
        {'NOT_RUN': 'gray', 'PASSED': 'green', 'FAILED': 'firebrick', 'BLOCKED': 'royalblue', 'INPROGRESS': 'orange'}
    status_names = client.get_status_names()

    for project, testplan, title in testing_list:
        testcycle_db = client.retrieve_testcycles(project_key=project, testplan_key=testplan)
        if testcycle_db is None:
            exit(1)

        testcycles = [None]
        for id, cycle in testcycle_db:
            testcycles.append(cycle)

        for cycle in testcycles:
            chart_title = title
            if cycle is not None:
                chart_title += ' (' + cycle + ')'
            df_status_by_date = client.get_testrun_status_historical(project_key=project,
                                                                     testplan_key=testplan,
                                                                     testcycle_key=cycle)
            if df_status_by_date is None:
                continue
            local_tz = get_localzone()
            deadline_date = datetime.strptime('2020-02-28-05:00:00', '%Y-%m-%d-%H:%M:%S').replace(tzinfo=pytz.utc).astimezone(local_tz)
            display_historical_status_chart(df_status=df_status_by_date,
                                            status_names=status_names,
                                            colormap=colormap,
                                            title=chart_title,
                                            deadline=deadline_date)

        for cycle in testcycles:
            df_status_current = client.get_testrun_status_current(project_key=project,
                                                                  testplan_key=testplan,
                                                                  testcycle_key=cycle)
            if df_status_current is None:
                continue
            display_current_status_chart(df_status=df_status_current,
                                         status_names=status_names, colormap=colormap, title=chart_title)

if __name__ == '__main__':
    main()

