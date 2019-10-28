from attr import dataclass

from utils.api import get_client


class BaseSpreadsheet:
    def __init__(self, filename):
        client = get_client()
        self.spreadsheet = client.open(filename)


@dataclass
class Color:
    red: float
    green: float
    blue: float
