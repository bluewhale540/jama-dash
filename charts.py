import logging
from testrun_utils import get_planned_week_from_label, get_testcycle_from_label, \
    get_testgroup_from_label, \
    get_priority_from_label, \
    get_status_names, \
    STATUS_NOT_RUN, \
    STATUS_FAILED, \
    STATUS_INPROGRESS, \
    STATUS_BLOCKED, \
    STATUS_PASSED, \
    METHOD_MANUAL, \
    METHOD_UNASSIGNED, \
    METHOD_MIXED, \
    METHOD_AUTOMATED
from historical_status import get_historical_status_line_chart
from current_status import (get_current_status_pie_chart, get_exec_method_pie_chart, 
    get_testgroup_status_bar_chart, get_person_bar_chart, get_planned_week_bar_chart, 
    get_test_network_bar_chart, get_testruns_table)

logging.basicConfig(format='%(asctime)s - %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


FIG_TYPE_HISTORICAL_STATUS_LINE_CHART = 'Historical Status'
FIG_TYPE_CURRENT_STATUS_PIE_CHART = 'Current Status'
FIG_TYPE_EXEC_METHOD_PIE_CHART = 'Execution Method'
FIG_TYPE_WEEKLY_STATUS_BAR_CHART = 'Weekly Status'
FIG_TYPE_CURRENT_STATUS_BY_PERSON_BAR_CHART = 'Current Status by Person'
FIG_TYPE_CURRENT_STATUS_BY_NETWORK_BAR_CHART = 'Current Satus by Test Network'
FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART = 'Current Status by Test Group'
FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART = 'Test Groups with Blocked/Failed Runs'
FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART = 'Test Groups with Not Run/In Progress Runs'
FIG_TYPE_CURRENT_RUNS_TABLE = 'Test Runs For Current Week'

ALL_TEST_CYCLES = 'All Test Cycles'
ALL_TEST_GROUPS = 'All Test Groups'


'''Get all supported chart types

Returns:
    chart_types (list): A list of all supported charts
'''
def get_chart_types():
    chart_types = [
        FIG_TYPE_HISTORICAL_STATUS_LINE_CHART,
        FIG_TYPE_CURRENT_STATUS_PIE_CHART,
        FIG_TYPE_EXEC_METHOD_PIE_CHART,
        FIG_TYPE_WEEKLY_STATUS_BAR_CHART,
        FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART,
        FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART,
        FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART,
        FIG_TYPE_CURRENT_RUNS_TABLE]
    return chart_types


'''Gets the correct chart given the chart type and other parameters

Parameters:
    df (dataframe): The dataframe
    testplan_ui():
'''
def get_chart(df, testplan_ui, testcycle_ui, testgroup_ui, priority_ui, week_ui, chart_type, colormap, **kwargs):
    testcycle = get_testcycle_from_label(label=testcycle_ui)
    testgroup = get_testgroup_from_label(label=testgroup_ui)
    priority = get_priority_from_label(label=priority_ui)
    week = get_planned_week_from_label(label=week_ui)

    if df is None:
        return  None

    # filter df by testplan
    df = df[df.testplan == testplan_ui]

    # create title for logging
    title = f'{chart_type} - {testplan_ui}'
    if testcycle is not None:
        title += f': {testcycle_ui}'
    if testgroup is not None:
        title += f': {testgroup_ui}'
    if priority is not None:
        title += f': {priority_ui}'
    if week is not None:
        title += f': {week_ui}'

    logging.info(f'Creating chart for {title}...')

    # generate the correct chart
    chart = None
    if chart_type == FIG_TYPE_CURRENT_STATUS_BY_PERSON_BAR_CHART:
        chart = get_person_bar_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                priority=priority,
                week=week,
                colormap=colormap,
                status_list=get_status_names(),
                **kwargs
                )

    if chart_type == FIG_TYPE_WEEKLY_STATUS_BAR_CHART:
        chart = get_planned_week_bar_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                priority=priority,
                colormap=colormap,
                status_list=get_status_names(),
                **kwargs
                )

    if chart_type == FIG_TYPE_HISTORICAL_STATUS_LINE_CHART:
        chart = \
            get_historical_status_line_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                priority=priority,
                title=title,
                colormap=colormap,
                **kwargs
                )

    if chart_type == FIG_TYPE_CURRENT_STATUS_PIE_CHART:
        chart = get_current_status_pie_chart(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                priority=priority,
                week=week,
                colormap=colormap
                )

    if chart_type == FIG_TYPE_EXEC_METHOD_PIE_CHART:
        chart = get_exec_method_pie_chart(
            df=df,
            testcycle=testcycle,
            testgroup=testgroup,
            priority=priority,
            week=week,
            colormap=colormap
        )

    if chart_type == FIG_TYPE_CURRENT_RUNS_TABLE:
        chart = \
            get_testruns_table(
                df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                priority=priority,
                week=week,
                colormap=colormap,
                **kwargs
            )

    if chart_type == FIG_TYPE_CURRENT_STATUS_BY_NETWORK_BAR_CHART:
        chart = get_test_network_bar_chart(
            df=df,
                testcycle=testcycle,
                testgroup=testgroup,
                priority=priority,
                week=week,
                colormap=colormap,
                **kwargs
        )

    if chart_type == FIG_TYPE_CURRENT_STATUS_BY_TESTGROUP_BAR_CHART:
        chart = get_testgroup_status_bar_chart(
            df=df,
            testcycle=testcycle,
            testgroup=testgroup,
            colormap=colormap,
            priority=priority,
            week=week,
            status_list=get_status_names(),
            **kwargs
            )

    if chart_type == FIG_TYPE_BLOCKED_FAILED_TESTGROUP_BAR_CHART:
        chart = get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, priority=priority,
                                           colormap=colormap, status_list=[STATUS_BLOCKED, STATUS_FAILED])

    if chart_type == FIG_TYPE_NOTRUN_INPROGRESS_TESTGROUP_BAR_CHART:
        chart = get_testgroup_status_bar_chart(df=df, testcycle=testcycle, testgroup=testgroup, priority=priority,
                                           colormap=colormap, status_list=[STATUS_NOT_RUN, STATUS_INPROGRESS])
    return chart


'''The colors to use for the different states

Returns:
    A dict of states to colors
'''
def get_default_colormap():
    return {
        STATUS_NOT_RUN: 'darkslategray',
        STATUS_PASSED: 'green',
        STATUS_FAILED: 'firebrick',
        STATUS_BLOCKED: 'royalblue',
        STATUS_INPROGRESS: 'darkorange',
        METHOD_UNASSIGNED: '#553D67',
        METHOD_MANUAL: '#2F2FA2',
        METHOD_MIXED: '#FF6B45',
        METHOD_AUTOMATED: '#FF2E7E'
    }
