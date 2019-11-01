from decimal import Decimal, InvalidOperation

from gspread.utils import a1_to_rowcol, rowcol_to_a1


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
    if "," in value and "." in value:
        value = value.replace(",", "")
    try:
        return Decimal(value)
    except (TypeError, InvalidOperation):
        if worksheet_title:
            msg = f"Error converting '{value}' to number in worksheet '{worksheet_title}', cell {label}"
        else:
            msg = f"Error converting '{value}' to number"
        raise ValueError(msg)


def get_earliest_label(*labels):
    """Return the earliest among labels in left-to-right top-to-bottom order."""
    labels = [label for label in labels if label]
    if not labels:
        raise ValueError("At least one non-empty label must be provided.")

    if len(labels) == 1:
        return labels[0]

    coords = [a1_to_rowcol(label) for label in labels]
    min_row = min(row for row, _ in coords)
    earliest_row = [(row, col) for row, col in coords if row == min_row]

    min_col = min(col for _, col in earliest_row)
    earliest = [(row, col) for row, col in earliest_row if col == min_col][0]
    earliest_label = rowcol_to_a1(*earliest)
    return earliest_label
