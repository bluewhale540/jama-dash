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

def display_historical_status_chart(df_list, status_names, colormap, title_list, deadline=None):
    if df_list is None or len(df_list) == 0:
        print('empty data set. Aborting line chart')
        return

    if len(df_list) != len(title_list):
        print('inconsistency between data and title lists. Aboting line chart')
        return

    # create historical status scatter graph
    x_list = [] # list of x axis data
    y_list = [] # list of dict of y-axis with status name as key
    deadline_x_list = []
    deadline_y_list = []
    for df in df_list:
        x_list.append([pd.to_datetime(d).date() for d in df['date'].values])
        y_dict = {}
        for status in status_names:
            y_dict[status] = df[status].values
        y_list.append(y_dict)
        if deadline is not None:
            tail = df.tail(1)
            current_date = pd.to_datetime(tail['date'].values[0])
            deadline_x = [current_date, pd.to_datetime(deadline)]
            deadline_y = [tail['NOT_RUN'].values[0], 0]
            deadline_x_list.append(deadline_x)
            deadline_y_list.append(deadline_y)

    df = df_list[0]
    x_axis = x_list[0]
    title = title_list[0]
    # Add traces
    data = []
    for status in status_names:
        y_axis = y_list[0][status]
        data.append(go.Scatter(x=x_axis, y=y_axis,
                                 mode='lines',
                                 name=status,
                                 line=dict(color=colormap[status])
                                 ))
    # add deadline meeting trace
    if deadline is not None:
        data.append(go.Scatter(x=deadline_x_list[0], y=deadline_y_list[0],
                                 mode='lines', name='required burn rate',
                                 line=dict(dash='dash', color='black')))

    updatemenus= []
    menu = {}
    menu['buttons'] = []
    for i in range(0, len(x_list)):
        button = {}
        button['method'] = 'restyle'
        button['label'] = title_list[i]
        button['args'] = []
        arg = {}
        arg['x'] = []
        arg['y'] = []
        for status in status_names:
            arg['x'].append(x_list[i])
            arg['y'].append(y_list[i][status])
        arg['x'].append(deadline_x_list[i])
        arg['y'].append(deadline_y_list[i])
        arg['title'] = title_list[i]
        button['args'].append(arg)
        menu['buttons'].append(button)
    menu['direction'] = 'down'
    menu['showactive'] = True
    updatemenus.append(menu)
    layout = go.Layout(updatemenus=updatemenus, title=title_list[0])
    fig = go.Figure(data=data, layout=layout)
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

    client = jama_client(blocking_as_not_run=True, inprogress_as_not_run=True)
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

        testcycles = [None,]
        for id, cycle in testcycle_db:
            testcycles.append(cycle)
        title_list = []
        df_list = []
        for cycle in testcycles:
            if cycle is None:
                title_list.append(title)
            else:
                title_list.append(cycle)

            df = client.get_testrun_status_historical(project_key=project,
                                                                     testplan_key=testplan,
                                                                     testcycle_key=cycle)
            if df is None:
                continue
            df_list.append(df)

        local_tz = get_localzone()
        deadline_date = datetime.strptime('2020-02-28-05:00:00', '%Y-%m-%d-%H:%M:%S').replace(tzinfo=pytz.utc).astimezone(local_tz)
        display_historical_status_chart(df_list=df_list,
                                        status_names=status_names,
                                        colormap=colormap,
                                        title_list=title_list,
                                        deadline=deadline_date)

'''
        for cycle in testcycles:
            df_status_current = client.get_testrun_status_current(project_key=project,
                                                                  testplan_key=testplan,
                                                                  testcycle_key=cycle)
            if df_status_current is None:
                continue
            display_current_status_chart(df_status=df_status_current,
                                         status_names=status_names, colormap=colormap, title=chart_title)
'''

if __name__ == '__main__':
    main()

