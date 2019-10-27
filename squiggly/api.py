import json
import os


class MockClient:
    """
    Simulates what a tildes API might look like by returning predefined data.

    This is intended to be used for testing and preliminary development.
    """

    DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

    def __init__(self):
        with open(self.DATA_FILE) as fp:
            self._data = json.load(fp)

    def list_groups(self):
        return self._data["groups"] * 4
