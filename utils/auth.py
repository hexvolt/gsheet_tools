from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']


def get_credentials():
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
    return credentials
