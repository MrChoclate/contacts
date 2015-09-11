# -*- coding: utf-8 -*-

import datetime

from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.bubble  import Bubble
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.properties import ListProperty, NumericProperty
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder

import models
import sync
import savecsv


Builder.load_file("contact.kv")
Builder.load_file("events.kv")


class Contacts(ScreenManager):
    pass

class Contact(Widget):
    time = ObjectProperty()
    contact = ObjectProperty()

    def __init__(self, **kwargs):
        super(Contact, self).__init__(**kwargs)
        self.contact = kwargs['contact']
        self.time = kwargs['time']

    def edit_contact(self):
        root = self.parent.parent.parent.parent
        form_name = "ContactForm #" + str(root.event.id)
        form = root.manager.get_screen(form_name)
        form.contact = self.contact
        form.update_field_from_contact()
        root.manager.transition.direction = "right"
        root.manager.current = form_name

class ContactsList(Screen):
    list_layout = ObjectProperty()
    event = ObjectProperty()

    def __init__(self, **kwargs):
        super(ContactsList, self).__init__(**kwargs)
        self.event = kwargs['event']
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))

    def load_contacts(self):
        self.list_layout.clear_widgets()
        for participate in self.event.contacts:
            time = participate.date.strftime("à %Hh%M")
            contact = Contact(time=time, contact=participate.contact)
            self.list_layout.add_widget(contact)

class Event(Widget):
    """This a row when you select an event"""

    event = ObjectProperty()
    name = ObjectProperty()
    date = ObjectProperty()

    def __init__(self, **kwargs):
        super(Event, self).__init__(**kwargs)
        self.event = kwargs['event']
        self.update_name()

    def add_contact(self):
        manager = self.get_EventsList().manager
        screen_name = "ContactForm #" + str(self.event.id)
        if not manager.has_screen(screen_name):
            manager.add_widget(ContactForm(event=self.event, name=screen_name))

        manager.transition.direction = 'left'
        manager.current = screen_name

    def update_name(self):
        self.name.text = self.event.name + u' - ' + self.event.location
        self.date.text = self.event.begin.strftime("%d/%m")
        self.date.text += u' au ' + self.event.end.strftime("%d/%m")

    def edit_event(self):
        EventHandler(event=self.event, widget=self).open()

    def delete_event(self):
        DelEventPopUp(event=self.event, widget_to_delete=self).open()

    def get_EventsList(self):
        """Get the EventsList associated to self.
        This is done to avoid typing self.parent.parent.parent, and allows
        changing the view without breaking the code."""

        widget = self
        while(type(widget) != EventsList):
            widget = widget.parent
        return widget

class EventsList(Screen):
    list_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super(EventsList, self).__init__(**kwargs)

        # We must wait the .kv file is loaded to access self.list_layout
        Clock.schedule_once(lambda dt: self.load_events(), -1)

    def load_events(self):
        events = models.Session.query(models.Event).all()
        for event in events:
            self.list_layout.add_widget(Event(event=event))

    def add_event(self):
        event = models.Event(name="", location="",
            begin=datetime.date.today(), end=datetime.date.today())
        EventHandler(event=event, widget=self).open()

    def sync(self):
        sync.synchronize()

    def save_csv(self):
        self.add_widget(ErrorBubble(message="csv sauvegardé", duration=3))
        savecsv.save_csv()

class TextForm(TextInput):

    def __init__(self, **kwargs):
        super(TextForm, self).__init__(**kwargs)

        self.bind(focus=self.span_keyboard_on_focus)
        self.bind(on_text_validate=self.next_on_validate)

    @staticmethod
    def next_on_validate(instance):
        """Change the focus when Enter is pressed.
        """
        next  = instance._get_focus_next('focus_next')
        if next:
            instance.focus = False
            next.focus = True

    @staticmethod
    def span_keyboard_on_focus(instance, value):
        """Span the keyboard when the instance is focus or unfocus (value is bool)
        """
        to_move = Window.children[0]

        if value:  # User focus
            def move(window, height):
                if instance.y <= height:
                    offset = 0 if type(to_move) == Contacts else to_move.y
                    y = height - instance.y + offset + 10

                    # Avoid reset when we change focus
                    Animation.cancel_all(to_move, 'y')
                    Animation(y=y, t='linear', d=0.5).start(to_move)

            instance._keyboard_move = move
            Window.bind(keyboard_height=move)
            move(Window, Window.keyboard_height)

        else:
            Window.unbind(keyboard_height=instance._keyboard_move)
            reset = 0 if type(to_move) == Contacts else \
                    (Window.height - to_move.height) / 2
            Animation(y=reset, t='in_out_cubic').start(to_move)

