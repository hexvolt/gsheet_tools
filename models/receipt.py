from enum import Enum

from cached_property import cached_property
from gspread import Cell
from gspread.utils import rowcol_to_a1, a1_to_rowcol
from gspread_formatting import get_user_entered_format, Color

from utils.cells import a1_to_coords, price_to_decimal


class CellType(Enum):
    REGULAR = None
    TAX = Color(red=0.8, green=0.25490198, blue=0.14509805)
    SUBTOTAL = Color(red=0.41568628, green=0.65882355, blue=0.30980393)
    TOTAL = Color(red=0.21960784, green=0.4627451, blue=0.11372549)
    ACTUALLY_PAID = Color(red=0.15294118, green=0.30588236, blue=0.07450981)
    DATE = Color(red=0.23529412, green=0.47058824, blue=0.84705883)

    # Food, glorious food
    GROCERY = Color(red=1, green=0.9490196, blue=0.8)
    TAKEOUTS = Color(red=0.9764706, green=0.79607844, blue=0.6117647)

    # The roof over your head
    HOUSEKEEPING = Color(red=0.91764706, green=0.81960785, blue=0.8627451)
    FURNITURE_APPLIANCES = Color(red=0.8352941, green=0.6509804, blue=0.7411765)

    # Style and personal care
    CLOTHING = Color(red=0.8117647, green=0.8862745, blue=0.9529412)
    GYM = Color(red=0.62352943, green=0.77254903, blue=0.9098039)

    # Fun stuff
    ENTERTAINMENT = Color(red=0.7176471, green=0.91764706, blue=0.7019608)
    TRAVEL = Color(red=0.44705883, green=0.84705883, blue=0.4509804)
    BOOKS = Color(red=0.30588236, green=0.7019608, blue=0.3529412)
    GIFTS = Color(red=0.5529412, green=0.9372549, blue=0.85490197)
    HOBBIES = Color(red=0.49019608, green=0.83137256, blue=0.7607843)
    OTHER_FUN = Color(red=0.41960785, green=0.7137255, blue=0.6509804)

    # Getting around
    GASOLINE = Color(red=0.7764706, green=0.6745098, blue=1)
    PARKING = Color(red=0.5568628, green=0.4862745, blue=0.7647059)
    FARES = Color(red=0.85882354, green=0.6431373, blue=0.9843137)

    # Health care
    DRUGS = Color(red=0.6431373, green=0.7607843, blue=0.95686275)
    DENTAL_VISION = Color(red=0.42745098, green=0.61960787, blue=0.92156863)

    # Other
    OTHER = Color(red=0.7176471, green=0.7176471, blue=0.7176471)


class Receipt:
    """
    Represents a worksheet with receipt.

    Encapsulates all data about receipt.
    """

    STORE_CELL = "G2"
    TEXT_CELL = "H2"
    JSON_CELL = "I2"
    LINE_COLUMN = "A"
    NAME_COLUMN = "B"
    CODE_COLUMN = "C"
    PRICE_COLUMN = "D"

    SUMMARY_TYPES = (
        CellType.TAX,
        CellType.SUBTOTAL,
        CellType.TOTAL,
        CellType.ACTUALLY_PAID,
    )

    def __init__(self, worksheet):
        self.worksheet = worksheet
        self.content = worksheet.get_all_values()

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
        native_format = get_user_entered_format(self.worksheet, label=label)
        return native_format.backgroundColor

    def get_cell_type(self, label):
        cell_color = self.get_cell_color(label)
        try:
            return CellType(cell_color)
        except ValueError:
            return None

    @cached_property
    def _names(self):
        """
        Get all names from the Names column and recognize their type.

        This method practices lazy evaluation - the first time a
        certain good gets requested, the entire column of purchased
        items gets parsed. This is done for performance reasons in
        order to reduce the number of API requests because it takes
        one API call to get the style of each cell.

        :return dict: a map
            {
                "B8": ('Bread', CellType.GROCERY),
                "B10": ('SUSHI ROLL', CellType.TAKEOUTS),
                "B14": ('DEBIT', CellType.REGULAR),
                ...
            }

        :return:
        """
        result = {}

        _, col = a1_to_rowcol(f"{self.NAME_COLUMN}1")
        name_cells = [
            Cell(row=row, col=col, value=line[col - 1])
            for row, line in enumerate(self.content, 1)
            if line[col - 1] and row > 1
        ]

        for cell in name_cells:
            label = rowcol_to_a1(cell.row, cell.col)
            cell_type = self.get_cell_type(label=label)

            result[label] = (cell.value, cell_type)

        return result

    @cached_property
    def _prices(self):
        """
        Get all prices and recognize their type.

        This method practices lazy evaluation too for the same reasons.

        :return dict: a map
            {
                "D13": (Decimal(1.23), CellType.TOTAL),
                "D15": (Decimal(1.23), CellType.TAX),
                ...
                "D10": (Decimal(3.45), CellType.REGULAR),
                "D12": (Decimal(4.56), CellType.REGULAR),
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
            amount = price_to_decimal(cell.value, worksheet_title=self.worksheet.title, label=label)

            is_summary_collected = all(
                price_type in result for price_type in self.SUMMARY_TYPES
            )

            if is_summary_collected:
                result[label] = (amount, CellType.REGULAR)
                # if all summary prices are identified already, then we don't need
                # to check the color of other prices because the rest of them are
                # regular prices. That's why we move on to the next cell right away.
                continue

            cell_type = self.get_cell_type(label=label)
            result[label] = (amount, cell_type)

        return result

    @cached_property
    def price_stats(self):
        """
        Return a sum of all prices of each type.

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
            if cell_type in result:
                result[cell_type] += price
            else:
                result[cell_type] = price
        return result

    @cached_property
    def regular_prices(self):
        """
        Get a dict of all regular prices.

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
            if cell_type == CellType.REGULAR
        }

    @property
    def actually_paid(self):
        return self.price_stats.get(CellType.ACTUALLY_PAID)

    @property
    def total(self):
        try:
            return self.price_stats[CellType.TOTAL]
        except KeyError:
            raise ValueError(f"There is no TOTAL price in {self.worksheet.title}")

    @property
    def subtotal(self):
        return self.price_stats.get(CellType.SUBTOTAL)

    @property
    def tax(self):
        return self.price_stats.get(CellType.TAX)

    def prices_are_valid(self, raise_exception=True):
        """Return True if all prices adds up correctly to subtotal and total numbers."""
        calculated_sum = self.price_stats.get(CellType.REGULAR, 0)
        tax = self.tax or 0
        match_total = self.total == (self.subtotal or calculated_sum) + tax
        if raise_exception and not match_total:
            raise ValueError(
                f"Subtotal {calculated_sum} + tax {tax} is not equal to total amount {self.total} "
                f"in {self.worksheet.title}"
            )

        if self.subtotal:
            match_subtotal = calculated_sum == self.subtotal
            if raise_exception and not match_subtotal:
                raise ValueError(
                    f"Sum of prices {calculated_sum} is not equal to subtotal amount {self.subtotal} "
                    f"in {self.worksheet.title}"
                )
            result = match_subtotal and match_total
        else:
            result = match_total

        return result
