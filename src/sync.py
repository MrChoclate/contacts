from kivy import platform
from jnius import autoclass

if platform ==  'android':
    _PythonActivity = autoclass('org.renpy.android.PythonActivity')
    _Secure = autoclass('android.provider.Settings$Secure')
    _android_id = _Secure.getString(_PythonActivity.mActivity.getContentResolver(),
                                  _Secure.ANDROID_ID)
if platform == 'linux':
    _android_id = 'linux'

_HOSTNAME = ""

def get_unique_id():
    return _android_id