import math
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Union

import click
from attr import dataclass
from cached_property import cached_property
from dateutil.parser import parse
from gspread import Worksheet, Cell
from gspread.utils import rowcol_to_a1, a1_to_rowcol

from models.base import BaseSpreadsheet
from utils.constants import RESULT_WARNING, CellType


TYPE_WORDS_MAPPING = {
    CellType.GROCERY: {
        "FOODLAND",
        "LOBLAWS",
        "WAL-MART",
        "NOFRILLS",
        "-MART",
        "RABBA",
        "FRESH MAR",
        "METRO",
    },
    CellType.TAKEOUTS: {
        "THE GREEK",
        "HORTONS",
        "STARBUCKS",
        "PANERA",
        "RABBA",
        "COFFEE",
        "PURDY",
        "JAZZ",
        "DUKE OF",
        "SECOND CUP",
        "EGGSMART",
    },
    CellType.FURNITURE_APPLIANCES: {"THE BRICK", "FAIRSTONE", "IKEA", "BED BATH"},
    CellType.GASOLINE: {"SHELL", "PETRO"},
    CellType.HOUSEKEEPING: {"SHOPPERS", "DOLLARAMA", "CANADIAN TIRE", "BED BATH"},
    CellType.GAS_ELECTRIC: {"HYD ELEC", "ENBRIDGE"},
    CellType.CLOTHING: {"WINNERS", "MARSHALLS", "HUDSON", "SPORTING LIFE"},
    CellType.FARES: {"PRESTO"},
    CellType.CAR_RENT: {"ENTERPRISE"},
    CellType.SUBSCRIPTIONS: {"NETFLIX", "DEEZER"},
    CellType.TV_INTERNET: {"BELL", ""},
    CellType.CHARITY: {"WAR AMPS", ""},
    CellType.PARKING: {"PARKING"},
    CellType.PHONES: {"MOBILE"},
    CellType.HAIRCUTS: {"BARBIERI"},
    CellType.ENTERTAINMENT: {"CINEMA", "CINEPLEX"},
}


@dataclass
class Transaction:
    worksheet: Worksheet
    has_receipt: bool
    created: date
    title: str
    price: Decimal
    label: str

    @classmethod
    def from_cells(cls, worksheet: Worksheet, row: int, cells: List):
        kwargs = dict(
            worksheet=worksheet, label=f"{TransactionHistory.HAS_RECEIPT_COLUMN}{row}"
        )
        for col, cell_value in enumerate(cells, 1):
            label = rowcol_to_a1(row, col)

            try:
                if label.startswith(TransactionHistory.HAS_RECEIPT_COLUMN):
                    kwargs.update(has_receipt=bool(cell_value))

                elif label.startswith(TransactionHistory.DATE_COLUMN):
                    kwargs.update(created=parse(cell_value).date())

                elif label.startswith(TransactionHistory.TITLE_COLUMN):
                    kwargs.update(title=cell_value)

                elif label.startswith(TransactionHistory.PRICE_COLUMN):
                    kwargs.update(price=Decimal(cell_value))
            except Exception:
                raise ValueError(
                    f"Can't convert '{cell_value}' from cell {label} ({worksheet.title}) into Transaction. "
                    f"Transaction wasn't created."
                )
        return cls(**kwargs)

    @cached_property
    def matching_types(self) -> List[CellType]:
        matches = []
        for cell_type, words in TYPE_WORDS_MAPPING.items():
            for word in words:
                if word in self.title.upper():
                    matches.append(cell_type)
        return matches

    @property
    def good_type(self) -> Union[CellType, None]:
        """Determine the good type by transaction title."""
        matching_types = self.matching_types
        if len(matching_types) > 1:
            raise ValueError(
                f"Ambiguous type - transaction can be one of {matching_types}"
            )

        elif len(matching_types) == 1:
            return matching_types[0]

        return None


