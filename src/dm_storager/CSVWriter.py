import csv
import time
import datetime
import os
import collections

appStartTime = datetime.datetime.fromtimestamp(time.time()).strftime(
    "%d-%m-%Y_%H.%M.%S"
)


class CSVWriter(object):
    def __init__(self):
        self._result_table = [[], []]
        self._presented_subtables = {}

        self._filename = str(self._get_file_path())

    def _get_file_path(self) -> str:

        data_dir = os.getcwd() + "\saved_data"
        os.makedirs(data_dir, exist_ok=True)
        file_path = data_dir + "\{}.data.csv".format(appStartTime)
        open(file_path, "a").close()

        return str(file_path)
