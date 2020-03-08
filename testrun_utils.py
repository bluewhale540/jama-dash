from datetime import timedelta, date, datetime
from dateutil import parser
import pandas as pd
import json
from tzlocal import get_localzone
from os.path import expanduser, isfile
from jama_client import jama_client

ALL_TEST_CYCLES = 'All Test Cycles'
ALL_TEST_GROUPS = 'All Test Groups'

class JamaReportsConfig:
    config = None
    colormap = None
    start_date = None
    test_deadline = None
    testplan_lookup = {}
    config_file_path = '<Invalid>'
    config_file_name = 'jama-report-config.json'

    def __init__(self):
        pass

    def __repr__(self):
        return f'{self.__class__.__name__})'

    def read_config_file(self):
        for settings_dir in [expanduser('~'), '.']:
            path = settings_dir + '/' + self.config_file_name
            if isfile(path):
                self.config_file_path = path
                print(f'settings file {path} found!')
                break

        if self.config_file_path is None:
            print(f'settings file {self.config_file_name} not found!')
            return False

        try:
            with open(self.config_file_path) as f:
                self.config = json.load(f)
        except json.decoder.JSONDecodeError as e:
            print(f'Settings file {self.config_file_path} has invalid format')
            print(f'{e}')
            return False
        except Exception as e:
            print(f'Error opening settings file {self.config_file_path}')
            print(f'{e}')
            return False

        testplans = self.config.get('testplans')
        if testplans is None:
            print('Invalid config. No testplans found!')
            return False
        for t in testplans:
            title = t.get('displayName')
            project = t.get('project')
            testplan = t.get('name')
            if project is None or testplan is None:
                print('missing project or testplan in config. Skipping...')
                continue
            if title is None:
                title = project + ':' + testplan
            # add to lookup
            self.testplan_lookup[title] = (project, testplan)

        chart_settings = self.config.get('chartSettings')
        if chart_settings is not None:
            self.colormap = chart_settings.get('colormap')
        dt = chart_settings.get('testStart')
        self.start_date = parser.parse(dt) if dt is not None else None
        dt = chart_settings.get('testDeadline')
        self.test_deadline = parser.parse(dt) if dt is not None else None
        return True

    def get_projects(self):
        if self.testplan_lookup is None:
            return None
        return [x[0] for x in self.testplan_lookup.values()]

    # return UI friendly testplan names
    def get_testplan_names(self):
        return [x for x in iter(self.testplan_lookup)]

    def get_project_and_testplan(self, testplan_ui_key):
        return self.testplan_lookup.get(testplan_ui_key)

    def get_colormap(self):
        return self.colormap

    def get_start_date(self):
        return self.start_date

    def get_test_deadline(self):
        return self.test_deadline



def get_status_names():
    return ['NOT_RUN', 'PASSED', 'FAILED', 'INPROGRESS', 'BLOCKED']

def filter_df(df, testcycle_key=None, testgroup_key=None):
    df1 = df
    if testcycle_key is not None:
        df1 = df1[df.testcycle.eq(testcycle_key)]
    if testgroup_key is not None:
        df1 = df1[df.testgroup.eq(testgroup_key)]
    return df1


# retuns an array of counts of the values in the status field in the df
# if override_total_runs is not None, calculate not_run using this value
def __get_status_counts(df, override_total_runs=None, inprogress_as_not_run=False, blocking_as_not_run=False):
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
    if inprogress_as_not_run:
        datadict['NOT_RUN'] += inprogress
    else:
        datadict['INPROGRESS'] = inprogress
    if blocking_as_not_run:
        datadict['NOT_RUN'] += blocked
    else:
        datadict['BLOCKED'] = blocked
    return datadict


def __get_status_counts_as_list(df, override_total_runs=None,
                                inprogress_as_not_run=False, blocking_as_not_run=False):
    d = __get_status_counts(df, override_total_runs, inprogress_as_not_run, blocking_as_not_run)
    status_list = ['NOT_RUN', 'PASSED', 'FAILED']
    if not inprogress_as_not_run:
        status_list.append('INPROGRESS')
    if not blocking_as_not_run:
        status_list.append('BLOCKED')
    data_row = [d[x] for x in status_list]
    return status_list, data_row


