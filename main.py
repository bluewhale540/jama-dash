import os
import json
import plotly
import testrun_utils
import login_dialog
from testrun_utils import JamaReportsConfig

def main():

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
    testruns_dict = testrun_utils.retrieve_testruns(jama_url=jama_url,
                                                    jama_username=jama_api_username,
                                                    jama_password=jama_api_password)
    testruns_json = json.dumps(
        testruns_dict,
        # This JSON Encoder will handle things like numpy arrays
        # and datetimes
        cls=plotly.utils.PlotlyJSONEncoder,
    )

    pass

if __name__ == '__main__':
    main()

