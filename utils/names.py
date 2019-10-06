import re
from string import ascii_letters

from dateutil import parser

DATE_PATTERN = re.compile(r"[\d\/.\-\\]+")


def get_normalized_title(tab_title, filename, names_registry=None):
    """
    Extract the day number from the title.

    Make sure the tab title corresponds to the file name:
    the tab in a file "2018-08" must contain the date of August 2018.

    :param str tab_title:
    :param str filename:
    :param set names_registry: if provided, this function will make sure
        the name is unique across the provided registry.
    :rtype: str
        Copy of 2018/08/01 PM ==> 01
        Copy of 18/08/07 1 ==> 07
    """
    try:
        match_date = re.search(DATE_PATTERN, tab_title)[0]
    except (TypeError, IndexError):
        raise ValueError(f"Date not found in title {tab_title}")

    try:
        is_normalized = 1 <= int(match_date) <= 31
    except ValueError:
        is_normalized = False

    if is_normalized:
        raise ValueError(f"The tab '{tab_title}' is normalized already.")

    tab_date = parser.parse(match_date, yearfirst=True)
    file_date = parser.parse(filename, yearfirst=True)

    if file_date.year != tab_date.year or file_date.month != tab_date.month:
        raise ValueError(
            f"The date in the tab '{tab_title}' does not correspond to the file name '{filename}'."
        )

    normalized_title = "{:02d}".format(tab_date.day)
    if names_registry:
        unique_title = normalized_title
        i = 0
        while unique_title in names_registry:
            unique_title = normalized_title + ascii_letters[i]
            i += 1
        normalized_title = unique_title

    return normalized_title
