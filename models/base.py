from utils.api import get_client


class BaseSpreadsheet:
    def __init__(self, filename):
        client = get_client()
        self.spreadsheet = client.open(filename)
