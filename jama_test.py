import os
from py_jama_rest_client.client import JamaClient
import login_dialog
import pandas as pd
import plotly.graph_objects as go



def print_fields(obj):
    # Print each field
    for field_name, field_data in obj.items():

        # If one of the fields(i.e. "fields") is a dictionary then print its subfields indented.
        if isinstance(field_data, dict):
            print(field_name + ':')
            # Print each sub field
            for sub_field_name in field_data:
                sub_field_data = field_data[sub_field_name]
                print('\t' + sub_field_name + ': ' + str(sub_field_data))

        # If this field is not a dictionary just print its field.
        else:
            print(field_name + ': ' + str(field_data))
    return

# Setup your Jama instance url, username, and password.
# You may use environment variables, or enter your information directly.
# Reminder: Follow your companies security policies for storing passwords.
jama_url = os.environ['JAMA_API_URL']
#jama_api_username = os.environ['JAMA_API_USERNAME']
#jama_api_password = os.environ['JAMA_API_PASSWORD']

# get Jama/contour login credentials
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
        df_overall.append(df)
    df_cycles[testcycle_name] = df

df_cycles['All'] = df_overall

status_counts = df_overall['status'].value_counts()

# Build chart data
x_axis = ['Overall']
chart_data = []
for index, value in status_counts.items():
    chart_data.append(go.Bar(name=index, x=x_axis, y=[value]))

fig = go.Figure(data=chart_data)
# Change the bar mode
fig.update_layout(barmode='stack')
fig.show()