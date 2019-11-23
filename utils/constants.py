from decimal import Decimal
from enum import Enum

import click

from models.base import Color

HST = Decimal(0.13)

RESULT_OK = click.style("OK. ", fg="green")
RESULT_WARNING = click.style("WARNING: {}", fg="yellow")
RESULT_SKIPPED = click.style("Skipped.", fg="yellow")
RESULT_ERROR = click.style("ERROR: {}", fg="red")


class CellType(Enum):
    """
    Describe the colors in the source Receipt spreadsheet that a certain
    categories were marked with.
    """

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
    RENT = Color(red=10, green=10, blue=10)
    HOUSEKEEPING = Color(red=0.91764706, green=0.81960785, blue=0.8627451)
    GAS_ELECTRIC = Color(red=2, green=2, blue=2)
    PHONES = Color(red=3, green=3, blue=3)
    TV_INTERNET = Color(red=4, green=4, blue=4)
    FURNITURE_APPLIANCES = Color(red=0.8352941, green=0.6509804, blue=0.7411765)

    # Style and personal care
    CLOTHING = Color(red=0.8117647, green=0.8862745, blue=0.9529412)
    GYM = Color(red=0.62352943, green=0.77254903, blue=0.9098039)
    HAIRCUTS = Color(red=7, green=7, blue=7)

    # Fun stuff
    ENTERTAINMENT = Color(red=0.7176471, green=0.91764706, blue=0.7019608)
    TRAVEL = Color(red=0.44705883, green=0.84705883, blue=0.4509804)
    BOOKS = Color(red=0.30588236, green=0.7019608, blue=0.3529412)
    GIFTS = Color(red=0.5529412, green=0.9372549, blue=0.85490197)
    HOBBIES = Color(red=0.49019608, green=0.83137256, blue=0.7607843)
    SUBSCRIPTIONS = Color(red=5, green=5, blue=5)
    OTHER_FUN = Color(red=0.41960785, green=0.7137255, blue=0.6509804)

    # Getting around
    GASOLINE = Color(red=0.7764706, green=0.6745098, blue=1)
    PARKING = Color(red=0.5568628, green=0.4862745, blue=0.7647059)
    FARES = Color(red=0.85882354, green=0.6431373, blue=0.9843137)
    CAR_RENT = Color(red=6, green=6, blue=6)

    # Health care
    DRUGS = Color(red=0.6431373, green=0.7607843, blue=0.95686275)
    DENTAL_VISION = Color(red=0.42745098, green=0.61960787, blue=0.92156863)

    # Other
    OTHER = Color(red=0.7176471, green=0.7176471, blue=0.7176471)
    CHARITY = Color(red=8, green=8, blue=8)


SUMMARY_TYPES = (
    CellType.TAX,
    CellType.SUBTOTAL,
    CellType.TOTAL,
    CellType.ACTUALLY_PAID,
)

GOODS_TYPES = (
    CellType.GROCERY,
    CellType.TAKEOUTS,
    CellType.HOUSEKEEPING,
    CellType.FURNITURE_APPLIANCES,
    CellType.CLOTHING,
    CellType.GYM,
    CellType.ENTERTAINMENT,
    CellType.TRAVEL,
    CellType.BOOKS,
    CellType.GIFTS,
    CellType.HOBBIES,
    CellType.OTHER_FUN,
    CellType.GASOLINE,
    CellType.PARKING,
    CellType.FARES,
    CellType.DRUGS,
    CellType.DENTAL_VISION,
    CellType.OTHER,
)
