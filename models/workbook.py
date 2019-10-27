import json

import click
from dateutil.parser import parse
from gspread.urls import SPREADSHEETS_API_V4_BASE_URL

from models.base import BaseSpreadsheet
from models.receipt import Receipt
from utils.constants import RESULT_OK, RESULT_ERROR, RESULT_WARNING
from utils.names import extract_date_string


class Workbook(BaseSpreadsheet):
    """
    Represents the source file with unordered receipts.
    """

    def copy_worksheet_to(self, src_worksheet, dest_filename):
        """
        Copy a tab from current spreadsheet file to the destination spreadsheet.

        The copied tab title is assigned by Google Sheets automatically and returned
        as a result of this method.

        :param Worksheet src_worksheet: source tab
        :param str dest_filename: filename of the destination spreadsheet
        :return str: an assigned title of the copied tab in the destination spreadsheet.
        :raise: WorksheetNotFound, SpreadsheetNotFound
        """
        source_file_id = self.spreadsheet.id
        source_sheet_id = src_worksheet.id
        dest_spreadsheet = self.client.open(dest_filename)
        dest_file_id = dest_spreadsheet.id

        url = f"{SPREADSHEETS_API_V4_BASE_URL}/{source_file_id}/sheets/{source_sheet_id}:copyTo"
        payload = {"destinationSpreadsheetId": dest_file_id}
        response = self.client.request("post", url, json=payload)

        new_title = json.loads(response.content)["title"]
        return new_title

    def move_tabs(self, one_by_one, dry=False, unambiguous_only=False):
        """
        Move each tab of the workbook to an appropriate Receipt book.
        """
        for worksheet in self.spreadsheet.worksheets():
            receipt = Receipt(worksheet)
            click.echo(
                f"'{worksheet.title}' ({receipt.store}) will go to ==> ", nl=False
            )
            try:
                date = parse(extract_date_string(worksheet.title))
            except ValueError as e:
                click.echo(RESULT_WARNING.format(e))
                continue

            dest_filename = f"{date.year}-{date.month:02d}"

            is_unambiguous = date.day > 12 or date.day == date.month
            if unambiguous_only and not is_unambiguous:
                click.echo(RESULT_WARNING.format("Skipped because date is ambiguous."))
                continue

            click.echo(f"'{dest_filename}'")
            if dry:
                continue

            is_unambiguous = date.day > 12 or date.day == date.month
            if unambiguous_only and not is_unambiguous:
                click.echo(RESULT_WARNING.format("Skipped because date is ambiguous."))
                continue

            if not one_by_one or (one_by_one and click.confirm(f"Move?", default=True)):
                try:
                    new_title = self.copy_worksheet_to(
                        src_worksheet=worksheet, dest_filename=dest_filename
                    )
                    self.spreadsheet.del_worksheet(worksheet)
                except Exception as e:
                    result_msg = RESULT_ERROR.format(e)
                else:
                    result_msg = f"{RESULT_OK} New title: '{new_title}'."
                click.echo(result_msg)
