from kivy import platform
from kivy.network.urlrequest import UrlRequest

from jnius import autoclass

import models

import json


# Getting the _unique_id, it's take a lot of ressources, so it is done once
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

        print data
        UrlRequest(url=url, req_body=json.dumps(data))


        for participate in event.contacts:
            # We must add the tablet id and the date to the json
            data = models.to_dict(participate.contact)
            data['date'] = participate.date
            data['tablet'] = get_unique_id()

            url = _HOSTNAME + _INDEX + 'contact/' #FIXME event.id
            body = {key: models.make_serializable(val)
                for key, val in data.iteritems()}

            print body
            UrlRequest(url=url, req_body=json.dumps(body))


