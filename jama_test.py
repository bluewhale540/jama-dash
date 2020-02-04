import os
from py_jama_rest_client.client import JamaClient
import login_dialog
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np



class jama_testplan_utils:
    testcycle_db = {} # DB of test cycles for the projects and test plans we want to track
    def __init__(self):
        # Test run DF columns
        self.df_columns = ['project', 'testplan', 'testcycle', 'testrun',
                                            'created_date', 'modified_date', 'status']
        # Test run DF
        self.df = pd.DataFrame([], columns=self.df_columns)
        self.df['created_date'] = pd.to_datetime(self.df['created_date'])
        self.df['modified_date'] = pd.to_datetime(self.df['modified_date'])

    def connect(self, url, username, password):
        # Create the Jama client
        try:
            self.jama_client = JamaClient(host_domain=url, credentials=(username, password))
            # get item types for test plans and cycles
            self.item_types = self.jama_client.get_item_types()
            self.testplan_type = next(x for x in self.item_types if x['typeKey'] == 'TSTPL')['id']
            self.testcycle_type = next(x for x in self.item_types if x['typeKey'] == 'TSTCY')['id']
        except Exception as err:
            print('Jama server connection ERROR! -', err)
            return False
        return True

    def retrieve_testcycles(self, project_key, testplan_key, update=False):
        testcycles = self.testcycle_db.get((project_key, testplan_key))
        if not update and self.testcycle_db is not None and testcycles is not None:
            # already in DB
            print('Test cycles for project {} and test plan {} already in DB. Will not re-query'
                  .format(project_key, testplan_key))
            return testcycles

        # get a list of all projects - not efficient but py_jama_rest_client does not support
        # searching using a project key
        # TODO: use REST API directly
        print('querying for project {}...'.format(project_key))
        projects = self.jama_client.get_projects()
        # find our project id
        projects = [x for x in projects if
                    x.get('projectKey') is not None and x['projectKey'] == project_key and x['isFolder'] is False]
        if len(projects) == 0:
            print('Error: Cannot find a project with name {}'.format(project_key))
            return None
        # we will assume that Jama only allows you to create projects with unique names
        project_id = projects[0]['id']
        print('found project {}!'.format(project_key))
        print('querying for test plan {}...'.format(testplan_key))
        # get all test plans in project
        testplans = self.jama_client.get_abstract_items(item_type=self.testplan_type,
                                                   project=project_id,
                                                   contains=testplan_key)
        if len(testplans) == 0:
            print('Error: Cannot find a testplan with name {}'.format(testplan_key))
            return None
        # we will assume that within a project, Jama only allows you to create testplans with unique names
        testplan_id = testplans[0]['id']
        print('found test plan {}!'.format(testplan_key))
        print('querying for test cycles under test plan {}...'.format(testplan_key))
        # get all test cycles in project
        tc = self.jama_client.get_abstract_items(item_type=self.testcycle_type,
                                                    project=project_id)  # contains='GX5_P1S1F2-DR_IQ800_Datapath'
        # remove test cycles that do not belong to our test plan
        tc = [x for x in tc if x['fields']['testPlan'] == testplan_id]
        if len(tc) == 0:
            print('Error: Cannot find any test cycles under test plan {}'.format(testplan_key))
            return None
        print('found {} test cycles under test plan {}!'.format(len(tc), testplan_key))

        # we just need test cycle id and name for our purposes
        testcycles = [(x['id'], x['fields']['name']) for x in tc]
        self.testcycle_db[(project_key, testplan_key)] = testcycles
        return testcycles

    def retrieve_testruns(self, project_key, testplan_key, update=True):
        # check for existing test run data
        if not self.df.empty:
            query_df = self.df[self.df.project.isin([project_key]) & self.df.testplan.isin([testplan_key])]
            if update == False and query_df.shape[0] != 0:
                return query_df
            # either update is True or query_df is empty - either case lets remove any existing runs for this test plan
            self.df = self.df[self.df['project'] != project_key or self.df['testplan'] != testplan_key]

        testcycles = self.testcycle_db.get((project_key, testplan_key))
        if testcycles is None:
            print('No test cycles found for test plan. please call retrieve_testcycles() first')
            return None

        testruns_to_add = []
        for (testcycle_id, testcycle_name) in testcycles:
            testruns_raw = self.jama_client.get_testruns(test_cycle_id=testcycle_id)
            for y in testruns_raw:
                testruns_to_add.append([project_key,
                                     testplan_key,
                                     testcycle_name,
                                     y['fields']['name'],
                                     y['createdDate'],
                                     y['modifiedDate'],
                                     y['fields']['testRunStatus']])
        # append the retrieved test runs to the existing data frame
        new_df = pd.DataFrame(testruns_to_add, columns=['project', 'testplan', 'testcycle', 'testrun',
                                            'created_date', 'modified_date', 'status'])
        new_df['created_date'] = pd.to_datetime(new_df['created_date'])
        new_df['modified_date'] = pd.to_datetime(new_df['modified_date'])
        self.df = self.df.append(new_df)
        return new_df

