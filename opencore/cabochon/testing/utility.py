from opencore.cabochon.interfaces import ICabochonClient
from opencore.testing.minimock import Mock
from opencore.testing.utility import mock_utility
from zope.component import provideUtility
from zope.interface import implements

test_log = []

def pop_test_log():
    if test_log:
        return test_log.pop()


# why not use minimock?
class StubCabochonClient(Mock):
    """stub class used to monkey patch cabochon for unit tests"""
    implements(ICabochonClient)

    def _stub(self, *args, **kwargs):
        argstr = str(args)
        kwargstr = str(kwargs)
        test_log.append('opencore.testing.utility.StubCabochonClient: args: %s; kwargs: %s' % (argstr, kwargstr))

    send_feed_item = _stub
    notify_project_created = _stub
    notify_project_deleted = _stub
    notify_wikipage_created = _stub
    notify_wikipage_updated = _stub
    notify_wikipage_deleted = _stub


def setup_cabochon_mock():
    cabclient = mock_utility('opencore.cabochon.client.CabochonClient',
                             ICabochonClient, StubCabochonClient)
    provideUtility(cabclient, provides=ICabochonClient)
