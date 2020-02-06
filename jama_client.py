import os
from py_jama_rest_client.client import JamaClient
import pandas as pd
from datetime import timedelta, date
from tzlocal import get_localzone


class jama_client:
    testcycle_db = {} # DB of test cycles for the projects and test plans we want to track

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

    def connect(self, url, username, password):
        # Create the Jama client
        try:
            self.client = JamaClient(host_domain=url, credentials=(username, password))
            # get item types for test plans and cycles
            self.item_types = self.client.get_item_types()
            self.testplan_type = next(x for x in self.item_types if x['typeKey'] == 'TSTPL')['id']
            self.testcycle_type = next(x for x in self.item_types if x['typeKey'] == 'TSTCY')['id']
        except Exception as err:
            print('Jama server connection ERROR! -', err)
            return False
        return True

    def get_status_names(self):
        return  self.status_list

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
        try:
            projects = self.client.get_projects()
        except Exception as err:
            print('Jama server connection ERROR! -', err)
            return None
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
                  .format(project_key, testplan_key, '' if testcycle_key is None else ' and test cycle {}'.format(testcycle_key)))
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

        print('attempting to retrieve test runs for project {} and test plan {} from Jama...'.format(project_key, testplan_key))
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
                testruns_to_add.append([project_key,
                                     testplan_key,
                                     testcycle_name,
                                     y['fields']['name'],
                                     y['createdDate'],
                                     y['modifiedDate'],
                                     y['fields']['testRunStatus']])

        print('found {} test runs!'.format(len(testruns_to_add)))

        # append the retrieved test runs to the existing data frame
        new_df = pd.DataFrame(testruns_to_add, columns=['project', 'testplan', 'testcycle', 'testrun',
                                            'created_date', 'modified_date', 'status'])
        new_df['created_date'] = pd.to_datetime(new_df['created_date'])
        new_df['modified_date'] = pd.to_datetime(new_df['modified_date'])
        self.df = self.df.append(new_df)
        if testcycle_key is not None:
            # filter by test cycle key
            new_df = new_df[new_df.testcycle.isin([testcycle_key])]
        return new_df

    def get_testrun_status_current(self, project_key, testplan_key, testcycle_key=None):
        testrun_df = self.retrieve_testruns(project_key=project_key,
                                            testplan_key=testplan_key,
                                            testcycle_key=testcycle_key)
        # get the counts of each status
        df = testrun_df['status'].value_counts()
        if self.inprogress_as_not_run:
            # consolidate INPROGRESS into NOT_RUN
            df['NOT_RUN'] = df['NOT_RUN'] + df['INPROGRESS']
            df = df.drop(columns=['INPROGRESS',])
        if self.blocking_as_not_run:
            #consolidate BLOCKED into NOT_RUN
            df['NOT_RUN'] = df['NOT_RUN'] + df['BLOCKED']
            df = df.drop(columns=['BLOCKED',])
        return df

    def get_testrun_status_historical(self, project_key, testplan_key, testcycle_key=None):
        testrun_df = self.retrieve_testruns(project_key=project_key,
                                            testplan_key=testplan_key,
                                            testcycle_key=testcycle_key)
        # set lowest modified date - 1 as start date
        start_date = pd.to_datetime(testrun_df['modified_date'].values.min()).date() - timedelta(days=1)
        # set tomorrow's date as end date
        end_date = date.today() + timedelta(days=1)

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
            total = df1.shape[0]  # no of rows gives total number of test runs on that date
            df2 = df1[df1['modified_date'] < d]
            counts = df2['status'].value_counts()
            passed = 0
            failed = 0
            inprogress = 0
            blocked = 0
            if 'PASSED' in counts.index:
                passed = counts['PASSED']
            if 'FAILED' in counts.index:
                failed = counts['FAILED']
            if 'INPROGRESS' in counts.index:
                inprogress = counts['INPROGRESS']
            if 'BLOCKED' in counts.index:
                blocked = counts['BLOCKED']
            not_run = total - passed - failed
            if self.inprogress_as_not_run:
                not_run -= inprogress
            if self.blocking_as_not_run:
                not_run -= blocked
            data_row = [d, not_run, passed, failed,]
            if not self.inprogress_as_not_run:
                data_row.append(inprogress)
            if not self.blocking_as_not_run:
                data_row.append(blocked)
            t.append(data_row)
            continue
        df = pd.DataFrame(t, columns=['date'] + self.status_list)
        df['date'] = pd.to_datetime(df['date'])
        return df