def __get_current_planned_week(planned_weeks):
    for start_date in planned_weeks:
        if start_date is None:
             continue
        if date.today() >= start_date and date.today() < start_date + timedelta(days=7):
            return start_date
    return None


def get_testrun_status_by_planned_weeks(df, testcycle_key=None, testgroup_key=None):
    df1 = filter_df(df, testcycle_key, testgroup_key)
    t = []
    status_list=[]
    planned_weeks = df1.planned_week.unique()
    for week in planned_weeks:
        df2 = pd.DataFrame()
        if week is None:
            df2 = df1[df1.planned_week.isnull()]
        else:
            df2 = df1[df1['planned_week'] == week]
        # get the counts of each status
        status_list, data_row = __get_status_counts_as_list(df=df2)
        if not any(data_row):
            # all zero values -- skip row
            continue
        # replace 0 values with None
        data_row = [i if i > 0 else None for i in data_row]

        t.append([week] + data_row)

    df = pd.DataFrame(t, columns=['planned_week'] + status_list)
    return df

def get_testruns_for_current_week(df, testcycle_key=None, testgroup_key=None):
    df1 = filter_df(df, testcycle_key, testgroup_key)
    planned_weeks = df1.planned_week.unique()
    start_date = __get_current_planned_week(planned_weeks)
    if start_date is None:
        # Cannot find current planned week in dataframe, return None
        return None
    # filter test runs by current week
    df1 = df1[df1['planned_week'] == start_date]
    df1 = df1.drop(columns=['project', 'testplan', 'created_date', 'modified_date', 'planned_week'])
    return df1


def get_testrun_status_historical(df, testcycle_key=None, testgroup_key=None, start_date=None):
    df1 = filter_df(df, testcycle_key, testgroup_key)
    # set lowest modified date - 1 as start date
    if start_date is None:
        start_date = df1['modified_date'].values.min()
    # set tomorrow's date as end date
    end_date = datetime.now().date() # today 11:59:59 pm
    # get local time zone
    local_tz = get_localzone()
    # create a date range using start and end dates from above set to the local TZ
    daterange = pd.date_range(start_date, end_date)
    t = []
    for d in daterange:
        # create a dataframe of all test runs created before date 'd'
        df2 = df1[df1['created_date'] <= d]
        if df2.empty:
            # no test runs found - we will not consider this date
            continue
        total_runs = df2.shape[0]
        df2 = df2[df2.modified_date <= d]
        if df2.empty:
            continue
        status_list, data_row = __get_status_counts_as_list(df2, override_total_runs=total_runs)
        data_row = [d] + data_row
        t.append(data_row)

    df3 = pd.DataFrame(t, columns=['date'] + get_status_names())
    df3['date'] = pd.to_datetime(df3['date'])
    return df3

# connect to JAMA server, download testruns for all testplans in config and return testruns as a JSON
def retrieve_testruns(jama_url: str, jama_username: str, jama_password: str):
    config = JamaReportsConfig()
    if not config.read_config_file():
        print('Error reading config file!')
        return None
    client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
    projects = config.get_projects()
    if len(projects) == 0:
        print('No projects found in config file')
        return None
    if not client.connect(url=jama_url, username=jama_username, password=jama_password, projkey_list=config.get_projects()):
        print('Error getting data from Jama/Contour')
        return None
    # download test runs
    testruns = {}
    testruns['testplan'] = []
    for testplan_name in config.get_testplan_names():
        project, testplan = config.get_project_and_testplan(testplan_ui_key=testplan_name)
        df = client.retrieve_testruns(project_key=project, testplan_key=testplan)
        d = {}
        d['name'] = testplan_name
        d['data'] = df.to_dict()
        testruns['testplan'].append(d)
    return testruns


