__version__ = "0.1.0"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

import widgets


class Contacts(ScreenManager):
    pass

class ContactsApp(App):
    def build(self):
        Window.bind(on_keyboard=self.hook_keyboard)

        return Contacts()

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def hook_keyboard(self, window, key, *largs):
        if key == 27: # Android back button
            self.root.transition.direction = 'right'
            if self.root.current != "EventsList":
                self.root.current = "EventsList"
            return True
        
if __name__ == '__main__':
    ContactsApp().run()