def main():
    jama_url = os.environ['JAMA_API_URL']
    jama_api_username = os.environ['JAMA_API_USERNAME']
    jama_api_password = os.environ['JAMA_API_PASSWORD']
    #project = 'PIT'
    #testplan = 'GX5_Phase1_Stage1_FAT2_Dry_Run'
    #title = 'PIT FAT2 Dry Run Status'
    project = 'VRel'
    testplan = '2.7.1-3.1-FAT2 Testing'
    title = 'SIT FAT2 Testing'

    if jama_api_password is None or jama_api_username is None:
        # get Jama/contour login credentials using a dialog box
        while True:
            result = login_dialog.run()
            if result is None:
                continue
            break
        jama_api_username = result[0]
        jama_api_password = result[1]

    client = jama_testplan_utils()
    if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password):
        exit(1)
    testcycle_db = client.retrieve_testcycles(project_key=project, testplan_key=testplan)
    if testcycle_db is None:
        exit(1)
    testrun_df = client.retrieve_testruns(project_key=project, testplan_key=testplan)
    if testrun_df is None:
        exit(1)

    status_counts = testrun_df['status'].value_counts()
    colormap = {'NOT_RUN': 'gray', 'PASSED': 'green', 'FAILED': 'red', 'BLOCKED': 'blue', 'INPROGRESS': 'yellow'}

    pie_colors = []
    for index in status_counts.index:
        pie_colors.append(colormap[index])
    fig = go.Figure(data=[go.Pie(labels=status_counts.index, values=status_counts.values,
                                 textinfo='label+percent',
                                 insidetextorientation='radial',
                                 marker_colors=pie_colors
                                 )])
    fig.update_layout(title_text=title)
    fig.show()

if __name__ == '__main__':
    main()




'''

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
'''
'''
chart_data = []
for status, column in chart_df.iteritems():
    chart_data.append(go.Bar(name=status, x=column.index.tolist(), y=column.values.tolist(), marker_color=colors_dict[status]))

fig = go.Figure(data=chart_data)
# Change the bar mode
fig.update_layout(barmode='stack', title_text='PIT FAT2 Dry Run Status')
fig.show()

'''

'''
# Pie chart subplots
num_traces = chart_df.shape[0]
num_rows = 3
num_cols = int(num_traces/3) +1
specs = [
    [{'type':'domain'},]*num_cols,
] * num_rows

fig = make_subplots(
    rows=num_rows, cols=num_cols,
    specs=specs,
    subplot_titles=list(chart_df.index.values)
)
fig.print_grid()
next_row = 1
next_col = 1
for test_cycle, row in chart_df.iterrows():
    fig.add_trace(go.Pie(name=test_cycle, labels=row.index, values=row.values, textinfo='label+percent',
                             insidetextorientation='radial', scalegroup='one'),
                  row=next_row,
                  col=next_col
                  )
    next_col += 1
    if next_col > num_cols:
        next_col = 1
        next_row += 1


fig.update_layout(height=800, width=600, title_text='PIT FAT2 Dry Run Status')
fig.show()

'''
'''
pie_row = chart_df.loc['Overall']
pie_colors = []
for index in pie_row.index:
    pie_colors.append(colors_dict[index])
fig = go.Figure(data=[go.Pie(labels=pie_row.index, values=pie_row.values,
                             textinfo='label+percent',
                             insidetextorientation='radial',
                             marker_colors=pie_colors
                             )])
fig.update_layout(title_text='PIT FAT2 Dry Run Status')
fig.show()
'''