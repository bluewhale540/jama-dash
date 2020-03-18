import datetime
import tzlocal
import os
import redis
import testrun_utils
import redis_data
import logging

from celery import Celery

celery_app = Celery('iDirect Contour Reports App', broker=os.environ['REDIS_URL'])
redis_instance = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
logger = logging.getLogger('Celery Backend')
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format,
        datefmt='%Y-%m-%d %I:%M:%S %p %z',
        level=logging.DEBUG)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print('----> setup_periodic_tasks')
    sender.add_periodic_task(
        140,  # seconds
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

    df = testrun_utils.retrieve_testruns(jama_url=jama_url,
                                                   jama_username=jama_api_username,
                                                   jama_password=jama_api_password)
    if df is None:
        logger.error('cannot retrieve data from Jama/Contour server. Check config file!')
        return

    # compare data with existing data in redis
    redis_df = redis_data.get_dataframe(redis_instance)

    modified = True
    if redis_df is not None and redis_df.equals(df):
        logger.debug('Data unchanged, will not update in Redis data store')
        modified = False

    # set updated time
    redis_data.set_updated_datetime(redis_instance)

    if modified is True:
        logger.debug('Data changed. will update in Redis data store')
        redis_data.set_dataframe(redis_instance, df)
        redis_data.set_modified_datetime(redis_instance)