class TransactionHistory(BaseSpreadsheet):
    """
    Represents the spreadsheet with the log of credit/debit card transactions.

    It is used to find all those transactions that are already in receipts, and
    therefore were imported. The rest of them will be ones without receipt and
    to be added to the billing later on.
    """

    HAS_RECEIPT_COLUMN = "A"
    DATE_COLUMN = "B"
    TITLE_COLUMN = "C"
    PRICE_COLUMN = "D"
    PAYMENT_COLUMN = "E"
    TIME_COLUMN = "F"

    price_match_threshold = Decimal(0.03)
    day_match_threshold = 2

    @cached_property
    def _tabs(self):
        return {
            worksheet.title: worksheet for worksheet in self.spreadsheet.worksheets()
        }

    @cached_property
    def content(self):
        """
        Lazy load of entire spreadsheet content.

        :return dict: {
            "Sheet1":  [[...], [...], ...],
            "Sheet2":  [[...], [...], ...],
        }
        """
        return {
            worksheet_title: worksheet.get_all_values()
            for worksheet_title, worksheet in self._tabs.items()
        }

    def fetch_transactions(self):
        """Read the transactions from transaction history spreadsheet into memory."""
        result = []
        for worksheet_title, row_containers in self.content.items():
            worksheet = self._tabs[worksheet_title]

            for row, cells in enumerate(row_containers, 1):
                if row == 1:
                    continue

                try:
                    transaction = Transaction.from_cells(
                        worksheet=worksheet, row=row, cells=cells
                    )
                except ValueError as e:
                    click.echo(RESULT_WARNING.format(e))
                    continue

                result.append(transaction)
        return result

    @cached_property
    def transactions(self) -> List[Transaction]:
        """
        Return all Transactions collected from all worksheets in the file.

        Once created, Transactions objects are mutable, so their `has_receipt`
        flag can be edited after for posting everything back into the spreadsheet.

        Unlike fetch_transactions(), this method is cached and populated only once.
        """
        return self.fetch_transactions()

    @cached_property
    def _transactions_by_date(self) -> Dict[date, list]:
        result = defaultdict(list)
        for transaction in self.transactions:
            result[transaction.created].append(transaction)
        return result

    def find_transactions(self, created, price, has_receipt):
        """
        Looks up the transaction for a certain day and price and certain has_receipt state.

        If the exact matches are not found on specified day, the closest days are
        checked because sometimes banks post transaction to the history on the next
        day or few. If the transaction with *exact* amount is found on next day,
        then it is returned.

        If the exact match by price is not found not on specified day, nor the next one,
        then the closest matches are logged and None is returned.

        :rtype: list or None
        """
        transactions_this_day = self._transactions_by_date[created]

        transactions_next_days = []
        for day in range(self.day_match_threshold):
            transactions_next_days.extend(
                self._transactions_by_date[created + timedelta(days=day + 1)]
            )

        transactions = transactions_this_day + transactions_next_days
        if has_receipt is not None:
            transactions = [
                transaction
                for transaction in transactions
                if transaction.has_receipt == has_receipt
            ]

        exact_matches = []
        for transaction in transactions:
            if math.isclose(transaction.price, price):
                if transaction.created > created:
                    click.echo(f"Found on the day {transaction.created}")
                exact_matches.append(transaction)

        if exact_matches:
            return exact_matches

        close_matches = []
        for transaction in transactions:
            difference = abs(transaction.price - price)

            if difference <= self.price_match_threshold:
                close_matches.append((transaction, difference))

        if not close_matches:
            return None

        min_diff = min(diff for _, diff in close_matches)
        close_matches = [
            transaction for transaction, diff in close_matches if diff == min_diff
        ]
        if close_matches:
            msg = "\n".join(str(t) for t in close_matches)
            click.echo(
                RESULT_WARNING.format(
                    f"Exact transaction for ({created}, {price}) was not found "
                    f"but there are close matches: {msg}"
                )
            )

        return None

    def post_to_spreadsheet(self):
        """Update spreadsheet with current transaction's has_receipt values."""
        worksheet_transactions = defaultdict(list)
        for transaction in self.transactions:
            worksheet_transactions[transaction.worksheet].append(transaction)

        for worksheet, transactions in worksheet_transactions.items():
            cell_list = [
                Cell(
                    *a1_to_rowcol(transaction.label),
                    "Y" if transaction.has_receipt else "",
                )
                for transaction in transactions
            ]
            worksheet.update_cells(cell_list=cell_list)

    def reset_flags(self):
        """Reset has_receipt flag value to False for all transactions in memory."""
        for transaction in self.transactions:
            transaction.has_receipt = False
