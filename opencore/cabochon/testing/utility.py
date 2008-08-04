from opencore.cabochon.interfaces import ICabochonClient
from zope.component import queryUtility
from zope.component import provideUtility
from zope.interface import implements

test_log = []

def pop_test_log():
    if test_log:
        return test_log.pop()

def setup_cabochon_mock(portal):
    if queryUtility(ICabochonClient):
        provideUtility(StubCabochonClient(), ICabochonClient)

# why not use minimock?
class StubCabochonClient(object):
    """stub class used to monkey patch cabochon for unit tests"""
    implements(ICabochonClient)

    def _stub(self, *args):
        test_log.append('opencore.testing.utility.StubCabochonClient: args: %s' % (args,))

    notify_project_created = _stub
    notify_project_deleted = _stub
    notify_wikipage_created = _stub
    notify_wikipage_updated = _stub
    notify_wikipage_deleted = _stub
