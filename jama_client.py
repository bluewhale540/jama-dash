from py_jama_rest_client.client import JamaClient
from testrun_utils import get_start_and_end_date
import pandas as pd
from datetime import timedelta, date, datetime
from tzlocal import get_localzone
import requests
from requests.exceptions import HTTPError

class jama_client:
    url = None
    username = None
    password = None
    testcycle_db = {}  # DB of test cycles for the projects and test plans we want to track
    planned_weeks_lookup = {}  # dict of planned week id to name
    planned_weeks = [] # sorted list of start dates of planned weeks
    project_id_lookup = {} # dict of project keys to id
    user_id_lookup = {} # dict of user ids to names

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
        return user

    # download the list of project ids given a list of project keys (names)
    def __get_projects_info(self, projkey_list):
        # get a list of all projects - not efficient but py_jama_rest_client does not support
        # searching using a project key
        # TODO: use REST API directly
        print('getting a list of all projects...')
        all_projects = self.client.get_projects()

        for x in all_projects:
            p = x.get('projectKey')
            if p is None or x['isFolder'] is True:
                continue

            projkey_list = [a for a in projkey_list if a not in iter(self.project_id_lookup)]
            for project_key in projkey_list:
                if p == project_key:
                    self.project_id_lookup[project_key] = x['id']
                    print('found project {}!'.format(project_key))
        if len(projkey_list) != 0:
            print('following projects not found -')
            for proj in projkey_list:
                print(f'\t{proj}')

    def connect(self, url, username, password, projkey_list):
        # Create the Jama client
        try:
            self.client = JamaClient(host_domain=url, credentials=(username, password))
            # create project id lookup table
            self.__get_projects_info(projkey_list)
            # get item types for test plans and cycles
            self.item_types = self.client.get_item_types()
            self.testplan_type = next(x for x in self.item_types if x['typeKey'] == 'TSTPL')['id']
            self.testcycle_type = next(x for x in self.item_types if x['typeKey'] == 'TSTCY')['id']

            self.testrun_obj = next(x for x in self.item_types if x['typeKey'] == 'TSTRN')
            # find the name for the 'Bug ID' field in a test run
            self.bug_id_field_name = None

            # find the name for the 'Planned week' field in a test run
            pick_lists = self.client.get_pick_lists()
            planned_week_id = next(x for x in pick_lists if x['name'] == 'Planned week')['id']
            self.planned_week_field_name = None
            for x in self.testrun_obj['fields']:
                if 'label' in x and x['label'] == 'Bug ID':
                    self.bug_id_field_name = x['name']
                    continue
                if 'pickList' in x and x['pickList'] == planned_week_id:
                    self.planned_week_field_name = x['name']
                    continue

            weeks = self.client.get_pick_list_options(planned_week_id)
            for x in weeks:
                start_date, end_date = get_start_and_end_date(x['name'])
                if start_date is None:
                    # will we ever get here?
                    continue
                self.planned_weeks_lookup[x['id']] = start_date
                self.planned_weeks.append(start_date)
            self.planned_weeks = sorted(self.planned_weeks)
            # Add None to the list for tests with aunassigned weeks
            self.planned_weeks = [None] + self.planned_weeks

        except Exception as err:
            print('Jama server connection ERROR! -', err)
            return False
        self.username = username
        self.password = password
        self.url = url
        return True


    def get_status_names(self):
        return self.status_list

    def get_planned_weeks(self):
        return self.planned_weeks

    # retuns an array of counts of the values in the status field in the df
    # if override_total_runs is not None, calculate not_run using this value
    def __get_status_counts(self, df, override_total_runs=None):
        df_counts = df['status'].value_counts()
        passed = 0
        failed = 0
        inprogress = 0
        blocked = 0
        not_run = 0
        if 'PASSED' in df_counts.index:
            passed = df_counts['PASSED']
        if 'FAILED' in df_counts.index:
            failed = df_counts['FAILED']
        if 'INPROGRESS' in df_counts.index:
            inprogress = df_counts['INPROGRESS']
        if 'BLOCKED' in df_counts.index:
            blocked = df_counts['BLOCKED']
        if 'NOT_RUN' in df_counts.index:
            not_run = df_counts['NOT_RUN']
        if override_total_runs is not None:
            not_run = override_total_runs - passed - failed - blocked - inprogress

        datadict = {}
        datadict['NOT_RUN'] = not_run
        datadict['PASSED'] = passed
        datadict['FAILED'] = failed
        if self.inprogress_as_not_run:
            datadict['NOT_RUN'] += inprogress
        else:
            datadict['INPROGRESS'] = inprogress
        if self.blocking_as_not_run:
            datadict['NOT_RUN'] += blocked
        else:
            datadict['BLOCKED'] = blocked
        return datadict

    def __get_status_counts_as_list(self, df, override_total_runs=None):
        d = self.__get_status_counts(df, override_total_runs)
        data_row = [d['NOT_RUN'], d['PASSED'], d['FAILED'], ]
        if not self.inprogress_as_not_run:
            data_row.append(d['INPROGRESS'])
        if not self.blocking_as_not_run:
            data_row.append(d['BLOCKED'])
        return data_row

    def retrieve_testcycles(self, project_key, testplan_key, update=False):
        testcycles = self.testcycle_db.get((project_key, testplan_key))
        if not update and self.testcycle_db is not None and testcycles is not None:
            # already in DB
            print('Test cycles for project {} and test plan {} already in DB. Will not re-query'
                  .format(project_key, testplan_key))
            return testcycles

        project_id = self.project_id_lookup[project_key]
        if project_id is None:
            print(f'Invalid project {project_key}')
        print(f'querying for test plan {testplan_key}...')
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
        print('querying for test cycles under test plan {}...'.format(testplan_key))
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
        self.testcycle_db[(project_key, testplan_key)] = testcycles
        return testcycles

    def retrieve_testruns(self, project_key, testplan_key, testcycle_key=None, update=False):
        # check for cached test run data
        if not self.df.empty:
            print('checking cached test runs for project {} and test plan {}{}...'
                  .format(project_key, testplan_key,
                          '' if testcycle_key is None else ' and test cycle {}'.format(testcycle_key)))
            query_df = self.df[self.df.project.isin([project_key]) & self.df.testplan.isin([testplan_key])]
            if not query_df.empty and testcycle_key is not None:
                # filter by test cycle key
                query_df = query_df[query_df.testcycle.isin([testcycle_key])]
            if query_df.empty:
                print('no cached test runs found!')
            else:
                print('{} cached test runs found!'.format(query_df.shape[0]))
                if update == False:
                    # return cached test runs
                    return query_df
                else:
                    print('removing cached test runs to prepare for update...')
                    # remove any cached runs for this test plan
                    self.df = self.df[self.df.project != project_key or self.df.testplan != testplan_key]

        print('retrieving test runs for project {} and test plan {}...'.format(project_key, testplan_key))
        testcycles = self.testcycle_db.get((project_key, testplan_key))
        if testcycles is None:
            print('No test cycles found for test plan. please call retrieve_testcycles() first')
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
                row = [project_key,
                       testplan_key,
                       testcycle_name,
                       fields.get('testRunSetName'),
                       fields.get('name'),
                       y.get('createdDate'),
                       y.get('modifiedDate'),
                       fields.get('testRunStatus'),
                       fields.get('executionDate'),
                       planned_week,
                       user,
                       bug_id]
                testruns_to_add.append(row)

        print('found {} test runs!'.format(len(testruns_to_add)))

        # append the retrieved test runs to the existing data frame
        new_df = pd.DataFrame(testruns_to_add, columns=['project', 'testplan', 'testcycle', 'testcase', 'testrun',
                                                        'created_date', 'modified_date', 'status', 'execution_date',
                                                        'planned_week', 'assigned_to', 'bug_id'])
        new_df['created_date'] = pd.to_datetime(new_df['created_date'], format="%Y-%m-%d").dt.floor("d")
        new_df['modified_date'] = pd.to_datetime(new_df['modified_date'], format="%Y-%m-%d").dt.floor("d")
        new_df['execution_date'] = pd.to_datetime(new_df['execution_date'], format="%Y-%m-%d").dt.floor("d")

        self.df = self.df.append(new_df, sort=False)

        if testcycle_key is not None:
            # filter by test cycle key
            new_df = new_df[new_df.testcycle.isin([testcycle_key])]
        return new_df

    # get testrun status by testrun set
    def get_testrun_status_by_testcase(self, project_key, testplan_key, testcycle_key=None):
        df = self.retrieve_testruns(project_key=project_key,
                                            testplan_key=testplan_key,
                                            testcycle_key=testcycle_key)

        # get list of testrun sets
        sets = [x for x in iter(df.testcase.unique())]
        d = []
        for set in iter(sets):
            df1 = df[df.testcase == set]
            total_runs = df1.shape[0]
            status_counts = self.__get_status_counts_as_list(df1)
            d.append(status_counts)
        df_result = pd.DataFrame(d, columns=self.get_status_names(), index=sets)
        df_result = df_result.query('FAILED > 0 or BLOCKED > 0')
        return df_result


    def get_testrun_status_historical(self, project_key, testplan_key, testcycle_key=None, start_date=None):
        testrun_df = self.retrieve_testruns(project_key=project_key,
                                            testplan_key=testplan_key,
                                            testcycle_key=testcycle_key)
        # set lowest modified date - 1 as start date
        if start_date is None:
            start_date = pd.to_datetime(testrun_df['modified_date'].values.min()).date() - timedelta(days=1)
        # set tomorrow's date as end date
        end_date = date.today() + timedelta(days=1) - timedelta(seconds=1)  # today 11:59:59 pm
        # get local time zone
        local_tz = get_localzone()
        # create a date range using start and end dates from above set to the local TZ
        daterange = pd.date_range(start_date, end_date, tz=local_tz)
        t = []
        for d in daterange:
            # create a dataframe of all test runs created before date 'd'
            df1 = testrun_df[testrun_df['created_date'] < d]
            if df1.empty:
                # no test runs found - we will not consider this date
                continue
            total_runs = df1.shape[0]
            df2 = df1[df1.modified_date < d]
            if df2.empty:
                continue
            #df2 = df2[df1.execution_date is not None and df1.execution_date < d]
            #if df2.empty:
            #    continue
            data_row = [d] + self.__get_status_counts_as_list(df2, override_total_runs=total_runs)
            t.append(data_row)

        df = pd.DataFrame(t, columns=['date'] + self.status_list)
        df['date'] = pd.to_datetime(df['date'])
        return df

