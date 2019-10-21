import click

from models.receipt import Receipt
from utils.auth import get_client
from utils.constants import RESULT_SKIPPED, RESULT_OK, RESULT_ERROR, RESULT_WARNING
from utils.names import get_normalized_title


class Spreadsheet:
    """
    Represents a spreadsheet file with all the receipts for the whole month. 
    """

    def __init__(self, filename):
        client = get_client()
        self.spreadsheet = client.open(filename)

    def rename_tabs(self, one_by_one, dry=False):
        names_registry = set()
        for worksheet in self.spreadsheet.worksheets():
            title_before = worksheet.title
            try:
                normalized_title = get_normalized_title(
                    tab_title=title_before,
                    filename=self.spreadsheet.title,
                    names_registry=names_registry,
                )
            except ValueError as e:
                conversion_error = RESULT_WARNING.format(e) if dry else RESULT_SKIPPED
                normalized_title = None
            else:
                conversion_error = None

            names_registry.add(normalized_title or title_before)

            click.echo(
                f"{title_before} ==> " + f"{normalized_title or conversion_error}"
            )
            if dry or conversion_error:
                continue

            if not one_by_one or one_by_one and click.confirm(f"Rename?", default=True):
                result_msg = RESULT_SKIPPED if conversion_error else RESULT_OK
                try:
                    worksheet.update_title(normalized_title)
                except Exception as e:
                    result_msg = RESULT_ERROR.format(e)
                click.echo(result_msg)

    def reorder(self):
        """Sort tabs in the spreadsheet by title alphabetically."""
        api_payload = []
        title_id_map = {
            worksheet.title: worksheet.id for worksheet in self.spreadsheet.worksheets()
        }
        sorted_titles = sorted(title_id_map.keys())
        for i, title in enumerate(sorted_titles):
            api_payload.append(
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": title_id_map.get(title), "index": i},
                        "fields": "index",
                    }
                }
            )
        try:
            self.spreadsheet.batch_update(body={"requests": api_payload})
        except Exception as e:
            click.echo(RESULT_ERROR.format(e))
        else:
            click.echo(RESULT_OK)

    def validate(self):
        for worksheet in self.spreadsheet.worksheets():
            click.echo(f"{worksheet.title} ==> ", nl=False)
            try:
                receipt = Receipt(worksheet)
                receipt.prices_are_valid(raise_exception=True)
            except ValueError as e:
                click.echo(RESULT_WARNING.format(e))
            except Exception as e:
                click.echo(RESULT_ERROR.format(e))
            else:
                click.echo(RESULT_OK)

    def find_duplicates(self):
        click.echo("Not implemented.")
