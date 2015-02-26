__version__ = "0.2.0"

from kivy.app import App
from kivy.core.window import Window
from kivy.config import Config

import widgets

class ContactsApp(App):
    def build(self):
        Window.bind(on_keyboard=self.hook_keyboard)

        return widgets.Contacts()

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def hook_keyboard(self, window, key, *largs):
        if key == 27:  # Android back button
            self.root.transition.direction = 'right'
            if self.root.current != "EventsList":
                self.root.current = "EventsList"
            return True
        
if __name__ == '__main__':
    ContactsApp().run()
