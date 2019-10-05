# noinspection PyPackageRequirements
from googleapiclient.discovery import build


class GSheetsClient:

    def __init__(self, credentials):
        service = build('sheets', 'v4', credentials=credentials)
        self.sheets = service.spreadsheets()
