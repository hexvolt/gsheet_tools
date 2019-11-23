import math
from collections import defaultdict, Counter
from copy import copy
from datetime import date
from typing import List

import click
from cached_property import cached_property
from dateutil.parser import parse
from gspread import Cell
from gspread.utils import rowcol_to_a1, a1_to_rowcol
from natsort import natsorted

from models.base import Color
from models.purchase import Purchase
from utils.cells import a1_to_coords, price_to_decimal, get_earliest_label
from utils.constants import CellType, GOODS_TYPES, SUMMARY_TYPES, HST, RESULT_WARNING
from utils.names import extract_number


class Receipt:
    """
    Represents a worksheet with a receipt.

    Encapsulates all data about receipt.
    """

    STORE_CELL = "G2"
    TEXT_CELL = "H2"
    JSON_CELL = "I2"
    LINE_COLUMN = "A"
    NAME_COLUMN = "B"
    CODE_COLUMN = "C"
    PRICE_COLUMN = "D"

    def __init__(self, worksheet):
        """Instantiate the Receipt from the *normalized worksheet* tab."""
        self.worksheet = worksheet

    @cached_property
    def content(self):
        """Lazy load of entire spreadsheet content."""
        return self.worksheet.get_all_values()

    @cached_property
    def _background_colors(self):
        client = self.worksheet.spreadsheet.client
        cells_colors = client.get_all_colors(self.worksheet)
        result = {
            label: Color(**color_props) for label, color_props in cells_colors.items()
        }
        return result

    @cached_property
    def date(self) -> date:
        """
        Return the date the receipt belongs to.

        Currently works only if Receipt is created from
        normalized tab that belongs to appropriate receipt book
        with proper title.

        So far this is the only way to be sure date is unambiguous,
        because the step of sorting receipts into receipt books
        is done manually and the date is validated by human.
        """
        try:
            day_from_title = int(extract_number(self.worksheet.title))
            date_from_spreadsheet = parse(self.worksheet.spreadsheet.title)
        except ValueError:
            raise NotImplementedError(
                "Receipt must have normalized title with day number and "
                "belong to a specific receipt book of name 'YYYY-MM'."
            )
        return date(
            year=date_from_spreadsheet.year,
            month=date_from_spreadsheet.month,
            day=day_from_title,
        )

    @property
    def store(self):
        y, x = a1_to_coords(self.STORE_CELL)
        try:
            return self.content[y][x]
        except IndexError:
            raise ValueError(
                f"Store cell {self.STORE_CELL} was not found in {self.worksheet.title}"
            )

    @property
    def raw_text(self):
        y, x = a1_to_coords(self.STORE_CELL)
        try:
            return self.content[y][x]
        except IndexError:
            raise ValueError(
                f"Raw text cell {self.TEXT_CELL} was not found in {self.worksheet.title}"
            )

    @property
    def raw_json(self):
        y, x = a1_to_coords(self.STORE_CELL)
        try:
            return self.content[y][x]
        except IndexError:
            raise ValueError(
                f"Raw JSON cell {self.JSON_CELL} was not found in {self.worksheet.title}"
            )

    def get_cell_color(self, label):
        return self._background_colors.get(label)

    def get_cell_type(self, label):
        cell_color = self.get_cell_color(label)
        try:
            return CellType(cell_color)
        except ValueError:
            return None

    @cached_property
    def _names(self):
        """
        Get all names from the Names column with recognized type.

        This method practices lazy evaluation - the first time a
        certain good gets requested, the entire column of purchased
        items gets parsed. This is done for performance reasons in
        order to reduce the number of API requests because it takes
        one API call to get the style of each cell.

        :return dict: a map sorted by cell label
            {
                "B8": ('Bread', CellType.GROCERY),
                "B10": ('SUSHI ROLL', CellType.TAKEOUTS),
                "B14": ('DEBIT', CellType.REGULAR),
                ...
            }
        """
        result = {}

        _, col = a1_to_rowcol(f"{self.NAME_COLUMN}1")

        for row, line in enumerate(self.content, 1):
            if row == 1:
                continue

            value = line[col - 1]
            label = rowcol_to_a1(row, col)
            cell_type = self.get_cell_type(label=label)
            if (not cell_type or cell_type == CellType.REGULAR) and not value:
                continue

            result[label] = (value, cell_type)

        result = dict(natsorted(result.items()))
        return result

    @cached_property
    def goods(self):
        """
        Return a dict with goods names.

        Unlike _names() this one returns only those which belong to
        a certain goods category, ignoring all other kind of cells.

        :return dict:
            {
                "B8": ('Bread', CellType.GROCERY),
                "B10": ('SUSHI ROLL', CellType.TAKEOUTS),
                ...
            }
        """
        return {
            label: (name, cell_type)
            for label, (name, cell_type) in self._names.items()
            if cell_type in GOODS_TYPES
        }

    @cached_property
    def _prices(self):
        """
        Get all prices and recognize their type.

        This method practices lazy evaluation too for the same reasons.

        :return dict: a map sorted by cell label
            {
                "D10": (Decimal(3.45), CellType.REGULAR),
                "D12": (Decimal(4.56), CellType.REGULAR),
                ...
                "D13": (Decimal(1.23), CellType.TOTAL),
                "D15": (Decimal(1.23), CellType.TAX),
            }
        """
        result = {}

        _, col = a1_to_rowcol(f"{self.PRICE_COLUMN}1")
        price_cells = [
            Cell(row=row, col=col, value=line[col - 1])
            for row, line in enumerate(self.content, 1)
            if line[col - 1] and row > 1
        ]

        for cell in reversed(price_cells):
            label = rowcol_to_a1(cell.row, cell.col)
            amount = price_to_decimal(
                cell.value, worksheet_title=self.worksheet.title, label=label
            )

            is_summary_collected = all(
                price_type in result for price_type in SUMMARY_TYPES
            )

            if is_summary_collected:
                result[label] = (amount, CellType.REGULAR)
                # if all summary prices are identified already, then we don't need
                # to check the color of other prices because the rest of them are
                # regular prices. That's why we move on to the next cell right away.
                continue

            cell_type = self.get_cell_type(label=label) or CellType.REGULAR
            result[label] = (amount, cell_type)

        result = dict(natsorted(result.items()))
        return result

    @cached_property
    def price_stats(self):
        """
        Return a sum of all prices of each type.

        NOTE: this is isolated from purchases, and there is no
        grocery types here. This is only about summary prices
        and all others fall into REGULAR.
        :return dict:
            {
                CellType.TOTAL: Decimal(3.45),
                CellType.REGULAR: Decimal(34.56),
                CellType.TAX: Decimal(1.23)
                ...
            }
        """
        result = {}
        for label, (price, cell_type) in self._prices.items():
            if cell_type in result and cell_type not in [
                CellType.ACTUALLY_PAID,
                CellType.TOTAL,
            ]:
                result[cell_type] += price
            else:
                result[cell_type] = price
        return result

    @cached_property
    def goods_prices(self):
        """
        Get a dict of all goods prices.

        :return dict: a map
            {
                "D10": Decimal(3.45),
                "D12": Decimal(4.56),
                ...
            }
        """
        return {
            label: price
            for label, (price, cell_type) in self._prices.items()
            if cell_type == CellType.REGULAR or not cell_type
        }

    @cached_property
    def purchases(self) -> List[Purchase]:
        """
        Match goods` names with appropriate prices and return list of Purchases.

        This method handles possible recognition artifacts when prices are not
        aligned with the goods and can be shifted up or down. It also handles
        the case when one good may have multiple prices which need to be added up.

        :return list: list of Purchases
        """
        result = []
        goods = copy(self.goods)
        goods_prices = copy(self.goods_prices)
        if not goods_prices and len(goods) == 1:
            goods_prices = {
                f"{self.PRICE_COLUMN}3": self.subtotal
                or self.total
                or self.actually_paid
            }

        elif len(goods_prices) < len(goods):
            raise ValueError(f"Some prices are missing in '{self.worksheet.title}'")

        # we determine if there are any goods with multiple prices per item in order
        # to determine the strategy of matching goods with the prices. Sometimes,
        # due to recognition artifacts, price may be shifted up or down comparing to
        # the item name, and therefore may appear to belong to the item which already
        # has the price. In some situations multiple prices per item is a valid case.
        # So, to distinguish that, we check it the total number of goods matches the
        # total number of prices: if they are equal, then we have an artifact.
        multiple_prices_per_good = len(goods_prices) > len(goods)

        while goods:
            good_label, (good_name, good_type) = next(iter(goods.items()))
            del goods[good_label]

            if multiple_prices_per_good:
                # greedy strategy - we should add as many prices as we can
                # before meeting the next good's name
                next_good_label = next(iter(goods), "")
                next_good_met = False
                result_price = 0
                while not next_good_met and goods_prices:
                    price_label, price = next(iter(goods_prices.items()))
                    result_price += price
                    del goods_prices[price_label]

                    if not goods_prices:
                        continue
                    next_price_label = next(iter(goods_prices), "")
                    earliest_label = get_earliest_label(
                        next_price_label, next_good_label
                    )
                    next_good_met = earliest_label == next_good_label
            else:
                price_label, result_price = next(iter(goods_prices.items()))
                del goods_prices[price_label]

            purchase = Purchase(
                good_name=good_name,
                good_type=good_type,
                good_label=good_label,
                price=result_price,
                created=self.date,
            )
            result.append(purchase)

        return result

    @property
    def purchases_by_type(self):
        """
        Return Purchases of the receipt grouped by their good type.

        return: {
            CellType.GROCERIES: [Purchase(), Purchase()],
            CellType.HOUSEKEEPING: [Purchase(), ...],
            ...
        }
        """
        result = defaultdict(list)
        for purchase in self.purchases:
            result[purchase.good_type].append(purchase)

        if not result:
            raise ValueError(
                f"No categorized purchases found in receipt {self.worksheet.title}. "
                f"Probably nothing is marked."
            )
        return result

    def get_category_price(self, good_type):
        """Return total price of all purchases of certain category (good type)."""
        mapping = {
            good_type: sum(purchase.price for purchase in purchases)
            for good_type, purchases in self.purchases_by_type.items()
        }
        return mapping.get(good_type)

    @cached_property
    def most_expensive_category(self) -> CellType:
        category_prices = [
            (good_type, sum(purchase.price for purchase in purchases))
            for good_type, purchases in self.purchases_by_type.items()
        ]
        category_prices = sorted(category_prices, key=lambda t: t[1], reverse=True)
        most_expensive_category, _ = category_prices[0]
        return most_expensive_category

    @property
    def actually_paid(self):
        return self.price_stats.get(CellType.ACTUALLY_PAID)

    @property
    def total(self):
        return self.price_stats.get(CellType.TOTAL)

    @property
    def subtotal(self):
        return self.price_stats.get(CellType.SUBTOTAL)

    @property
    def tax(self):
        return self.price_stats.get(CellType.TAX)

    @property
    def discount(self):
        """
        Return the difference between actually paid amound and total price of all purchases.

        If there was some discount applied (and it wasn't specified in the goods), the
        actually paid amount can be less than the sum of all purchases. In this case,
        this property will return the positive number - amount of discoung.

        In all other cases, it will be 0.
        """
        total = self.total or sum(p.price for p in self.purchases)
        if self.actually_paid and self.actually_paid < total:
            discount = abs(self.actually_paid - total)
        else:
            discount = 0
        return discount

    @cached_property
    def tax_belongs_to(self) -> CellType:
        """Returns the good type where the tax allegedly belongs."""
        if len(self.purchases_by_type) == 1 or not self.tax:
            return list(self.purchases_by_type.keys())[0]

        category_prices = {
            good_type: sum(purchase.price for purchase in purchases)
            for good_type, purchases in self.purchases_by_type.items()
        }
        sorted_category_prices = sorted(
            category_prices.items(), key=lambda i: i[1], reverse=True
        )

        result, tax_commensurate = None, False
        for good_type, total_price in sorted_category_prices:
            tax_commensurate = self.tax <= (HST * total_price)

            if tax_commensurate:
                result = good_type

            if good_type != CellType.GROCERY and tax_commensurate:
                break

        if sorted_category_prices and not result:
            result = sorted_category_prices[0]

        return result

    def prices_are_valid(self, raise_exception=True):
        """Return True if all prices adds up correctly to subtotal and total numbers."""
        if not self._prices:
            if raise_exception:
                raise ValueError(f"There is no prices in {self.worksheet.title}.")
            else:
                return False

        calculated_sum = self.price_stats.get(CellType.REGULAR, 0)
        if not self.subtotal and not calculated_sum:
            # some receipts has just one total price
            return True

        tax = self.tax or 0
        match_total = math.isclose(
            (self.total or self.actually_paid), (self.subtotal or calculated_sum) + tax
        )
        if raise_exception and not match_total:
            raise ValueError(
                f"Subtotal {self.subtotal or calculated_sum} + tax {tax} is not equal to amount "
                f"{self.total or self.actually_paid} in tab '{self.worksheet.title}'"
            )

        if self.subtotal and calculated_sum:
            match_subtotal = math.isclose(calculated_sum, self.subtotal)
            if raise_exception and not match_subtotal:
                raise ValueError(
                    f"Sum of prices {calculated_sum} is not equal to subtotal amount {self.subtotal} "
                    f"in tab '{self.worksheet.title}'"
                )
            result = match_subtotal and match_total
        else:
            result = match_total

        return result
