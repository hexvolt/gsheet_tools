from decimal import Decimal, InvalidOperation

from gspread.utils import a1_to_rowcol


def a1_to_coords(label):
    """
    Convert A1 label notion to coordinates in array.

    :return tuple:  A1 ==> [0, 0]
    """
    row, col = a1_to_rowcol(label)
    row -= 1
    col -= 1
    assert row >= 0 and col >= 0, f"{label} results in wrong index [{row}, {col}]"
    return row, col


def price_to_decimal(value, worksheet_title=None, label=None):
    try:
        return Decimal(value)
    except (TypeError, InvalidOperation):
        if worksheet_title:
            msg = f"Error converting '{value}' to number in worksheet '{worksheet_title}', cell {label}"
        else:
            msg = f"Error converting '{value}' to number"
        raise ValueError(msg)
