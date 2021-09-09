from kivy.properties import DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screen import MDScreen


class MainButton(MDRaisedButton):
    pass


class MainCard(MDCard):
    data = DictProperty()

    def __init__(self, data: dict):

        # Shorten the data
        for thing in ("details", "state"):
            if len(data[thing]) > 32:
                data[thing] = data[thing][:31] + "…"

        self.data = data
        super().__init__()


class Form(BoxLayout):
    def change_text(self, id):
        for child in self.parent.children:
            if isinstance(child, MainCard):
                child.ids[id].text = self.ids[id].text
                break


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        screen = FloatLayout()
        screen.add_widget(Form())
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
