# -*- coding: utf-8 -*-

import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty, ObjectProperty
from kivy.lang import Builder

import models
import sync

Builder.load_file("contact.kv")
Builder.load_file("events.kv")

KEYBOARD_HEIGHT = 292  # FIXME: Default value


class Contacts(ScreenManager):
    pass

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
	acc_img = ObjectProperty()
	save_btn = ObjectProperty()
	title = ObjectProperty()
	acc_number = NumericProperty(0)

	def __init__(self, **kwargs):
		super(ContactForm, self).__init__(**kwargs)
		self.event = kwargs['event']

		# Update the title
		self.title.text = self.event.name + ' - ' + self.title.text

		# Get the accompanists number or create it
		self.get_or_create_acc()		

	def increase_acc(self):
		self.acc_number  += 1
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
		self.last_name.text = self.first_name.text = self.mail.text = ""
		self.mail2.text = self.phone.text = self.street.text = "" 
		self.town.text = self.postal_code.text = self.degree.text = ""
		self.master.text = self.comment.text = ""
		self.studies.text = "-"
		self.gender.text = "Homme"
		self.country.text = "France"
		self.eisti.text = "Dans ce salon"

	def is_proper(self):
		"""Check if the contact can be saved, some field must not be null."""

		return bool(self.last_name.text and self.first_name.text and \
					self.mail.text and self.studies.text != u' - ')

	def save(self):
		if not self.is_proper():
			print "No !"
			return 

		contact = models.Contact(
				last_name=self.last_name.text.decode('utf-8'), 
				first_name=self.first_name.text.decode('utf-8'),
				gender=self.gender.text.decode('utf-8'),
				postal_code=int(self.postal_code.text.decode('utf-8') or 0),
				street=self.street.text.decode('utf-8'),
				town=self.town.text.decode('utf-8'),
				country=self.country.text.decode('utf-8'),
				mail=self.mail.text.decode('utf-8'),
				mail2=self.mail2.text.decode('utf-8'),
				phone=self.phone.text.decode('utf-8'),
				degree=self.degree.text.decode('utf-8'),
				studies=self.studies.text.decode('utf-8'),
				master=int(self.master.text.decode('utf-8') or 0),
				comment=self.comment.text.decode('utf-8'),
				eisti=self.eisti.text.decode('utf-8')
				)

		models.Session.add(contact)
		models.Session.flush()

		participate = models.Participate(event_id=self.event.id,
										 contact_id=contact.id)

		models.Session.add(participate)
		models.Session.commit()

		self.reset()

	def on_touch_down(self, touch):
		if self.acc_img.x <= touch.x <= self.acc_img.x + self.acc_img.width and \
		   self.acc_img.y <= touch.y <= self.acc_img.y + self.acc_img.height:
			self.increase_acc()

		# Propagate the event
		super(ContactForm, self).on_touch_down(touch)

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

	def __init__(self, **kwargs):
		super(EventHandler, self).__init__(**kwargs)

		self.event = kwargs['event']
		self.widget = kwargs['widget']

		Clock.schedule_once(lambda dt: self.load_event(), -1)

	def load_event(self):
		self.name.text = self.event.name
		self.location.text = self.event.location

	def save(self):
		self.event.name = self.name.text.decode('utf-8')
		self.event.location = self.location.text.decode('utf-8')

		models.Session.add(self.event)
		models.Session.commit()

		# Edit case
		if self.widget and type(self.widget) == Event:
			self.widget.name.text = self.event.name + u' - ' + self.event.location

		# Add case
		if self.widget and type(self.widget) == EventsList:
			self.widget.list_layout.add_widget(Event(event=self.event))

		self.dismiss()

class Event(Widget):
	"""This a row when you select an event"""

	event = ObjectProperty()
	name = ObjectProperty()
	
	def __init__(self, **kwargs):
		super(Event, self).__init__(**kwargs)
		self.event = kwargs['event']

	def add_contact(self):
		manager = self.get_EventsList().manager
		screen_name = "ContactForm #" + str(self.event.id)
		if not manager.has_screen(screen_name):
			manager.add_widget(ContactForm(event=self.event, name=screen_name))

		manager.transition.direction = 'left'
		manager.current = screen_name

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
		EventHandler(event=models.Event(name="", location=""), widget=self).open()

	def sync(self):
		sync.synchronize()

	def save_csv(self):
		sync.save_csv()