"""Offline contract tests; run with python -m unittest discover -s tests."""
import unittest
from pathlib import Path

import hw1


class StubChain:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def invoke(self, inputs):
        self.calls += 1
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return value


def receipt(paid="102.30", subtotal="102.31", rounding="-0.01",
            discounts=None, items=None):
    return {
        "final_payment": paid, "subtotal": subtotal, "rounding": rounding,
        "discounts": discounts if discounts is not None else [
            {"label": "5% OFF", "amount": "-5.39"}],
        "items": items if items is not None else [
            {"label": "item A", "amount": "10.00"},
            {"label": "item B", "amount": "36.90"},
            {"label": "item C", "amount": "60.80"}],
    }


class AnswerTests(unittest.TestCase):
    image = Path(__file__).resolve().parents[1] / "public_test/receipt5.jpg"

    def test_discount_is_added_back_but_rounding_is_not(self):
        answer = hw1.answer_queries(StubChain([receipt()]), [self.image])
        self.assertEqual(answer, {hw1.QUERY_1: "HK$102.30", hw1.QUERY_2: "HK$107.70"})

    def test_all_receipts_and_all_discount_types_are_included(self):
        second = receipt("8.00", "8.00", "0.00", [
            {"label": "coupon", "amount": "1.50"},
            {"label": "member discount", "amount": "-0.50"}],
            [{"label": "item", "amount": "10.00"}])
        answer = hw1.answer_queries(StubChain([receipt(), second]), [self.image] * 2)
        self.assertEqual(answer, {hw1.QUERY_1: "HK$110.30", hw1.QUERY_2: "HK$117.70"})
        for value in answer.values():
            self.assertIsNotNone(hw1.parse_single_amount(value))

    def test_inconsistent_extraction_is_retried(self):
        chain = StubChain([receipt(paid="999.00"), receipt()])
        self.assertEqual(hw1.answer_queries(chain, [self.image])[hw1.QUERY_1], "HK$102.30")
        self.assertEqual(chain.calls, 2)

    def test_missing_discount_detected_by_item_sum(self):
        chain = StubChain([receipt(discounts=[]), receipt()])
        self.assertEqual(hw1.answer_queries(chain, [self.image])[hw1.QUERY_2], "HK$107.70")
        self.assertEqual(chain.calls, 2)

    def test_invalid_amount_never_silently_becomes_zero(self):
        chain = StubChain([receipt(paid="NaN")] * 3)
        answer = hw1.answer_queries(chain, [self.image])
        self.assertEqual(set(answer), set(hw1.QUERIES))
        self.assertTrue(all(hw1.parse_single_amount(v) is None for v in answer.values()))
        self.assertLessEqual(chain.calls, 3)

    def test_api_failure_returns_explicit_failure_for_csv(self):
        chain = StubChain([RuntimeError("API unavailable")] * 3)
        answer = hw1.answer_queries(chain, [self.image])
        self.assertTrue(all("ERROR" in v for v in answer.values()))

    def test_no_discount_and_positive_rounding(self):
        chain = StubChain([receipt("10.10", "10.08", "+0.02", [], [
            {"label": "item", "amount": "10.08"}])])
        answer = hw1.answer_queries(chain, [self.image])
        self.assertEqual(answer, {hw1.QUERY_1: "HK$10.10", hw1.QUERY_2: "HK$10.08"})


if __name__ == "__main__":
    unittest.main()
