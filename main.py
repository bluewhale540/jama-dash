import os
from jama_client import jama_client
import login_dialog

def main():
    # list of project, test plan and chart title
    testing_list = [
        ('VRel', '2.7.1-3.1-FAT2 Testing (Priority1)', 'SIT FAT2 Testing Status'),
        #    ('PIT', 'GX5_Phase1_Stage1_FAT2_Dry_Run', 'PIT FAT2 Dry Run Status'),
    ]
    projlist = [x[0] for x in testing_list]


    jama_url = os.environ.get('JAMA_API_URL')
    jama_api_username = os.environ.get('JAMA_API_USERNAME')
    jama_api_password = os.environ.get('JAMA_API_PASSWORD')

    if jama_url is None:
        jama_url = 'https://paperclip.idirect.net'

    if jama_api_password is None or jama_api_username is None:
        # get Jama/contour login credentials using a dialog box
        while True:
            result = login_dialog.run()
            if result is None:
                exit(1)
            break
        jama_api_username = result[0]
        jama_api_password = result[1]

    client = jama_client(blocking_as_not_run=False, inprogress_as_not_run=False)
    if not client.connect(url=jama_url, username=jama_api_username, password=jama_api_password, projkey_list=projlist):
        exit(1)
    for project, testplan, title in testing_list:
        testcycle_db = client.retrieve_testcycles(project_key=project, testplan_key=testplan)
        if testcycle_db is None:
            exit(1)

        testcycles = [None,]
        for id, cycle in testcycle_db:
            testcycles.append(cycle)

if __name__ == '__main__':
    main()

