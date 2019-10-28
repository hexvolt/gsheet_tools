import json
import time

import gspread
from gspread import Client
from gspread.urls import SPREADSHEETS_API_V4_BASE_URL
from gspread.utils import rowcol_to_a1
from oauth2client.service_account import ServiceAccountCredentials

from config import QUOTA_DELAY, SCOPES
from utils.cells import a1_to_coords


class QuotaCompliantClient(Client):
    def request(self, *args, **kwargs):
        time.sleep(QUOTA_DELAY)
        return super().request(*args, **kwargs)

    def insert_note(self, worksheet, label, note):
        """Insert one note into the google spreadsheet cell."""
        row, col = a1_to_coords(label)
        spreadsheet_id = worksheet.spreadsheet.id

        url = f"{SPREADSHEETS_API_V4_BASE_URL}/{spreadsheet_id}:batchUpdate"
        payload = {
            "requests": [
                {
                    "updateCells": {
                        "range": {
                            "sheetId": worksheet.id,
                            "startRowIndex": row,
                            "endRowIndex": row + 1,
                            "startColumnIndex": col,
                            "endColumnIndex": col + 1,
                        },
                        "rows": [{"values": [{"note": note}]}],
                        "fields": "note",
                    }
                }
            ]
        }
        self.request("post", url, json=payload)

    def get_all_notes(self, worksheet):
        """
        Get notes of all cells from a certain worksheet.

        :return dict: {
            "A1": "Blah",
            "L2": "Note"
        }
        """
        result = {}
        spreadsheet_id = worksheet.spreadsheet.id
        url = (
            f"{SPREADSHEETS_API_V4_BASE_URL}/{spreadsheet_id}?ranges='{worksheet.title}'"
            f"&fields=sheets/data/rowData/values/note"
        )
        response = self.request("get", url)
        content = json.loads(response.content)

        row_containers = content["sheets"][0]["data"][0]["rowData"]
        for row, row_container in enumerate(row_containers, 1):
            cell_containers = row_container.get("values", [])
            for col, cell_container in enumerate(cell_containers, 1):
                note = cell_container.get("note")
                if note:
                    label = rowcol_to_a1(row=row, col=col)
                    result[label] = note
        return result

    def insert_notes(self, worksheet, labels_notes, replace=False):
        """
        Adds specified notes to the cells.

        :param Worksheet worksheet: a worksheet to insert notes to
        :param dict labels_notes:
            {
                "A1": "car, house",
                "B2": "cheese, bread"
            }
        :param bool replace: if False, the notes will be appended to existing ones
        """
        spreadsheet_id = worksheet.spreadsheet.id

        existing_notes = {} if replace else self.get_all_notes(worksheet)

        url = f"{SPREADSHEETS_API_V4_BASE_URL}/{spreadsheet_id}:batchUpdate"
        requests_payload = []
        for label, note in labels_notes.items():
            row, col = a1_to_coords(label)
            existing_note = existing_notes.get(label, "")
            note = f"{existing_note}, {note}" if existing_note else note
            requests_payload.append(
                {
                    "updateCells": {
                        "range": {
                            "sheetId": worksheet.id,
                            "startRowIndex": row,
                            "endRowIndex": row + 1,
                            "startColumnIndex": col,
                            "endColumnIndex": col + 1,
                        },
                        "rows": [{"values": [{"note": note}]}],
                        "fields": "note",
                    }
                }
            )
        self.request("post", url, json={"requests": [requests_payload]})


def get_credentials():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", SCOPES
    )
    return credentials


def get_client():
    credentials = get_credentials()
    client = gspread.authorize(credentials, client_class=QuotaCompliantClient)
    return client
