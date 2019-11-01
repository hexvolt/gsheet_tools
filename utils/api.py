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

    def copy_worksheet_to(self, worksheet, dest_filename):
        """
        Copy a tab from current spreadsheet file to the destination spreadsheet.

        The copied tab title is assigned by Google Sheets automatically and returned
        as a result of this method.

        :param Worksheet worksheet: source tab
        :param str dest_filename: filename of the destination spreadsheet
        :return str: an assigned title of the copied tab in the destination spreadsheet.
        :raise: WorksheetNotFound, SpreadsheetNotFound
        """
        source_file_id = worksheet.spreadsheet.id
        source_sheet_id = worksheet.id
        dest_spreadsheet = self.open(dest_filename)
        dest_file_id = dest_spreadsheet.id

        url = f"{SPREADSHEETS_API_V4_BASE_URL}/{source_file_id}/sheets/{source_sheet_id}:copyTo"
        payload = {"destinationSpreadsheetId": dest_file_id}
        response = self.request("post", url, json=payload)

        new_title = json.loads(response.content)["title"]
        return new_title

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
        if not labels_notes:
            return

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

    def get_all_colors(self, worksheet):
        """
        Return background colors of all cells.

        :return dict: {
            "A1": {"red": 0.858689, "green": 0.3425, "blue": 0.85004},
            ...
        }
        """
        result = {}
        spreadsheet_id = worksheet.spreadsheet.id
        url = (
            f"{SPREADSHEETS_API_V4_BASE_URL}/{spreadsheet_id}?ranges='{worksheet.title}'"
            f"&fields=sheets/data/rowData/values/userEnteredFormat/backgroundColor"
        )
        response = self.request("get", url)
        content = json.loads(response.content)

        row_containers = content["sheets"][0]["data"][0]["rowData"]
        for row, row_container in enumerate(row_containers, 1):
            cell_containers = row_container.get("values", [])
            for col, cell_container in enumerate(cell_containers, 1):
                formatting = cell_container.get("userEnteredFormat")
                if formatting:
                    label = rowcol_to_a1(row=row, col=col)
                    result[label] = formatting.get("backgroundColor")
        return result


def get_credentials():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", SCOPES
    )
    return credentials


def get_client():
    credentials = get_credentials()
    client = gspread.authorize(credentials, client_class=QuotaCompliantClient)
    return client
