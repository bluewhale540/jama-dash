import re
from datetime import timedelta, date, datetime
import pandas as pd
from tzlocal import get_localzone

def get_status_names():
    return ['NOT_RUN', 'PASSED', 'FAILED', 'INPROGRESS', 'BLOCKED']

def filter_df(df, testcycle_key=None, testcase_key=None):
    df1 = df
    if testcycle_key is not None:
        df1 = df1[df.testcycle.eq(testcycle_key)]
    if testcase_key is not None:
        df1 = df1[df.testcase.eq(testcase_key)]
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


# process the week string in the format SprintX_mmmdd_mmmdd or SprintX_mmmdd_dd
# and return the start and end dates in the string. Returns None, None if format is
# invalid
def get_start_and_end_date(week_str):
    # strip 'Sprint\d_' prefix if it exists
    result = re.findall('^Sprint\d+_', week_str)
    if len(result) == 0:
        return None, None
    dates = week_str[len(result[0]):]
    result = re.findall('^\D+', dates)
    month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5,
                 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10,
                 'Nov': 11, 'Dec': 12}
    if len(result) == 0 or result[0] not in iter(month_map):
        return None, None
    start_month = month_map[result[0]]
    end_month = start_month
    days = re.split('-', dates[len(result[0]):])
    if len(days) < 2:
        return None, None
    start_day = int(days[0])
    # check for second month
    result = re.findall('^\D+', days[1])
    if len(result) != 0:
        if result[0] not in iter(month_map):
            return None, None
        else:
            end_month = month_map[result[0]]
            days[1] = days[1][len(result[0]):]
    end_day = int(days[1])

    current_year = date.today().year
    current_month = date.today().month
    start_year = current_year
    end_year = current_year
    # empirically check if we are straddling years
    # (assume month > current month + 6) as the threshold
    if start_month > current_month + 6:
        start_year -= 1
    if end_month > current_month + 6:
        end_year -= 1

    start_date = date(year=start_year, month=start_month, day=start_day)
    end_date = date(year=end_year, month=end_month, day=end_day)
    return start_date, end_date

def __get_current_planned_week(planned_weeks):
    for start_date in planned_weeks:
        if start_date is None:
             continue
        if date.today() >= start_date and date.today() < start_date + timedelta(days=7):
            return start_date
    return None


def get_testrun_status_by_planned_weeks(df, testcycle_key=None, testcase_key=None):
    df1 = filter_df(df, testcycle_key, testcase_key)
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

def get_testruns_for_current_week(df, testcycle_key=None, testcase_key=None):
    df1 = filter_df(df, testcycle_key, testcase_key)
    planned_weeks = df1.planned_week.unique()
    start_date = __get_current_planned_week(planned_weeks)
    if start_date is None:
        # Cannot find current planned week in dataframe, return None
        return None
    # filter test runs by current week
    df1 = df1[df1['planned_week'] == start_date]
    df1 = df1.drop(columns=['project', 'testplan', 'created_date', 'modified_date', 'planned_week'])
    return df1


def get_testrun_status_historical(df, testcycle_key=None, testcase_key=None, start_date=None):
    df1 = filter_df(df, testcycle_key, testcase_key)
    # set lowest modified date - 1 as start date
    if start_date is None:
        start_date = df1['modified_date'].values.min()
    # set tomorrow's date as end date
    end_date = datetime.now().date()  # today 11:59:59 pm
    # get local time zone
    local_tz = get_localzone()
    # create a date range using start and end dates from above set to the local TZ
    daterange = pd.date_range(start_date, end_date)
    t = []
    for d in daterange:
        # create a dataframe of all test runs created before date 'd'
        df2 = df1[df1['created_date'] < d]
        if df2.empty:
            # no test runs found - we will not consider this date
            continue
        total_runs = df2.shape[0]
        df2 = df2[df2.modified_date < d]
        if df2.empty:
            continue
        status_list, data_row = __get_status_counts_as_list(df2, override_total_runs=total_runs)
        data_row = [d] + data_row
        t.append(data_row)

    df3 = pd.DataFrame(t, columns=['date'] + get_status_names())
    df3['date'] = pd.to_datetime(df3['date'])
    return df3

