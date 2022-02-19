import json

from pathlib import Path
from typing import List, NamedTuple
from unittest import result

from dm_storager.structs import ScannerStat

class ValidationResult(NamedTuple):
    result: bool
    msg: str

def is_valid_scanner_info(scanner: ScannerStat) -> ValidationResult:
    
    r = ValidationResult()
    r.result = True
    r.msg = ""


def scanners_settings_reading(settings_path: Path) -> List[ScannerStat]:
    scanners = []

    with open(settings_path, "r") as settings_file:
        scanners = json.load(settings_file)
        
    return scanners