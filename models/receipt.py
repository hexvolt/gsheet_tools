from enum import Enum

from gspread_formatting import get_user_entered_format, CellFormat, Color, TextFormat


class CellType(Enum):
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


class ReceiptSheet:
    """
    Represents a worksheet with receipt.

    Encapsulates all data about receipt.
    """
    STORE_CELL = 'G2'
    TEXT_CELL = 'H2'
    JSON_CELL = 'I2'
    LINE_COLUMN = 'A'
    NAME_COLUMN = 'B'
    CODE_COLUMN = 'C'
    PRICE_COLUMN = 'D'

    def __init__(self, worksheet):
        self.worksheet = worksheet

    @property
    def store(self):
        return self.worksheet.acell(self.STORE_CELL).value

    @property
    def raw_text(self):
        return self.worksheet.acell(self.TEXT_CELL).value

    @property
    def raw_json(self):
        return self.worksheet.acell(self.JSON_CELL).value

    def get_cell_color(self, cell):
        native_format = get_user_entered_format(self, cell)
        return native_format.backgroundColor

    def get_cell_type(self, cell):
        cell_color = self.get_cell_color(cell)
        try:
            cell_type = CellType(cell_color)
        except ValueError:
            cell_type = None
        return cell_type
