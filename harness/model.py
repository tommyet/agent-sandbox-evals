from typing import Dict, List


class FakeModel:
    """
    A fake model used to test the agent loop.

    It ignores the messages and returns a fixed sequence of responses.
    This lets us test the harness before connecting a real LLM.
    """

    def __init__(self):
        self.responses = [
            "ACTION:\npwd && ls -la",
            "ACTION:\npytest",
            "ACTION:\nsed -i 's/return price + tax_rate/return price * (1 + tax_rate)/' app.py",
            "ACTION:\npytest",
            "FINAL:\nThe bug is fixed and pytest passes.",
        ]
        self.index = 0

    def complete(self, messages: List[Dict[str, str]]) -> str:
        if self.index >= len(self.responses):
            return "FINAL:\nNo more actions."

        response = self.responses[self.index]
        self.index += 1
        return response