import csv
import time
import datetime
import os
from pathlib import Path
from typing import List, Any

appStartTime = datetime.datetime.fromtimestamp(time.time()).strftime(
    "%d-%m-%Y_%H.%M.%S"
)


class CSVWriter(object):
    def __init__(self, scanner_id: int):
        self._result_table: List[Any] = []
        self._filename = self._get_file_path(scanner_id)

    def _get_file_path(self, scanner_id: int) -> Path:

        data_dir = Path.cwd() / "saved_data"
        os.makedirs(data_dir, exist_ok=True)
        file_path = data_dir / f"scanner_#{scanner_id}.data.csv"
        open(file_path, "a").close()

        return file_path

    def append_data(self, archieve_data: str) -> None:

        count = int(archieve_data[0])
        record_len = int(archieve_data[1])
        archieve_data = archieve_data[2:]
        listed_data = []

        for i in range(0, count, record_len):
            record = archieve_data[i : i + record_len]
            # archieve_data = archieve_data[i + record_len :]
            listed_data.extend(record)

        self._result_table.append(listed_data)

    def store_data(self) -> None:

        with open(self._filename, "w", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerows(self._result_table)


test_id = 1
tl1 = [5, 1, 1, 2, 3, 4, 5]
tl2 = [3, 1, "a", "b", "c"]
wr = CSVWriter(test_id)
wr.append_data(tl1)
wr.store_data()
wr.append_data(tl2)
wr.store_data()
