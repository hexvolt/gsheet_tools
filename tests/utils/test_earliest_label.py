from unittest import TestCase

from utils.cells import get_earliest_label


class GetEarliestLabelTestCase(TestCase):

    def test_different_rows_cols(self):
        result = get_earliest_label("B2", "A2", "C3")
        self.assertEqual(result, "A2")

    def test_upper_right_earlier_than_left_bottom(self):
        result = get_earliest_label("B4", "D2")
        self.assertEqual(result, "D2")

    def test_different_rows_same_cols(self):
        result = get_earliest_label("A1", "B1")
        self.assertEqual(result, "A1")

    def test_same_rows_different_cols(self):
        result = get_earliest_label("A4", "D4", "E4")
        self.assertEqual(result, "A4")

    def test_same_labels(self):
        result = get_earliest_label("B2", "B2")
        self.assertEqual(result, "B2")

    def test_one_label(self):
        result = get_earliest_label("A1")
        self.assertEqual(result, "A1")

    def test_empty_label(self):
        result = get_earliest_label("A1", "")
        self.assertEqual(result, "A1")
