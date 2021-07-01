import os
import redis
import datetime
import tzlocal
import redis_params
import testrun_utils


def get_redis_inst():
    redis_url = os.getenv('REDIS_URL')
    if redis_url is None:
        return None
    redis_inst = redis.StrictRedis.from_url(redis_url)
    return redis_inst


def set_dataframe(redis_inst, df):
    ''' Update data to redis if data has changed
    '''
    json_str = testrun_utils.df_to_json(df)

    # Save testrun dataframes in redis so that the Dash app, running on a separate
    # process, can read it
    resp = redis_inst.hset(
        redis_params.REDIS_HASH_NAME,
        redis_params.REDIS_DATASET_KEY,
        json_str
    )
    return resp


def get_dataframe_json(redis_inst):
    '''
    Get dataframe from redis in json format
    '''
    data = redis_inst.hget(
        redis_params.REDIS_HASH_NAME, redis_params.REDIS_DATASET_KEY
    )
    if data is None:
        return None
    jsonified_df = data.decode('utf-8')
    return jsonified_df

def get_dataframe(redis_inst):
    '''
    get dataframe from redis in pandas dataframe format
    '''
    jsonified_df = get_dataframe_json(redis_inst)
    return testrun_utils.json_to_df(jsonified_df) if jsonified_df is not None else None



def set_updated_datetime(redis_inst):
    '''
    set the date and time the data was last checked against existing data in redis
     (which may or may not be the same as the date and time the data was last changed)
    '''
    redis_inst.hset(
        redis_params.REDIS_HASH_NAME,
        redis_params.REDIS_UPDATED_KEY,
        str(datetime.datetime.now(
            tzlocal.get_localzone()).strftime(redis_params.REDIS_TIME_FORMAT))
    )


def get_updated_datetime(redis_inst):
    '''
    retrieve the date and time the data was last checked against existing data in redis
     (which may or may not be the same as the date and time the data was last changed)
    '''
    data_last_updated = redis_inst.hget(
        redis_params.REDIS_HASH_NAME,
        redis_params.REDIS_UPDATED_KEY
    ).decode('utf-8')
    return data_last_updated


def set_modified_datetime(redis_inst):
    '''
    set the date and time the data was last modified
    '''
    redis_inst.hset(
        redis_params.REDIS_HASH_NAME,
        redis_params.REDIS_MODIFIED_KEY,
        str(datetime.datetime.now(
            tzlocal.get_localzone()).strftime(redis_params.REDIS_TIME_FORMAT))
    )

def get_modified_datetime(redis_inst):
    '''
    retrieve the date and time the data was last modified
    '''
    data_last_modified = redis_inst.hget(
        redis_params.REDIS_HASH_NAME,
        redis_params.REDIS_MODIFIED_KEY
    ).decode('utf-8')
    if data_last_modified is None:
        data_last_modified = ''
    return data_last_modified

