import click
from cached_property import cached_property
from dateutil.parser import parse

from models.base import BaseSpreadsheet
from models.month_billing import MonthBilling
from utils.constants import RESULT_WARNING


class BillingBook(BaseSpreadsheet):
    """
    Represents an annual billing spreadsheet with 12 monthly billing tabs inside.
    """

    @cached_property
    def _month_billings_map(self):
        result = {}
        for worksheet in self.spreadsheet.worksheets():
            try:
                month = parse(worksheet.title).month
            except ValueError:
                continue

            result[month] = MonthBilling(worksheet=worksheet)

        if len(result) != 12:
            click.echo(
                RESULT_WARNING.format(
                    f"Only {len(result)} moths found in year billing book."
                )
            )
        return result

    @property
    def month_billings(self):
        return self._month_billings_map.values()

    def get_month_billing(self, month: int) -> MonthBilling:
        return self._month_billings_map.get(month)
