# -*- coding: utf-8 -*-

import json
import datetime

from kivy import platform
from kivy.app import App
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest

from jnius import autoclass

import models
import widgets

# Getting the _unique_id, it's take a lot of ressources (~1-2 seconds on
# Archos Neon 101), so it is done only once.
if platform == 'android':
    _PythonActivity = autoclass('org.renpy.android.PythonActivity')
    _Secure = autoclass('android.provider.Settings$Secure')
    _unique_id = _Secure.getString(
        _PythonActivity.mActivity.getContentResolver(),
        _Secure.ANDROID_ID)
if platform == 'linux':
    _unique_id = 'linux-laptop'


_HOSTNAME = "http://127.0.0.1:9200/"
_INDEX = "contacts/"


def get_unique_id():
    return _unique_id


def print_error(request, error):
    bubble = widgets.ErrorBubble(message="Une erreur est servenue", duration=1)
    Window.children[0].children[0].add_widget(bubble)


def print_sucess(request, error):
    bubble = widgets.ErrorBubble(message="Contact synchro", duration=1)
    Window.children[0].children[0].add_widget(bubble)


def search_event(event, return_=False):
    """Returns the result of a search request
    An  event is unique by its name, location and dates.
    """

    url = _HOSTNAME + _INDEX + 'event/_search'
    method = "GET"

    d = models.to_dict(event)
    del d['id']
    data = {"query":
            {"bool":
             {"must":
              [{"match_phrase": {k: v}} for k, v in d.iteritems()]
              }
             }
            }

    sucess = None if return_ else \
        lambda req, res: update_or_create_event(event, res)

    req = UrlRequest(url=url, req_body=json.dumps(data), method=method,
                     timeout=1, on_error=print_error, on_success=sucess)
    if return_:
        req.wait()  # We need the result before continuing
        return req.result


def update_or_create_event(event, result):
    """Update or create an event in elasticsearch using the response of
    search_event(event) request.
    """
    url = _HOSTNAME + _INDEX + 'event/'
    accompanists = models.Session.query(models.Accompanists).\
        filter(models.Accompanists.event_id == event.id).all()

    if result['hits']['total'] == 0:  # We need to create the event
        data = models.to_dict(event)
        data['accompanists'] = {str(acc.date): acc.number
                                for acc in accompanists}
        data['from'] = [get_unique_id()]
        del data['id']
        UrlRequest(url=url, req_body=json.dumps(data), on_error=print_error,
                   on_success=lambda req, res: send_contacts(event, result), timeout=1,
                   on_failure=print_error)

    else:
        res = result['hits']['hits'][0]['_source']
        if get_unique_id() in res['from']:
            send_contacts(event, result)
            return  # We already synchronize event, just send the contacts

        # We add our id and our accompanists
        res['from'].append(get_unique_id())
        for acc in accompanists:
            d = str(acc.date)
            if d not in res['accompanists']:
                res['accompanists'][d] = acc.number
            else:
                res['accompanists'][d] += acc.number

        url += result['hits']['hits'][0]['_id'] + '/_update'
        res = {"doc": res}
        UrlRequest(url=url, req_body=json.dumps(res), on_error=print_error,
                   on_success=lambda req, res: send_contacts(event, result), timeout=1,
                   on_failure=print_error)


def send_contacts(event, result):
    # Get the _id after a post request, we need to search again.
    res = search_event(event, return_=True)
    _id = res['hits']['hits'][0]['_id']

    for participate in event.contacts:
        contact, date = participate.contact, participate.date
        search_or_create_contact(contact, date, _id)


def search_or_create_contact(contact, date, _id):
    """We search a contact by its date, cause datetime is unique.
    If we did not find it, we send it to the server.
    """

    url = _HOSTNAME + _INDEX + 'contact/_search?parent=' + str(_id)
    method = 'GET'
    query = {'query':
             {"bool":
              {"must":
               [{"match_phrase": {'date': str(date)}},
                {"match_phrase": {'tablet': get_unique_id()}}
                ]
               }
              }
             }

    req = UrlRequest(url=url, req_body=json.dumps(query), method=method,
                     on_success=lambda req, res: create_or_none(res, contact, date, _id),
                     on_error=print_error, on_failure=print_error)


def create_or_none(result, contact, date, _id):
    if 'hits' not in result or 'total' not in result['hits'] or \
            result['hits']['total'] == 0:
        url = _HOSTNAME + _INDEX + 'contact/?parent=' + str(_id)
        data = models.to_dict(contact)
        data['date'] = str(date)
        data['tablet'] = get_unique_id()
        del data['id']

        UrlRequest(url=url, req_body=json.dumps(data), on_success=print_sucess,
                   on_error=print_error, on_failure=print_error)


def synchronize():
    for event in models.Session.query(models.Event).all():
        res = search_event(event)
