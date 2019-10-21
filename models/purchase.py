from decimal import Decimal

from attr import dataclass

from utils.constants import CellType


@dataclass
class Purchase:
    """
    Represents one purchased item.
    """
    good_name: str
    good_type: CellType
    good_label: str
    price: Decimal
    price_label: str
