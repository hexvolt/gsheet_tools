# Google Sheets API has quotas (default 100 requests per 100 seconds)
# Use this parameter to set a delay between the requests to prevent exceeding is (sec):
QUOTA_DELAY = 0.5

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
