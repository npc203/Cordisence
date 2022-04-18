from dataclasses import dataclass, field
import os
import json
from typing import List, Optional


@dataclass
class Template:
    client_id: int
    state: Optional[str] = None
    details: Optional[str] = None
    large_image: Optional[str] = None
    large_text: Optional[str] = None
    small_image: Optional[str] = None
    small_text: Optional[str] = None
    buttons: list = field(default_factory=list)

    @property
    def data(self):
        final_dict = {}
        for key in (
            "state",
            "details",
            "large_image",
            "large_text",
            "small_image",
            "small_text",
            "buttons",
        ):
            if value := getattr(self, key):
                final_dict[key] = value
        return final_dict


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
