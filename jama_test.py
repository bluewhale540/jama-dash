import os
from py_jama_rest_client.client import JamaClient
import login_dialog
import pandas as pd
import plotly.graph_objects as go



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
    colormap = {'NOT_RUN': 'gray', 'PASSED': 'green', 'FAILED': 'red', 'BLOCKED': 'blue', 'INPROGRESS': 'orange'}

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
