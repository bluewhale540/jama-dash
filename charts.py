from datetime import datetime
from testrun_utils import get_testcycle_from_label, \
    get_testgroup_from_label, \
    get_status_names, \
    STATUS_NOT_RUN, \
    STATUS_FAILED, \
    STATUS_INPROGRESS, \
    STATUS_BLOCKED, \
    STATUS_PASSED
from weekly_status import get_weekly_status_bar_chart, get_current_week_testruns_table
from historical_status import get_historical_status_line_chart
from current_status import get_current_status_pie_chart, get_testgroup_status_bar_chart


FIG_TYPE_WEEKLY_STATUS_BAR_CHART = 'Weekly Status'
FIG_TYPE_HISTORICAL_STATUS_LINE_CHART = 'Historical Status'
FIG_TYPE_CURRENT_STATUS_PIE_CHART = 'Current Status'
FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART = 'Current Status By Test Group'
FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART = 'Test Groups with Blocked/Failed Runs'
FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART = 'Test Groups with Not Run/In Progress Runs'
FIG_TYPE_CURRENT_RUNS_TABLE = 'Test Runs For Current Week'

ALL_TEST_CYCLES = 'All Test Cycles'
ALL_TEST_GROUPS = 'All Test Groups'

def get_chart_types():
    chart_types = [
        FIG_TYPE_WEEKLY_STATUS_BAR_CHART,
        FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
        FIG_TYPE_CURRENT_STATUS_PIE_CHART,
        FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART,
        FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART,
        FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART,
        FIG_TYPE_CURRENT_RUNS_TABLE]
    return chart_types


def get_chart(df, testplan_ui, testcycle_ui, testgroup_ui, chart_type, colormap, start_date, test_deadline):
    print('In Get chart: {}'.format(str(datetime.now().strftime('%M %d-%Y %H:%M:%S'))))
    testcycle = get_testcycle_from_label(label=testcycle_ui)
    testgroup = get_testgroup_from_label(label=testgroup_ui)
    if df is None:
        return  None
    title = f'{chart_type} - {testplan_ui}'
    if testcycle is not None:
        title += f':{testcycle_ui}'
    if testgroup is not None:
        title += f':{testgroup_ui}'

    print(f'Creating charts for {title}...')
    chart = None
    if chart_type == FIG_TYPE_WEEKLY_STATUS_BAR_CHART:
        chart = \
            [get_weekly_status_bar_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                title=title,
                colormap=colormap)]

    if chart_type == FIG_TYPE_HISTORICAL_STATUS_LINE_CHART:
        chart = \
            [get_historical_status_line_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                start_date=start_date,
                test_deadline=test_deadline,
                title=title,
                colormap=colormap,
                treat_blocked_as_not_run=True,
                treat_inprogress_as_not_run=True)]

    if chart_type == FIG_TYPE_CURRENT_STATUS_PIE_CHART:
        chart = \
            [get_current_status_pie_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                title=title,
                colormap=colormap)]

    if chart_type == FIG_TYPE_CURRENT_RUNS_TABLE:
        chart = \
            [html.H6(title), get_current_week_testruns_table(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                title=title,
                colormap=colormap)]

    if chart_type == FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART:
        chart = \
            [get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, title=title,
                                           colormap=colormap, status_list=get_status_names())]

    if chart_type == FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART:
        chart = \
            [get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, title=title,
                                           colormap=colormap, status_list=[STATUS_BLOCKED, STATUS_FAILED])]

    if chart_type == FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART:
        chart = \
            [get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, title=title,
                                           colormap=colormap, status_list=[STATUS_NOT_RUN, STATUS_INPROGRESS])]
    return chart

def get_default_colormap():
    return {
        STATUS_NOT_RUN: 'darkslategray',
        STATUS_PASSED: 'green',
        STATUS_FAILED: 'firebrick',
        STATUS_BLOCKED: 'royalblue',
        STATUS_INPROGRESS: 'darkorange'
    }
