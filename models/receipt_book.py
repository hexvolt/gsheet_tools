from collections import Counter

import click
from cached_property import cached_property

from models.base import BaseSpreadsheet
from models.receipt import Receipt
from utils.constants import RESULT_SKIPPED, RESULT_OK, RESULT_ERROR, RESULT_WARNING
from utils.names import get_normalized_title


class ReceiptBook(BaseSpreadsheet):
    """
    Represents a spreadsheet file with a collection of receipts for the whole month.

    Typical name `2019-01`.
    """

    @cached_property
    def _receipts_map(self):
        return {
            worksheet.title: Receipt(worksheet=worksheet)
            for worksheet in self.spreadsheet.worksheets()
        }

    @property
    def receipts(self):
        return list(self._receipts_map.values())

    def get_receipt(self, title):
        return self._receipts_map.get(title)

    def rename_tabs(self, one_by_one, dry=False):
        """Rename each tab title to reflect the day number of the receipt."""
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
        """Check if the prices in each tab add up correctly."""
        for receipt in self.receipts:
            click.echo(f"{receipt.worksheet.title} ==> ", nl=False)
            try:
                receipt.prices_are_valid(raise_exception=True)
            except ValueError as e:
                click.echo(RESULT_WARNING.format(e))
                continue
            except Exception as e:
                click.echo(RESULT_ERROR.format(e))
                continue

            if receipt.discount:
                click.echo(
                    RESULT_OK + f"Receipt has a discount/loyalty of {receipt.discount}."
                )
            else:
                click.echo(RESULT_OK)

    def find_duplicates(self):
        comparison_attrs = []
        for receipt in self.receipts:
            click.echo(f"Reading receipt {receipt.worksheet.title}")
            try:
                comparison_attrs.append(
                    (
                        receipt.date,
                        receipt.subtotal,
                        receipt.total,
                        receipt.actually_paid,
                    )
                )
            except (ValueError, NotImplementedError) as e:
                click.echo(
                    RESULT_WARNING.format(
                        f"Receipt {receipt.worksheet.title} has wrong data and skipped from analysis: {e}"
                    )
                )

        for attrs, count in Counter(comparison_attrs).items():
            if count > 1:
                click.echo(
                    RESULT_WARNING.format(
                        f"There are likely {count} duplicates of receipt from {attrs[0]}"
                    )
                )
        click.echo(RESULT_OK.format(f"No other duplicates found."))
