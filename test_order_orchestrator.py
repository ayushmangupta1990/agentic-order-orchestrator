import unittest

from order_orchestrator import OrderState, OrderSupervisor, Stage


class OrderSupervisorTests(unittest.TestCase):
    def test_happy_path_and_idempotency(self):
        supervisor = OrderSupervisor({"SKU-101": 5})
        first = supervisor.run(OrderState("1", "SKU-101", 2, "400001"))
        second = supervisor.run(OrderState("1", "SKU-101", 2, "400001"))
        self.assertEqual(first.stage, Stage.COMPLETED)
        self.assertIs(first, second)
        self.assertEqual(supervisor.stock["SKU-101"], 3)

    def test_insufficient_stock_is_rejected(self):
        result = OrderSupervisor({"SKU-101": 1}).run(
            OrderState("2", "SKU-101", 2, "400001")
        )
        self.assertEqual(result.stage, Stage.REJECTED)
        self.assertIsNone(result.dispatch_id)


if __name__ == "__main__":
    unittest.main()
