# -*- coding: utf-8 -*-

import json
import datetime

from kivy import platform
from kivy.app import App
from kivy.network.urlrequest import UrlRequest

from jnius import autoclass

import models

# Getting the _unique_id, it's take a lot of ressources (~1-2 seconds on 
# Archos Neon 101), so it is done only once.
if platform ==  'android':
    _PythonActivity = autoclass('org.renpy.android.PythonActivity')
    _Secure = autoclass('android.provider.Settings$Secure')
    _unique_id = _Secure.getString(
        _PythonActivity.mActivity.getContentResolver(),
        _Secure.ANDROID_ID)
if platform == 'linux':
    _unique_id = 'linux-laptop'


_HOSTNAME = "http://192.168.0.111:9200/"
_INDEX = "contacts/"


def get_unique_id():
    return _unique_id

def synchronize():
    for event in models.Session.query(models.Event).all():
        # Send the event with the number of accompanists per day
        url = _HOSTNAME + _INDEX + 'event/'
        data = models.to_dict(event)

        accompanists = models.Session.query(models.Accompanists).\
                        filter(models.Accompanists.event_id == event.id).all()
        data['accompanists'] = {str(acc.date): acc.number 
                                for acc in accompanists}

        UrlRequest(url=url, req_body=json.dumps(data))


        for participate in event.contacts:
            # We must add the tablet id and the date to the json
            data = models.to_dict(participate.contact)
            data['date'] = participate.date
            data['tablet'] = get_unique_id()

            url = _HOSTNAME + _INDEX + 'contact/' #FIXME event.id
            body = {key: models.make_serializable(val)
                for key, val in data.iteritems()}

            UrlRequest(url=url, req_body=json.dumps(body))


def save_csv():
    for event in models.Session.query(models.Event).all():
        save_csv_event(event)

def save_csv_event(event):
    event_name = event.name.encode('utf-8')
    event_location = event.location.encode('utf-8')

    source = '/sdcard/exportcsv/' if platform == 'android' else ''
    filename = source + event_name + '-' + event_location + '-'
    filename += str(datetime.datetime.now()) + '.csv'

    with open(filename, 'w') as f:
        accompanists = models.Session.query(models.Accompanists).\
                        filter(models.Accompanists.event_id == event.id).all()
        header = ["Nom de l'évènement", "Lieu"]
        header += [str(a.date) for a in accompanists]
        f.write(';'.join(header) + '\n')
        header = [event_name, event_location]
        header += [str(a.number) for a in accompanists]
        f.write(';'.join(header) + '\n\n')

        header = ["Genre", "Nom", "Prénom",  "Adresse", "", "CP", "Ville", 
                  "Pays", "Mail", "Mail2", "Niveau d'étude", "Commentaire", 
                  "Téléphone", "Dernier diplôme", "Expérience mastère",
                  "Connaissance eisti", "Date"]
        order = ["gender", "last_name", "first_name", "street", "", 
                 "postal_code", "town", "country", "mail", "mail2",
                 "studies", "comment", "phone", "degree", "master",
                 "eisti"]
        f.write(';'.join(header) + '\n')

        for participate in event.contacts:
            contact = participate.contact
            data = [getattr(contact, attr) if attr else '' for attr in order]
            data.append(participate.date)
            data = [unicode(x).encode('utf-8') for x in data]
            f.write(';'.join(data) + '\n')

