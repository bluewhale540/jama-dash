import datetime
import json
import os
import plotly
import redis
import testrun_utils


from celery import Celery

celery_app = Celery('iDirect Contour Reports App', broker=os.environ['REDIS_URL'])
redis_instance = redis.StrictRedis.from_url(os.environ['REDIS_URL'])


REDIS_HASH_NAME = 'IDIRECT_CONTOUR_TESTRUN_HASH'
REDIS_DATASET_KEY = 'TESTRUN_DATASET'
REDIS_UPDATED_KEY = 'TESTRUN_UPDATED_TIME'


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print('----> setup_periodic_tasks')
    sender.add_periodic_task(
        300,  # seconds
        # an alternative to the @app.task decorator:
        # wrap the function in the app.task function
        update_data.s(),
        name='Update data',
    )


@celery_app.task
def update_data():
    jama_url = os.environ.get('JAMA_API_URL')
    jama_api_username = os.environ.get('JAMA_API_USERNAME')
    jama_api_password = os.environ.get('JAMA_API_PASSWORD')

    if jama_url is None:
        jama_url = 'https://paperclip.idirect.net'

    testrun_dict = testrun_utils.retrieve_testruns(jama_url=jama_url,
                                                   jama_username=jama_api_username,
                                                   jama_password=jama_api_password)
    # Save testrun dataframes in redis so that the Dash app, running on a separate
    # process, can read it
    redis_instance.hset(
        REDIS_HASH_NAME,
        REDIS_DATASET_KEY,
        json.dumps(
            testrun_dict,
            # This JSON Encoder will handle things like numpy arrays
            # and datetimes
            cls=plotly.utils.PlotlyJSONEncoder,
        ),
    )
    # Save the timestamp that the dataframe was updated
    redis_instance.hset(
        REDIS_HASH_NAME, REDIS_UPDATED_KEY, str(datetime.datetime.now())
    )