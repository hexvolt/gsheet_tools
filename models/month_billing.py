import math
from decimal import Decimal

import click
from cached_property import cached_property
from dateutil.parser import parse
from gspread import Cell
from gspread.utils import a1_to_rowcol, rowcol_to_a1

from models.receipt import Receipt
from utils.constants import CellType, RESULT_WARNING
from utils.names import extract_number


class MonthBilling:
    """Represents a monthly billing tab."""

    FIRST_DAY_COLUMN = "E"
    LAST_DAY_COLUMN = "AI"

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

    def import_receipt(self, receipt: Receipt, note_threshold=50):
        """
        Adds the data from the receipt to the month billing spreadsheet.

        If a purchase in receipt exceeds threshold, it's name will be included
        into a note for a cell.

        Rules for HST/taxes:
            if all purchases are groceries, then it is added too total grocery price;
            if there are other categories, then it is added to the biggest one.
        """
        date_match = receipt.date.month == self.month and receipt.date.year == self.year
        if not date_match:
            raise ValueError(
                f"The receipt from {receipt.date} does not belong "
                f"to '{self.year}-{self.month} billing sheet."
            )

        if receipt.tax_belongs_to is None:
            click.echo(
                RESULT_WARNING.format(
                    f"Can't determine which category the tax belongs to in receipt '{receipt.worksheet.title}'"
                )
            )

        cells_to_update = []
        notes_to_add = {}
        for good_type, purchases in receipt.purchases_by_type.items():
            if not purchases:
                continue

            destination_label = self.get_destination_label(purchase=purchases[0])
            cell = self.worksheet.acell(
                destination_label, value_render_option="FORMULA"
            )
            cells_to_update.append(cell)

            cell_str_value = self.worksheet.acell(destination_label).value
            cell_price_before = Decimal(cell_str_value) if cell_str_value else 0

            cell_formula = cell.value
            for purchase in purchases:
                cell_formula += (
                    f"+{purchase.price}" if cell_formula else f"={purchase.price}"
                )

            is_tax_here = receipt.tax and good_type == receipt.tax_belongs_to
            if is_tax_here:
                cell_formula += f"+{receipt.tax}"

            cell.value = cell_formula

            category_price = receipt.get_category_price(good_type=good_type)
            added_price = category_price + (receipt.tax if is_tax_here else 0)

            note = ", ".join(
                purchase.good_name
                for purchase in purchases
                if purchase.price > note_threshold
            )
            if note:
                notes_to_add[destination_label] = note

            if cell_price_before and math.isclose(cell_price_before % added_price, 0):
                click.echo(
                    RESULT_WARNING.format(
                        f"Purchase in a cell {destination_label} is likely imported multiple times."
                    )
                )

        if notes_to_add:
            self.worksheet.spreadsheet.client.insert_notes(
                worksheet=self.worksheet, labels_notes=notes_to_add, replace=False
            )
        self.worksheet.update_cells(cells_to_update, value_input_option="USER_ENTERED")

    def get_destination_label(self, purchase) -> str:
        """Return the cell label in a month billing for a certain Purchase."""
        row = self.CATEGORY_ROWS[purchase.good_type]
        _, col = a1_to_rowcol(f"{self.FIRST_DAY_COLUMN}1")
        col += purchase.date.day - 1
        return rowcol_to_a1(row, col)

    def clear_expenses(self):
        """Clear all expenses and notes for the month in all categories."""
        _, col_1 = a1_to_rowcol(f"{self.FIRST_DAY_COLUMN}1")
        _, col_31 = a1_to_rowcol(f"{self.LAST_DAY_COLUMN}1")
        cell_list = [
            Cell(row=row, col=col, value="")
            for col in range(col_1, col_31 + 1)
            for row in self.CATEGORY_ROWS.values()
        ]
        label_notes = {rowcol_to_a1(cell.row, cell.col): "" for cell in cell_list}
        self.worksheet.update_cells(cell_list=cell_list)
        self.worksheet.spreadsheet.client.insert_notes(
            worksheet=self.worksheet, labels_notes=label_notes, replace=True
        )
