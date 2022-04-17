from kivy.properties import DictProperty
from kivymd.uix.gridlayout import GridLayout
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.floatlayout import FloatLayout

from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screen import MDScreen
from kivymd.toast import toast

from pypresence import Presence
from typing import Optional

from state_handler import StateHandler, Template


def shorten_data(text):
    if len(text) > 32:
        text = text[:31] + "…"
    return text


class MainButton(MDRaisedButton):
    pass


class MainCard(MDCard):
    data = DictProperty()

    def __init__(self, data: dict):

        # Shorten the data
        for thing in ("details", "state"):
            data[thing] = shorten_data(data[thing])

        self.data = data
        super().__init__()


class ConnectCard(MDCard):
    pass


class Form(GridLayout):
    def __init__(self):
        super().__init__(cols=2)
        self.app: MainApp = MDApp.get_running_app()
        self.build()

    def build(self):
        left_pane = BoxLayout()
        left_pane.id = "left_pane"
        left_pane.spacing = 20
        left_pane.orientation = "vertical"

        left_pane.add_widget(ConnectCard())

        for item in ("large_image", "small_image"):
            txtfield = MDTextField()
            txtfield.hint_text = item + " (name)"
            txtfield.id = item
            txtfield.mode = "rectangle"
            txtfield.bind(focus=self.update_state)
            left_pane.add_widget(txtfield)
        self.add_widget(left_pane)

        right_pane = BoxLayout()
        right_pane.id = "right_pane"
        right_pane.spacing = 20
        right_pane.orientation = "vertical"

        for item in ("details", "state", "large_text", "small_text"):
            txtfield = MDTextField()
            txtfield.hint_text = item
            txtfield.id = item
            txtfield.mode = "rectangle"
            txtfield.bind(text=lambda button, text: self.change_text(button.id, text))
            right_pane.add_widget(txtfield)

        self.add_widget(right_pane)

    def update_state(self, button, focus_bool):
        if not focus_bool:  # user is unfocusing after writing
            name = button.id
            value = button.text
            # print(name, value, button)
            self.app.display_state[name] = value

    def change_text(self, id_of_target, text):
        for child in self.parent.children:
            if isinstance(child, MainCard):
                if target := child.ids.get(id_of_target):  # TODO raise error
                    target.text = shorten_data(text)
                break


class ButtonBar(BoxLayout):
    def __init__(self):
        self.button_map = {
            "add button": self.add_button,
            "update": self.update,
            "clear": self.clear,
            "close": self.close,
        }
        super().__init__()
        self.app: MainApp = MDApp.get_running_app()
        self.build()

    def build(self):
        for button, callback in self.button_map.items():
            self.add_widget(MDRaisedButton(text=button.capitalize(), on_release=callback))

    def add_button(self):
        pass

    def update(self, button):
        template = Template(**self.app.display_state)
        # Check Valid state
        if template is None:
            toast("Invalid Credentials, fill in the form")
            return

        # RPC was already connected and running
        if self.app.RPC:
            self.app.RPC.update(**template.data)
        else:
            self.app.RPC = Presence(template.client_id)
            try:
                self.app.RPC.connect()
            except:
                toast("Could not connect to Discord")
            else:
                self.app.RPC.update(**template.data)

    def clear(self):
        pass

    def close(self):
        pass


class MainApp(MDApp):
    def __init__(self):
        self.RPC: Optional[Presence] = None
        self.data_state = StateHandler("data.json")
        self.display_state = dict()
        super().__init__()

    def connect(self):
        print("boom bap")

    def build(self):
        self.theme_cls.theme_style = "Dark"
        screen = FloatLayout()
        screen.add_widget(
            MDLabel(
                text="Cordisence",
                bold=True,
                font_style="H2",
                pos_hint={"center_y": 0.9},
                padding=(20, 10),
            )
        )
        screen.add_widget(Form())
        screen.add_widget(ButtonBar())
        screen.add_widget(
            MainCard(
                {
                    "name": "Name of your app",
                    "details": "",
                    "state": "",
                }
            )
        )
        return screen


MainApp().run()