class ContactForm(Screen):
    """This is where you register your contact."""

    gender = ObjectProperty()
    last_name = ObjectProperty()
    first_name = ObjectProperty()
    mail = ObjectProperty()
    mail2 = ObjectProperty()
    phone = ObjectProperty()
    street= ObjectProperty()
    town = ObjectProperty()
    postal_code = ObjectProperty()
    country = ObjectProperty()
    degree = ObjectProperty()
    studies = ObjectProperty()
    master = ObjectProperty()
    eisti = ObjectProperty()
    comment = ObjectProperty()
    save_btn = ObjectProperty()
    title = ObjectProperty()
    date = ObjectProperty()
    acc_number = NumericProperty(0)

    def __init__(self, **kwargs):
        super(ContactForm, self).__init__(**kwargs)
        self.event = kwargs['event']

        # Get the accompanists number or create it
        self.get_or_create_acc()

        # Lock the button if the dates are incorect
        if not (self.event.begin <= datetime.date.today() <= self.event.end):
            self.save_btn.disabled = True

        self.contact = models.Contact()

    def update_title(self):
        self.title.text = self.event.name
        self.date.text = self.event.begin.strftime("%d/%m") + ' au '
        self.date.text += self.event.end.strftime("%d/%m")

    def increase_acc(self):
        self.acc_number += 1
        self.accompanists.number += 1
        models.Session.add(self.accompanists)
        models.Session.commit()

    def get_or_create_acc(self):
        acc = models.Session.query(models.Accompanists).\
            filter_by(event_id=self.event.id, date=datetime.date.today()).all()
        if acc:
            self.accompanists = acc[0]
            self.acc_number = self.accompanists.number
        else:
            self.accompanists = models.Accompanists(event_id=self.event.id,
                                                    date=datetime.date.today())
            models.Session.add(self.accompanists)
            models.Session.commit()

    def reset(self):
        self.contact = models.Contact()
        self.update_field_from_contact()

    def is_proper(self):
        """Check if the contact can be saved, some field must not be null."""
        if not self.last_name.text:
            self.add_widget(ErrorBubble(message="Merci de rentrer votre nom"))
            return False

        if not self.first_name.text:
            self.add_widget(ErrorBubble(
                                message="Merci de rentrer votre prénom"))
            return False

        if not self.mail.text:
            self.add_widget(ErrorBubble(message="Merci de rentrer votre mail"))
            return False

        if self.studies.text == '-':
            self.add_widget(ErrorBubble(message="Merci de remplir vos études"))
            return False

        return True

    def update_field_from_contact(self):
        columns = self.contact.__table__.columns
        attrs = [c.name for c in columns if c.name != 'id']
        for attr in attrs:
            val = unicode(getattr(self.contact, attr)).encode('utf8')
            getattr(self, attr).text = val

    def update_contact_from_field(self):
        columns = self.contact.__table__.columns
        attrs = [c.name for c in columns
            if c.name not in ['id', 'postal_code', 'master']]

        for attr in attrs:
            setattr(self.contact, attr, getattr(self, attr).text.decode('utf-8'))
        for attr in ['postal_code', 'master']:
            val = int(getattr(self, attr).text.decode('utf-8') or 0)
            setattr(self.contact, attr, val)

    def save(self):
        if not self.is_proper():
            return

        self.update_contact_from_field()
        models.Session.add(self.contact)
        models.Session.flush()

        number = models.Session.query(models.Participate).\
            filter(models.Participate.event_id==self.event.id and \
                   models.Participate.contact_id==self.contact.id).count()

        if number == 0:  # This is an add, not an update
            participate = models.Participate(event_id=self.event.id,
                                         contact_id=self.contact.id,
                                         date=datetime.datetime.now())
            models.Session.add(participate)
        models.Session.commit()

        self.reset()

    def see_contacts(self):
        manager = self.manager
        screen_name = "ContactsList #" + str(self.event.id)
        if not manager.has_screen(screen_name):
            manager.add_widget(ContactsList(event=self.event, name=screen_name))

        manager.transition.direction = 'left'
        manager.current = screen_name

