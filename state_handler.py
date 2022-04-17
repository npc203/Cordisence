from dataclasses import dataclass, field
import os
import json
from typing import List, Optional


@dataclass
class Template:
    client_id: int
    state: str
    details: str
    large_image: str
    large_text: str
    small_image: str
    small_text: str
    buttons: dict = field(default_factory=dict)

    @property
    def data(self):
        return {
            "state": self.state,
            "details": self.details,
            "large_image": self.large_image,
            "large_text": self.large_text,
            "small_image": self.small_image,
            "small_text": self.small_text,
            "buttons": self.buttons,
        }


class StateHandler:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data: List[Template] = list()
        self.load_state()
        self.curr_index = 0  # state index on the self.data list
        self.state: Optional[Template] = None  # Current state

    def set_state(self, index):
        self.curr_index = index
        self.state = self.data[index]

    def load_state(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                raw_data = json.load(f)
                for args in raw_data:
                    self.data.append(Template(**args))

    def save_state(self):
        raw_data = list()
        for template in self.data:
            raw_data.append(vars(template))
        with open(self.filepath, "w+") as f:
            json.dump(raw_data, f)
