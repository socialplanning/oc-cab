from zope.app.component.hooks import setSite
from opencore.testing import utils
from opencore.testing.setup import simple_setup

def base_tt_setup(tc):
    tc.new_request = utils.new_request()
    import opencore.tasktracker
    from zope.app.annotation.interfaces import IAttributeAnnotatable
    from zope.testing.loggingsupport import InstalledHandler
    tc.log = InstalledHandler(opencore.tasktracker.LOG)
    setSite(tc.app.plone)

def extended_tt_setup(tc):
    base_tt_setup(tc)
    simple_setup(tc)

