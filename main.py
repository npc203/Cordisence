from kivy.properties import DictProperty
from kivymd.uix.gridlayout import GridLayout
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.floatlayout import FloatLayout
from kivy.utils import get_color_from_hex

from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screen import MDScreen
from kivymd.toast import toast
from kivy.uix.popup import Popup

import traceback
import pypresence
from typing import Optional, List, Dict, Union, Any

from state_handler import StateHandler, Template
from kivy.graphics import Color, Line


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


class PopupContent(BoxLayout):
    pass


class ConnectCard(BoxLayout):
    def __init__(self):
        super().__init__()
        self.app: MainApp = MDApp.get_running_app()

    def tick(self):
        self.ids["status_icon"].icon = "checkbox-marked-circle"
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.5, 1, 0.5, 1)
            Line(
                width=1,
                rectangle=(self.x - 20, self.y - 20, self.width + 40, self.height + 40),
            )

    def untick(self):
        self.ids["status_icon"].icon = "checkbox-blank-circle"
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 0.5, 0.5, 1)
            Line(
                width=1,
                rectangle=(self.x - 20, self.y - 20, self.width + 40, self.height + 40),
            )

    def connect(self):
        print("Connecting...")
        text = self.ids["client_id"].text
        if text.isdigit():
            # Close already existing ones
            if self.app.RPC:
                self.app.RPC.close()  # TODO need error handling
            self.app.RPC = pypresence.Presence(text)
            try:
                self.app.RPC.connect()
                self.app.display_state["client_id"] = text
                self.tick()
            except:
                # traceback.print_exc()
                toast("Could not connect to Discord")
                self.app.RPC = None
        else:
            toast("Invalid Client ID")


class Form(BoxLayout):
    def __init__(self):
        super().__init__()
        self.app: MainApp = MDApp.get_running_app()
        self.build()

    def build(self):
        left_pane = BoxLayout()
        left_pane.id = "left_pane"
        left_pane.spacing = 20
        left_pane.orientation = "vertical"

        connect_card = ConnectCard()
        connect_card.id = "connect_card"

        left_pane.add_widget(connect_card)

        for item in ("large_image", "small_image"):
            txtfield = MDTextField()
            txtfield.hint_text = item + " (url)"
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
            txtfield.bind(focus=self.update_state)
            right_pane.add_widget(txtfield)

        self.add_widget(right_pane)

    def update_state(self, button, focus_bool):
        if not focus_bool:  # user is unfocusing after writing
            name = button.id
            value = button.text
            if name == "large_image":
                for child in self.parent.children:
                    if isinstance(child, MainCard):
                        child.ids["large_image"].source = value
                    break
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
            "update": self.update,
            "clear": self.clear,
            "Minimize to Tray": self.minimize_to_tray,
            "add button": self.add_button,
        }
        super().__init__()
        self.app: MainApp = MDApp.get_running_app()
        self.build()

    def build(self):
        for button, callback in self.button_map.items():
            self.add_widget(MDRaisedButton(text=button.capitalize(), on_release=callback))

    def add_button(self, button):
        content = PopupContent()
        popup = Popup(title="Add button", content=content, size_hint=(0.5, 0.5))
        # content.id = "btn_" + str(len(self.app.display_state["buttons"]))
        add_btn = content.ids["add_button"]

        def add(button):
            label = content.ids["label"].text
            url = content.ids["url"].text
            if len(self.app.display_state["buttons"]) >= 2:
                toast("You can only have 2 buttons")
                return
            self.app.display_state["buttons"].append({"label": label, "url": url})
            self.app.update_buttons()
            popup.dismiss()

        add_btn.bind(on_release=add)
        popup.open()

    def update(self, button):
        try:
            template = Template(**self.app.display_state)
        except Exception as e:
            toast("Fill in the following fields:" + str(e).split(":", 1)[1])
            return
        # Check Valid state
        if template is None:
            toast("Invalid Credentials, fill in the form")
            return

        # RPC was already connected and running
        if self.app.RPC:
            print(template.data)
            try:
                self.app.RPC.update(**template.data)
            except pypresence.exceptions.InvalidID:
                toast("Invalid Client ID")
                self.app.disconnect_rpc()
                return
            except pypresence.exceptions.ServerError as e:
                toast(str(e), duration=5)
                return
        else:
            toast("RPC not connected, setup your client ID and click connect", duration=5)

    def clear(self, btn):
        """Clears all the fields and the presence as well (connection is maintained)"""
        # TODO simplify
        for widget in self.app.root.children:
            if isinstance(widget, Form):
                for pane in widget.children:
                    for child in pane.children:
                        if isinstance(child, MDTextField):
                            child.text = ""
        if self.app.RPC:
            self.app.RPC.clear()

        toast("Cleared fields")

    def minimize_to_tray(self, btn):
        toast("WIP")


class MainApp(MDApp):
    def __init__(self):
        self.RPC: Optional[pypresence.Presence] = None
        self.data_state = StateHandler("cordisence_data.json")
        self.display_state: Dict[str, Any] = dict(buttons=[])
        super().__init__()

    def disconnect_rpc(self):
        self.RPC = None
        # TODO simplify
        for widget in self.root.children:
            if isinstance(widget, Form):
                for pane in widget.children:
                    if pane.id == "left_pane":
                        for child in pane.children:
                            if isinstance(child, ConnectCard):
                                child.untick()
                                child.ids["client_id"].text = ""
                                break
                        break
                break

    def delete_button(self, btn, content):
        self.display_state["buttons"].pop(content.id)
        content.popup.dismiss()
        self.update_buttons()

    def edit_button(self, btn, content):
        self.display_state["buttons"][content.id] = {
            "label": content.ids["label"].text,
            "url": content.ids["url"].text,
        }
        content.popup.dismiss()
        self.update_buttons()

    def update_buttons(self):
        """Updates the buttons on the display card"""
        for widget in self.root.children:
            if isinstance(widget, MainCard):
                # Remove the older buttons
                for btn_widget in widget.children:
                    if isinstance(btn_widget, MainButton):
                        widget.remove_widget(btn_widget)

                # Expand card size based on the button
                widget.size = ("260dp", f"{100+(40*len(self.display_state['buttons']))}dp")
                for ind, button in enumerate(self.display_state["buttons"]):
                    new_btn = MainButton(text=button["label"])
                    new_btn.id = ind

                    def display_edit_popup(click_btn):
                        form_data = self.display_state["buttons"][click_btn.id]
                        content = PopupContent()
                        content.id = click_btn.id
                        popup = Popup(
                            title="Edit button",
                            content=content,
                            size_hint=(0.5, 0.5),
                        )
                        content.popup = popup
                        content.ids["url"].text = form_data["url"]
                        content.ids["label"].text = form_data["label"]

                        content.ids["add_button"].text = "Edit"
                        content.ids["add_button"].bind(
                            on_release=lambda btn: self.edit_button(btn, content)
                        )

                        content.ids["bar"].add_widget(
                            MDRaisedButton(
                                text="Delete",
                                on_release=lambda btn: self.delete_button(btn, content),
                            )
                        )
                        content.popup = popup
                        popup.open()

                    new_btn.bind(on_release=display_edit_popup)
                    widget.add_widget(new_btn)

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

    def on_start(self):
        self.fps_monitor_start()

if __name__ == "__main__":
    MainApp().run()
