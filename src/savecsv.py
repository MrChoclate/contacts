# -*- coding: utf-8 -*-

import datetime
import os

from kivy import platform

import models


def save_csv():
    for event in models.Session.query(models.Event).all():
        save_csv_event(event)


def save_csv_event(event):
    event_name = event.name.encode('utf-8')
    event_location = event.location.encode('utf-8')

    source = '/sdcard/exportcsv/' if platform == 'android' else ''
    filename = source + event_name + '-' + event_location + '-'
    filename += str(datetime.datetime.now()) + '.csv'

    if not os.path.exists(source):
        os.makedirs(source)

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
