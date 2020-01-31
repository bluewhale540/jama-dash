import os
from py_jama_rest_client.client import JamaClient


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
jama_api_username = os.environ['JAMA_API_USERNAME']
jama_api_password = os.environ['JAMA_API_PASSWORD']

# Create the JamaClient
jama_client = JamaClient(host_domain=jama_url, credentials=(jama_api_username, jama_api_password))


# get item types
item_types = jama_client.get_item_types()

'''
# Get the list of projects from Jama
# The client will return to us a JSON array of Projects, where each project is a JSON object.
project_list = jama_client.get_projects()

#

# Print the data out for each project.

for project in project_list:
    project_name = project['fields']['name']
    if project_name == 'PIT':
        print('\n---------------' + project_name + '---------------')
        print_fields(project)
        print('\n')
'''

# get all test plans in project
testplans = jama_client.get_abstract_items(item_type=35, project=269 , contains='GX5_Phase1_Stage1_FAT2_Dry_Run') #project=269

# there should only be one test plan with this name
testplan_id = testplans[0]['id']

# get all test cycles in project
testcycles = jama_client.get_abstract_items(item_type=36, project=269 ) #contains='GX5_P1S1F2-DR_IQ800_Datapath'

# remove test cycles that do not belong to our test plan
testcycles = [x for x in testcycles if x['fields']['testPlan'] == testplan_id]

# get all test run in project
alltestruns = jama_client.get_abstract_items(item_type=37, project=269)

for x in testcycles:
    testcycle_id = x['id']
    testcycle_name = x['fields']['name']
    print(testcycle_name + ':')
    testruns = [x for x in alltestruns if x['fields']['testCycle'] == testcycle_id]
    for y in testruns:
        testrun_name = y['fields']['name']
        testrun_status = y['fields']['testRunStatus']
        print('\t' + testrun_name + ':' + testrun_status)

    continue

# remove test runs that do not belong to our test cycle
#testcycles = [x for x in testcycles if x['fields']['testPlan'] == testplan_id]

pass