class DelEventPopUp(Popup):
    """A yes-no popup to confirm the deletion of an event"""

    def __init__(self, **kwargs):
        super(DelEventPopUp, self).__init__(**kwargs)
        self.event = kwargs['event']
        self.widget_to_delete = kwargs['widget_to_delete']

    def delete_event(self):
        models.Session.delete(self.event)
        models.Session.commit()
        self.widget_to_delete.parent.remove_widget(self.widget_to_delete)
        self.dismiss()

class EventHandler(Popup):
    """A quick form to edit and add an event"""

    name = ObjectProperty()
    location = ObjectProperty()
    begin = ObjectProperty()
    end = ObjectProperty()

    def __init__(self, **kwargs):
        super(EventHandler, self).__init__(**kwargs)

        self.event = kwargs['event']
        self.widget = kwargs['widget']

        Clock.schedule_once(lambda dt: self.load_event(), -1)

    def load_event(self):
        self.name.text = self.event.name
        self.location.text = self.event.location
        self.begin.text = self.event.begin.strftime("%d/%m/%y")
        self.end.text = self.event.end.strftime("%d/%m/%y")

    def save(self):
        if not self.name.text or not self.location.text:
            return

        self.event.name = self.name.text.decode('utf-8')
        self.event.location = self.location.text.decode('utf-8')
        try:
            self.event.begin = datetime.datetime.\
                            strptime(self.begin.text, "%d/%m/%y").date()
            self.event.end = datetime.datetime.\
                            strptime(self.end.text, "%d/%m/%y").date()
        except:
            self.dismiss()
            # TODO: Errors should never pass silently.
            return

        models.Session.add(self.event)
        models.Session.commit()

        # Edit case
        if self.widget and type(self.widget) == Event:
            self.widget.update_name()
        # Add case
        if self.widget and type(self.widget) == EventsList:
            self.widget.list_layout.add_widget(Event(event=self.event))

        self.dismiss()

class ErrorBubble(Bubble):
    message = ObjectProperty()

    def __init__(self, **kwargs):
        super(ErrorBubble, self).__init__(**kwargs)
        self.message.text = kwargs['message']
        self.width = 8 * len(self.message.text)
        self.height = 50
        time = kwargs['duration'] if 'duration' in kwargs else 10
        Clock.schedule_once(lambda dt: self.parent.remove_widget(self), time)

class OthersPopup(Popup):
    textinput = ObjectProperty()
    choices = ObjectProperty()
    values = ListProperty()

    def __init__(self, **kwargs):
        super(OthersPopup, self).__init__(**kwargs)
        self.spinner = kwargs['spinner']
        values = kwargs['values']

    def on_dismiss(self):
        if self.choices.text:
            self.spinner.text = self.choices.text
            self.choices.text = ""
        elif self.textinput.text:
            self.spinner.text = self.textinput.text
            self.textinput.text = ""
        else:
            self.spinner.text =  "-"

class SpinnerOthers(Spinner):
    other = StringProperty()
    other_values = ListProperty()

    def __init__(self, **kwargs):
        super(SpinnerOthers, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_popup(), -1)
        self.bind(text=self.on_text_other)

    def load_popup(self):
        """We need to wait the .kv loading, otherwise, other_values is empty.
        """
        self.popup = OthersPopup(spinner=self, values=self.other_values)

    @staticmethod
    def on_text_other(self, value):
        if value == self.other:
            self.popup.open()
