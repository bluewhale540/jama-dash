import os
from py_jama_rest_client.client import JamaClient
import login_dialog
import pandas as pd
import plotly.graph_objects as go
import numpy as np


jama_url = os.environ['JAMA_API_URL']
jama_api_username = os.environ['JAMA_API_USERNAME']
jama_api_password = os.environ['JAMA_API_PASSWORD']

if jama_api_password is None or jama_api_username is None:
    # get Jama/contour login credentials using a dialog box
    while True:
        result = login_dialog.run()
        if result is None:
            continue
        break
    jama_api_username = result[0]
    jama_api_password = result[1]

# Create the JamaClient
try:
    jama_client = JamaClient(host_domain=jama_url, credentials=(jama_api_username, jama_api_password))
    # get item types
    item_types = jama_client.get_item_types()
except Exception as err:
    print('Error: cannot connect to Jama server -', err)
    exit(-1)

#project_type = next(x for x in item_types if x['typeKey'] == 'TSTPL')['id']
testplan_type = next(x for x in item_types if x['typeKey'] == 'TSTPL')['id']
testcycle_type = next(x for x in item_types if x['typeKey'] == 'TSTCY')['id']

# find our project id
projects = jama_client.get_projects()

projects = [x for x in projects if x.get('projectKey') is not None and x['projectKey'] == 'PIT' and x['isFolder'] is False]

project_id = projects[0]['id']

# get all test plans in project
testplans = jama_client.get_abstract_items(item_type=testplan_type,
                                           project=project_id ,
                                           contains='GX5_Phase1_Stage1_FAT2_Dry_Run') #project=269

# there should only be one test plan with this name
testplan_id = testplans[0]['id']

# get all test cycles in project
testcycles = jama_client.get_abstract_items(item_type=testcycle_type, project=project_id) #contains='GX5_P1S1F2-DR_IQ800_Datapath'

# remove test cycles that do not belong to our test plan
testcycles = [x for x in testcycles if x['fields']['testPlan'] == testplan_id]


# create a dctionary of data frames for all test cycles
df_cycles = {}
df_overall = None
for x in testcycles:
    testcycle_id = x['id']
    testcycle_name = x['fields']['name']
    testruns = jama_client.get_testruns(test_cycle_id=testcycle_id)
    data_list = list()
    for y in testruns:
        data_list.append([testcycle_name,
                    y['fields']['name'],
                    y['modifiedDate'],
                    y['fields']['testRunStatus']])
    # create a data frame from the test runs for this test cycle
    df = pd.DataFrame(data_list, columns=['cycle', 'name', 'date', 'status'])
    # convert 'date' column dtype to datetime
    df['date'] = pd.to_datetime(df['date'])

    if df_overall is None:
        df_overall = df
    else:
        df_overall = pd.concat([df_overall, df])
    df_cycles[testcycle_name] = df

#df_cycles['All'] = df_overall

status_counts = df_overall['status'].value_counts()
status_counts = status_counts.rename('Overall')
# Build chart data
x_axis = ['All test cycles']
for x in testcycles:
    x_axis.append(x['fields']['name'])

chart_df = pd.DataFrame(columns=['cycle', 'NOT_RUN', 'PASSED', 'FAILED', 'BLOCKED', 'INPROGRESS'])
chart_df = chart_df.set_index(['cycle'])
chart_df = chart_df.append(status_counts)

for cycle in df_cycles.keys():
    status_counts = df_cycles[cycle]['status'].value_counts()
    status_counts = status_counts.rename(cycle)
    chart_df = chart_df.append((status_counts))

colors_dict = { 'NOT_RUN': 'gray', 'PASSED': 'green', 'FAILED': 'red', 'BLOCKED': 'blue', 'INPROGRESS': 'yellow'}
chart_data = []
for status, column in chart_df.iteritems():
    chart_data.append(go.Bar(name=status, x=column.index.tolist(), y=column.values.tolist(), marker_color=colors_dict[status]))

fig = go.Figure(data=chart_data)
# Change the bar mode
fig.update_layout(barmode='stack', title_text='PIT FAT2 Dry Run Status')
fig.show()