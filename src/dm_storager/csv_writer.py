import csv
import time
import datetime
import os

from csv import reader
from datetime import date
from pathlib import Path
from typing import List, Any

from dm_storager.protocol.schema import ArchieveData, ScannerSettings

appStartTime = datetime.datetime.fromtimestamp(time.time()).strftime(
    "%d-%m-%Y_%H.%M.%S"
)


class CSVWriter(object):
    
    HEADER = ["Timestamp", "Product Name", "Record"]

    def __init__(self, scanner_id: int):
        self._result_table: List[Any] = []
        self._scanner_id = scanner_id
        self._result_table = []

    def append_data(self, archieve_data: ArchieveData, scanner_settings: ScannerSettings) -> None:

        new_row = []

        for i in range(archieve_data.records_count):
            _timestamp = str(datetime.datetime.now())
            _product_name = scanner_settings.products[
                archieve_data.product_id
            ]
            _record = archieve_data.records[i]
            new_row = [_timestamp, _product_name, _record]
            self._result_table.append(new_row)

        self._store_data()

    def _store_header(self) -> None:
       with open(self._filename, "a", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerows(CSVWriter.HEADER)

    def _store_data(self) -> None:
        self._filename = self._get_file_path(self._scanner_id)
        sh = False
        with open(self._filename, "r") as csv_file:
            csv_reader = reader(csv_file)
            try:
                header = next(csv_reader)
            except StopIteration:
                sh = True
        if sh:
            with open(self._filename, "a", newline="") as csv_file:
                writer = csv.writer(csv_file, delimiter=";")
                writer.writerow(CSVWriter.HEADER)

        with open(self._filename, "a", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerows(self._result_table)

    def _get_file_path(self, scanner_id: int) -> Path:
        data_dir = Path.cwd() / "saved_data"
        os.makedirs(data_dir, exist_ok=True)
        current_date = str(date.today())
        file_path = data_dir / f"scanner_#{scanner_id}.{current_date}.csv"
        open(file_path, "a").close()
        return file_path

# w = CSVWriter(0)
# s_set = ScannerSettings(
#     products=["Product1","Product2","Product3","","","",],
#     server_ip="",
#     server_port=0,
#     gateway_ip="",
#     netmask="",
#     reserved=0
# )

# a_data = ArchieveData(
#     records_count=2,
#     record_len=8,
#     product_id=1,
#     records=[
#         "RECORD-1",
#         "RECORD-2",
#     ]
# )

# w.append_data(a_data, s_set)
# pass