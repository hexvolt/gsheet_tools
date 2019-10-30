import click
from dateutil.parser import parse

from models.base import BaseSpreadsheet
from models.receipt import Receipt
from utils.constants import RESULT_OK, RESULT_ERROR, RESULT_WARNING
from utils.names import extract_date_string


class Workbook(BaseSpreadsheet):
    """
    Represents the source file with unordered receipts.
    """

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
                    new_title = self.spreadsheet.client.copy_worksheet_to(
                        worksheet=worksheet, dest_filename=dest_filename
                    )
                    self.spreadsheet.del_worksheet(worksheet)
                except Exception as e:
                    result_msg = RESULT_ERROR.format(e)
                else:
                    result_msg = f"{RESULT_OK} New title: '{new_title}'."
                click.echo(result_msg)
