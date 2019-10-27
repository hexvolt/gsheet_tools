from cached_property import cached_property
from dateutil.parser import parse
from gspread.utils import a1_to_rowcol, rowcol_to_a1

from models.receipt import Receipt
from utils.constants import CellType
from utils.names import extract_number


class MonthBilling:
    """Represents a monthly billing tab."""

    FIRST_DAY_COLUMN = "E"

    CATEGORY_ROWS = {
        CellType.GROCERY: 14,
        CellType.TAKEOUTS: 15,
        CellType.HOUSEKEEPING: 24,
        CellType.FURNITURE_APPLIANCES: 25,
        CellType.CLOTHING: 28,
        CellType.GYM: 32,
        CellType.ENTERTAINMENT: 36,
        CellType.TRAVEL: 37,
        CellType.BOOKS: 38,
        CellType.GIFTS: 39,
        CellType.HOBBIES: 40,
        CellType.OTHER_FUN: 43,
        CellType.GASOLINE: 45,
        CellType.PARKING: 48,
        CellType.FARES: 49,
        CellType.DRUGS: 52,
        CellType.DENTAL_VISION: 53,
        CellType.OTHER: 88,
    }

    def __init__(self, worksheet):
        self.worksheet = worksheet

    @cached_property
    def month(self) -> int:
        """Return the month the billing month heet is related to."""
        try:
            return parse(self.worksheet.title).month
        except ValueError:
            raise ValueError("Billing month sheet must have month in the title.")

    @cached_property
    def year(self) -> int:
        """Return the year current billing month sheet belongs to."""
        try:
            year_string = extract_number(self.worksheet.spreadsheet.title)
            return parse(str(year_string)).year
        except ValueError:
            raise ValueError("Billing book must have a year in the title.")

    def import_receipt(self, receipt: Receipt):
        """Adds the data from the receipt to the month billing spreadsheet."""
        date_match = receipt.date.month == self.month and receipt.date.year == self.year
        if not date_match:
            raise ValueError(
                f"The receipt from {receipt.date} does not belong "
                f"to '{self.year}-{self.month} billing sheet."
            )

        cells_to_update = []
        for good_type, purchases in receipt.purchases_by_type.items():
            if not purchases:
                continue

            destination_label = self.get_destination_label(purchase=purchases[0])
            cell = self.worksheet.acell(
                destination_label, value_render_option="FORMULA"
            )
            cells_to_update.append(cell)

            for purchase in purchases:
                cell.value += (
                    f"+{purchase.price}" if cell.value else f"={purchase.price}"
                )

        self.worksheet.update_cells(cells_to_update, value_input_option="USER_ENTERED")

    def get_destination_label(self, purchase) -> str:
        """Return the cell label in a month billing for a certain Purchase."""
        row = self.CATEGORY_ROWS[purchase.good_type]
        _, col = a1_to_rowcol(f"{self.FIRST_DAY_COLUMN}1")
        col += purchase.date.day - 1
        return rowcol_to_a1(row, col)

    def clear_expenses(self):
        pass
