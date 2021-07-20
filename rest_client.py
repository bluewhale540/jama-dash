import requests
import json

'''Gets a list of active testplans in a project

Parameters:
  url(string): The base url of the Jama instance
  project(int): The project ID

Returns:
  active_plans(list): A list of all active testplans
'''
def get_active_testplans(url, project, username, password):
  result_count = 50
  start = 0
  active_plans = []
  while result_count == 50:
    full_url = url + '/rest/latest/testplans?project={}&maxResults=50&startAt={}'.format(str(project), str(start))
    # CHANGE THIS BEFORE DEPLOYMENT
    myResponse = requests.get(full_url,auth=(username, password))

    # For successful API call, response code will be 200 (OK)
    if myResponse.ok:
      # Loading the response data into a dict variable
      resp_json = json.loads(myResponse.content)
      result_count = resp_json['meta']['pageInfo']['resultCount']
      start = start + 50
      print('found {} testplans:'.format(result_count))

      for key in resp_json['data']:
        name = key['fields']['name']

        # Test plan status field created by Rob (drop down options in vRel only)
        status = key['fields'].get('test_plan_status$35')

        # Archived state of test plan (applies to all projects)
        archived = key['archived']
        if status == 2503:
          active_plans.insert(0, name)
          print('{}: [ACTIVE]'.format(name))
        elif not archived:
          active_plans.append(name)
          print('{}: [NOT ARCHIVED & NOT ACTIVE]'.format(name))
        else:
          print('{}: [ARCHIVED]'.format(name))

    # If response code is not ok (200), print the resulting http error code with description
    else:
      myResponse.raise_for_status()

  return active_plans