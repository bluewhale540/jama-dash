import redis_data
import argparse
import sys
import pandas as pd
from pandas import ExcelWriter

def main(argv):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', dest='output', help='CSV output file name', required=True)
    args = parser.parse_args()
    redis_inst = redis_data.get_redis_inst()
    df = redis_data.get_dataframe(redis_inst)
    df.to_csv(args.output)

if __name__ == '__main__':
    main(sys.argv[1:])
