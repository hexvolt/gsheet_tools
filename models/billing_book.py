from models.base import BaseSpreadsheet
from models.month_billing import MonthBilling


class BillingBook(BaseSpreadsheet):
    """
    Represents an annual billing spreadsheet with 12 monthly billing tabs inside.
    """

    def get_month_billing(self, month: int) -> MonthBilling:
        raise NotImplementedError
