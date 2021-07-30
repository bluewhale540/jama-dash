from py_jama_rest_client.client import JamaClient
from datetime import date
import pandas as pd
import requests
import re
from requests.exceptions import HTTPError


# Dataframe columns
COL_PROJECT = 'project'
COL_TESTPLAN = 'testplan'
COL_TESTCYCLE = 'testcycle'
COL_TESTGROUP = 'testgroup'
COL_TESTRUN = 'testrun'
COL_CREATED_DATE = 'created_date'
COL_MODIFIED_DATE = 'modified_date'
COL_EXECUTION_DATE = 'execution_date'
COL_PLANNED_WEEK = 'planned_week'
COL_STATUS = 'status'
COL_PRIORITY = 'priority'
COL_NETWORK_TYPE = 'network_type'
COL_ASSIGNED_TO = 'assigned_to'
COL_BUG_ID = 'bug_id'
COL_TEST_NETWORK = 'test_network'
COL_EXECUTION_METHOD = 'execution_method'


class jama_client:
    url = None
    username = None
    password = None
    testcycle_db = {}  # DB of test cycles for the projects and test plans we want to track
    planned_weeks_lookup = {}  # dict of planned week id to name
    planned_weeks = [] # sorted list of start dates of planned weeks
    user_id_lookup = {} # dict of user ids to names
    priority_id_lookup = {} # dict of priority ids to names
    network_type_id_lookup = {} # dict of network ids to names
    test_network_id_lookup = {} # dict of test network ids to names
    execution_method_id_lookup = {} #dict of execution method ids to names

    def __repr__(self):
        return f'{self.__class__.__name__})'

    def __init__(self, blocking_as_not_run=False, inprogress_as_not_run=False):
        # Test run DF columns
        self.df_columns = ['project', 'testplan', 'testcycle', 'testrun',
                           'created_date', 'modified_date', 'status']
        # Test run DF
        self.df = pd.DataFrame([], columns=self.df_columns)
        self.df['created_date'] = pd.to_datetime(self.df['created_date'])
        self.df['modified_date'] = pd.to_datetime(self.df['modified_date'])
        self.blocking_as_not_run = blocking_as_not_run
        self.inprogress_as_not_run = inprogress_as_not_run
        self.status_list = ['NOT_RUN', 'PASSED', 'FAILED']
        if not inprogress_as_not_run:
            self.status_list.append('INPROGRESS')
        if not blocking_as_not_run:
            self.status_list.append('BLOCKED')

    def __get_user_info_from_jama(self, user_id):
        try:
            response = requests.get(self.url + '/rest/latest/users/' + str(user_id), auth=(self.username, self.password))
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
            return ''
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
            return ''
        else:
            data = response.json().get('data')
            if data is None:
                return ''
            first_name = data['firstName']
            last_name = data['lastName']
            return first_name + ' ' + last_name

    # query the name for a user id
    def __get_user_from_id(self, user_id):
        if user_id is None:
            return ''
        user = self.user_id_lookup.get(user_id)
        if user is None:
            user = self.__get_user_info_from_jama(user_id)
            self.user_id_lookup[user_id] = user
        return user

    '''Gets the priority string from the ID
    
    Parameters:
        id (int): The ID of the priority
        
    Returns:
        The priority string
    '''
    def __get_priority_from_id(self, id):
        return self.priority_id_lookup.get(id) if id is not None else 'Unassigned'

    '''Gets the network type string from the ID
    
    Parameters:
        id (int): The ID of the network type
        
    Returns:
        The network type string
    '''
    def __get_network_type_from_id(self, id):
        return self.network_type_id_lookup.get(id) if id is not None else 'Unassigned'

    '''Gets the test network string from the ID
    
    Parameters:
        id (int): The ID of the test network
        
    Returns:
        The test network string
    '''
    def __get_test_network_from_id(self, id):
        return self.test_network_id_lookup.get(id) if id is not None else 'Unassigned'

    '''Gets the execution method string from the ID
    
    Parameters:
        id (int): The ID of the execution method
        
    Returns:
        The execution method string
    '''
    def __get_execution_method_from_id(self, id):
        return self.execution_method_id_lookup.get(id) if id is not None else 'Unassigned'

    '''Initializes the client connection

    Parameters:
        url (string): The base URL of the Jama instance
        username (string): The username for the Jama login
        password (string): The password for the Jama login
    '''
    def connect(self, url, username, password, ssl_verify=True):
        # Create the Jama client
        try:
            self.client = JamaClient(host_domain=url, credentials=(username, password), verify=ssl_verify)

            # get item types for test plans and cycles
            self.item_types = self.client.get_item_types()
            self.testplan_type = next(x for x in self.item_types if x['typeKey'] == 'TSTPL')['id']
            self.testcycle_type = next(x for x in self.item_types if x['typeKey'] == 'TSTCY')['id']

            self.testrun_obj = next(x for x in self.item_types if x['typeKey'] == 'TSTRN')
            # find the name for the 'Bug ID' field in a test run
            self.bug_id_field_name = None
            self.priority_field_name = None
            self.network_type_field_name = None
            self.planned_week_field_name = None
            self.test_network_field_name = None
            self.execution_method_field_name = None

            # find the name for the 'Planned week' field in a test run
            pick_lists = self.client.get_pick_lists()
            planned_week_id = next(x for x in pick_lists if x['name'] == 'Planned week')['id']
            priority_id = next(x for x in pick_lists if x['name'] == 'Priority')['id']
            network_type_id = next(x for x in pick_lists if x['name'] == 'Network')['id']
            test_network_id = next(x for x in pick_lists if x['name'] == 'Test Network')['id']
            execution_method_id = next(x for x in pick_lists if x['name'] == 'Execution Method')['id']

            for x in self.testrun_obj['fields']:
                if 'label' in x:
                    if x['label'] == 'Bug ID':
                        self.bug_id_field_name = x['name']
                        continue
                    if x['label'] == 'Priority':
                        self.priority_field_name = x['name']
                        continue
                    if x['label'] == 'Network Type':
                        self.network_type_field_name = x['name']
                        continue
                    if x['label'] == 'Test Network':
                        self.test_network_field_name = x['name']
                        continue
                    if x['label'] == 'Test Execution Method':
                        self.execution_method_field_name = x['name']
                        continue
                if 'pickList' in x and x['pickList'] == planned_week_id:
                    self.planned_week_field_name = x['name']
                    continue

            weeks = self.client.get_pick_list_options(planned_week_id)
            for x in weeks:
                week = x['name']
                self.planned_weeks_lookup[x['id']] = week
                self.planned_weeks.append(week)
            self.planned_weeks = sorted(self.planned_weeks)
            # Add None to the list for tests with unassigned weeks
            self.planned_weeks = [None] + self.planned_weeks

            priorities = self.client.get_pick_list_options(priority_id)
            for x in priorities:
                self.priority_id_lookup[x['id']] = x['name']

            network_types = self.client.get_pick_list_options(network_type_id)
            for x in network_types:
                self.network_type_id_lookup[x['id']] = x['name']

            test_networks = self.client.get_pick_list_options(test_network_id)
            for network in test_networks:
                self.test_network_id_lookup[network['id']] = network['name']

            execution_methods = self.client.get_pick_list_options(execution_method_id)
            for method in execution_methods:
                self.execution_method_id_lookup[method['id']] = method['name']

        except requests.exceptions.ConnectionError as err:
            print('Jama server connection ERROR! -', err)
            return False
        self.username = username
        self.password = password
        self.url = url
        return True

    '''Gets a list of testcycles in a given project and testplan

    Parameters:
        project_id (int): The ID of the project
        testplan_key (string): The name of the testplan
    
    Returns:
        testcycles (list): A list of testcycles in the testplan
    '''
    def retrieve_testcycles(self, project_id, testplan_key, update=False):
        testcycles = self.testcycle_db.get((project_id, testplan_key))
        if not update and self.testcycle_db is not None and testcycles is not None:
            return testcycles

        #print(f'querying for test plan {testplan_key}...')
        # get all test plans in project
        try:
            testplans = self.client.get_abstract_items(item_type=self.testplan_type,
                                                       project=project_id,
                                                       contains=testplan_key)
        except Exception as err:
            print('Jama server connection ERROR! -', err)
            return None

        if len(testplans) == 0:
            print('Error: Cannot find a testplan with name {}'.format(testplan_key))
            return None
        # we will assume that within a project, Jama only allows you to create testplans with unique names
        testplan_id = testplans[0]['id']
        print('found test plan {}!'.format(testplan_key))
        #print('querying for test cycles under test plan {}...'.format(testplan_key))
        # get all test cycles in project
        try:
            tc = self.client.get_abstract_items(item_type=self.testcycle_type,
                                                project=project_id)  # contains='GX5_P1S1F2-DR_IQ800_Datapath'
        except Exception as err:
            print('Jama server connection ERROR! -', err)
            return None

        # remove test cycles that do not belong to our test plan
        tc = [x for x in tc if x['fields']['testPlan'] == testplan_id]
        if len(tc) == 0:
            print('Error: Cannot find any test cycles under test plan {}'.format(testplan_key))
            return None
        print('found {} test cycles under test plan {}!'.format(len(tc), testplan_key))

        # we just need test cycle id and name for our purposes
        testcycles = [(x['id'], x['fields']['name']) for x in tc]
        self.testcycle_db[(project_id, testplan_key)] = testcycles
        return testcycles

    '''Gets a list of testruns in a given project, testplan, and testcycle

    Parameters:
        project_id (int): The ID of the project
        testplan_key (string): The name of the testplan
        testcycle_key (string): The name of the testcycle
    
    Returns:
        new_df (JSON): A JSON containing all the testruns
    '''
    def retrieve_testruns(self, project_id, testplan_key, testcycle_key=None, update=False):
        # check for cached test run data
        if not self.df.empty:
            print('checking cached test runs for project {} and test plan {}{}...'
                  .format(project_id, testplan_key,
                          '' if testcycle_key is None else ' and test cycle {}'.format(testcycle_key)))
            query_df = self.df[self.df.project.isin([project_id]) & self.df.testplan.isin([testplan_key])]
            if not query_df.empty and testcycle_key is not None:
                # filter by test cycle key
                query_df = query_df[query_df.testcycle.isin([testcycle_key])]
            if not query_df.empty:
                print('{} cached test runs found!'.format(query_df.shape[0]))
                if update == False:
                    # return cached test runs
                    return query_df
                else:
                    print('removing cached test runs to prepare for update...')
                    # remove any cached runs for this test plan
                    self.df = self.df[~self.df.testplan.eq(testplan_key)]

        print('retrieving test runs for project {} and test plan {}...'.format(project_id, testplan_key))
        testcycles = self.retrieve_testcycles(project_id=project_id, testplan_key=testplan_key)
        if testcycles is None:
            print(f'invalid testplan {testplan_key}')
            return None
        testruns_to_add = []
        for (testcycle_id, testcycle_name) in testcycles:
            try:
                testruns_raw = self.client.get_testruns(test_cycle_id=testcycle_id)
            except Exception as err:
                print('Jama server connection ERROR! -', err)
                return None

            for y in testruns_raw:
                planned_week = None
                if self.planned_week_field_name is not None and self.planned_week_field_name in y['fields']:
                    week_id = y['fields'][self.planned_week_field_name]
                    if week_id in self.planned_weeks_lookup:
                        planned_week = self.planned_weeks_lookup[week_id]

                bug_id = None
                if self.bug_id_field_name is not None:
                    bug_id = y['fields'].get(self.bug_id_field_name)

                fields = y.get('fields')
                if fields is None:
                    continue

                user = self.__get_user_from_id(fields.get('assignedTo'))
                priority = self.__get_priority_from_id(fields.get(self.priority_field_name))
                network_type = self.__get_network_type_from_id(fields.get(self.network_type_field_name))
                test_network = self.__get_test_network_from_id(fields.get(self.test_network_field_name))
                execution_method = self.__get_execution_method_from_id(fields.get(self.execution_method_field_name))
                
                row = [project_id,
                       testplan_key,
                       testcycle_name,
                       fields.get('testRunSetName'),
                       fields.get('name'),
                       priority,
                       y.get('createdDate'),
                       y.get('modifiedDate'),
                       fields.get('testRunStatus'),
                       fields.get('executionDate'),
                       planned_week,
                       user,
                       bug_id,
                       network_type,
                       test_network,
                       execution_method]
                testruns_to_add.append(row)

        print('found {} test runs!'.format(len(testruns_to_add)))

        # append the retrieved test runs to the existing data frame
        new_df = pd.DataFrame(
            testruns_to_add,
            columns=[
                COL_PROJECT, 
                COL_TESTPLAN, 
                COL_TESTCYCLE, 
                COL_TESTGROUP, 
                COL_TESTRUN, 
                COL_PRIORITY,
                COL_CREATED_DATE, 
                COL_MODIFIED_DATE, 
                COL_STATUS, 
                COL_EXECUTION_DATE,
                COL_PLANNED_WEEK, 
                COL_ASSIGNED_TO, 
                COL_BUG_ID, 
                COL_NETWORK_TYPE, 
                COL_TEST_NETWORK, 
                COL_EXECUTION_METHOD
            ]
        )
        new_df['created_date'] = pd.to_datetime(new_df['created_date'], format="%Y-%m-%d").dt.date
        new_df['modified_date'] = pd.to_datetime(new_df['modified_date'], format="%Y-%m-%d").dt.date
        new_df['execution_date'] = pd.to_datetime(new_df['execution_date'], format="%Y-%m-%d").dt.date
        self.df = self.df.append(new_df, sort=False)

        if testcycle_key is not None:
            # filter by test cycle key
            new_df = new_df[new_df.testcycle.isin([testcycle_key])]
        return new_df

