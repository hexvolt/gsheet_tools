import time

import gspread
from gspread import Client
from oauth2client.service_account import ServiceAccountCredentials

from config import QUOTA_DELAY, SCOPES


class QuotaCompliantClient(Client):
    def request(self, *args, **kwargs):
        time.sleep(QUOTA_DELAY)
        return super().request(*args, **kwargs)


def get_credentials():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", SCOPES
    )
    return credentials


def get_client():
    credentials = get_credentials()
    client = gspread.authorize(credentials, client_class=QuotaCompliantClient)
    return client
